import asyncio
import json
import logging
import random
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.models import (
    FailureSimulationRequest,
    HealthResponse,
    InfoResponse,
    LatencySimulationRequest,
    Product,
    ProductListResponse,
    SimulationStatusResponse,
    VersionResponse,
)

# -----------------------------------------------------------------------------
# Structured JSON Logging Setup
# -----------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


logger = logging.getLogger(settings.APP_NAME)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger.propagate = False

# -----------------------------------------------------------------------------
# Custom Prometheus Metrics
# -----------------------------------------------------------------------------
APP_VERSION_INFO = Gauge(
    "app_version_info",
    "Application version information",
    ["version", "commit_sha", "environment"],
)
APP_VERSION_INFO.labels(
    version=settings.APP_VERSION,
    commit_sha=settings.COMMIT_SHA,
    environment=settings.APP_ENV,
).set(1)

SIMULATION_STATE_GAUGE = Gauge(
    "release_demo_simulation_active",
    "Whether failure or latency simulation is currently active",
    ["simulation_type"],
)
SIMULATION_STATE_GAUGE.labels(simulation_type="failure").set(0)
SIMULATION_STATE_GAUGE.labels(simulation_type="latency").set(0)

# Low-cardinality custom error counters for Prometheus analysis
HTTP_ERRORS_TOTAL = Counter(
    "release_demo_http_errors_total",
    "Total HTTP 5xx errors recorded",
    ["endpoint", "status_code", "version"],
)

# -----------------------------------------------------------------------------
# In-Memory Simulation State
# -----------------------------------------------------------------------------
simulation_state = {
    "failure_enabled": False,
    "error_rate_percent": 100,
    "target_status_code": 500,
    "latency_enabled": False,
    "latency_ms": 500,
}


# -----------------------------------------------------------------------------
# Lifespan Context Manager (Graceful Startup & Shutdown)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting {settings.APP_NAME} version {settings.APP_VERSION} (env: {settings.APP_ENV}, sha: {settings.COMMIT_SHA})"
    )
    yield
    logger.info(f"Gracefully shutting down {settings.APP_NAME}")


app = FastAPI(
    title="Release Demo API",
    description="Application designed for Zero-Downtime Blue-Green and Canary Deployment verification",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Instrument Prometheus metrics (/metrics endpoint)
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/health", "/ready"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")


# -----------------------------------------------------------------------------
# Middleware: Latency Injection & Request Logging
# -----------------------------------------------------------------------------
@app.middleware("http")
async def simulation_and_logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Latency simulation check
    if simulation_state["latency_enabled"] and request.url.path.startswith("/api/products"):
        delay = simulation_state["latency_ms"] / 1000.0
        await asyncio.sleep(delay)

    response: Response = await call_next(request)

    duration = time.time() - start_time
    # Avoid noisy logs on health and metric probes
    if request.url.path not in ["/health", "/ready", "/metrics"]:
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration:.4f}s)"
        )

    # Track 5xx errors for Prometheus analysis
    if response.status_code >= 500:
        HTTP_ERRORS_TOTAL.labels(
            endpoint=request.url.path,
            status_code=str(response.status_code),
            version=settings.APP_VERSION,
        ).inc()

    return response


# -----------------------------------------------------------------------------
# Simulation Safeguard Helper
# -----------------------------------------------------------------------------
def verify_simulation_access(token: Optional[str] = Header(None, alias="X-Simulation-Token")):
    if not settings.SIMULATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Simulation controls are disabled in this environment. Set SIMULATION_ENABLED=true to enable.",
        )
    if token != settings.SIMULATION_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Simulation-Token header.",
        )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/", response_model=InfoResponse, tags=["General"])
async def root():
    return InfoResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        build_sha=settings.COMMIT_SHA,
        environment=settings.APP_ENV,
        status="operational",
    )


@app.get("/health", response_model=HealthResponse, tags=["Probes"])
async def liveness():
    """Lightweight Kubernetes liveness probe."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks={"process": "alive", "version": settings.APP_VERSION},
    )


@app.get("/ready", response_model=HealthResponse, tags=["Probes"])
async def readiness():
    """
    Kubernetes readiness probe.
    If failure simulation is active, deliberately fail readiness to simulate an unhealthy rollout.
    """
    if simulation_state["failure_enabled"] and simulation_state["target_status_code"] >= 500:
        logger.warning("Readiness probe failing due to active failure simulation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready (simulated failure active)",
        )

    return HealthResponse(
        status="ready",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks={"database": "connected", "dependencies": "ready"},
    )


@app.get("/api/version", response_model=VersionResponse, tags=["General"])
async def get_version():
    return VersionResponse(
        version=settings.APP_VERSION,
        build_sha=settings.COMMIT_SHA,
        release_type="canary" if "canary" in settings.APP_VERSION else "stable",
    )


@app.get("/api/products", response_model=ProductListResponse, tags=["Business Logic"])
async def get_products():
    """
    Returns product catalog data.
    Simulates failure if active according to configured error rate percentage.
    Demonstrates observable version difference:
    - v1.0.0 returns core products without tags/discounts.
    - v1.1.0 returns enhanced products with category tags and promotion discounts.
    """
    if simulation_state["failure_enabled"]:
        # Deterministic failure injection based on error_rate_percent
        roll = random.randint(1, 100)
        if roll <= simulation_state["error_rate_percent"]:
            logger.error(f"Simulating {simulation_state['target_status_code']} error on /api/products")
            raise HTTPException(
                status_code=simulation_state["target_status_code"],
                detail=f"Simulated failure trigger (error rate: {simulation_state['error_rate_percent']}%)",
            )

    is_v1_1 = settings.APP_VERSION.startswith("v1.1") or "v1.1" in settings.APP_VERSION

    if is_v1_1:
        # Observable feature addition in v1.1.0
        products = [
            Product(
                id=101,
                name="Kubernetes Cloud Cluster v2",
                category="Infrastructure",
                price=199.99,
                tags=["cloud", "managed", "high-availability"],
                discount_rate=0.15,
            ),
            Product(
                id=102,
                name="Argo Rollouts Enterprise Pack",
                category="CI/CD",
                price=89.50,
                tags=["progressive-delivery", "canary", "blue-green"],
                discount_rate=0.10,
            ),
            Product(
                id=103,
                name="Prometheus Production Telemetry Agent",
                category="Observability",
                price=49.00,
                tags=["monitoring", "metrics", "alerts"],
                discount_rate=0.05,
            ),
        ]
    else:
        # Baseline products for v1.0.0
        products = [
            Product(
                id=101,
                name="Kubernetes Cloud Cluster",
                category="Infrastructure",
                price=199.99,
            ),
            Product(
                id=102,
                name="Argo Rollouts Basic Pack",
                category="CI/CD",
                price=89.50,
            ),
            Product(
                id=103,
                name="Prometheus Telemetry Agent",
                category="Observability",
                price=49.00,
            ),
        ]

    return ProductListResponse(
        version=settings.APP_VERSION,
        total_count=len(products),
        products=products,
    )


# -----------------------------------------------------------------------------
# Simulation Endpoints (Controlled & Protected)
# -----------------------------------------------------------------------------
@app.get("/api/simulate/status", response_model=SimulationStatusResponse, tags=["Simulation Controls"])
async def get_simulation_status():
    return SimulationStatusResponse(
        simulation_feature_active=settings.SIMULATION_ENABLED,
        failure_enabled=simulation_state["failure_enabled"],
        error_rate_percent=simulation_state["error_rate_percent"],
        target_status_code=simulation_state["target_status_code"],
        latency_enabled=simulation_state["latency_enabled"],
        latency_ms=simulation_state["latency_ms"],
    )


@app.post("/api/simulate/failure", tags=["Simulation Controls"])
async def configure_failure_simulation(
    req: FailureSimulationRequest,
    x_token: Optional[str] = Header(None, alias="X-Simulation-Token"),
):
    verify_simulation_access(x_token)
    simulation_state["failure_enabled"] = req.enabled
    simulation_state["error_rate_percent"] = req.error_rate_percent
    simulation_state["target_status_code"] = req.target_status_code
    SIMULATION_STATE_GAUGE.labels(simulation_type="failure").set(1 if req.enabled else 0)

    logger.warning(
        f"Failure simulation updated: enabled={req.enabled}, error_rate={req.error_rate_percent}%, status={req.target_status_code}"
    )
    return {
        "status": "success",
        "message": f"Failure simulation set to {req.enabled}",
        "config": simulation_state,
    }


@app.post("/api/simulate/latency", tags=["Simulation Controls"])
async def configure_latency_simulation(
    req: LatencySimulationRequest,
    x_token: Optional[str] = Header(None, alias="X-Simulation-Token"),
):
    verify_simulation_access(x_token)
    simulation_state["latency_enabled"] = req.enabled
    simulation_state["latency_ms"] = req.latency_ms
    SIMULATION_STATE_GAUGE.labels(simulation_type="latency").set(1 if req.enabled else 0)

    logger.warning(
        f"Latency simulation updated: enabled={req.enabled}, latency={req.latency_ms}ms"
    )
    return {
        "status": "success",
        "message": f"Latency simulation set to {req.enabled}",
        "config": simulation_state,
    }


@app.post("/api/simulate/reset", tags=["Simulation Controls"])
async def reset_simulation(x_token: Optional[str] = Header(None, alias="X-Simulation-Token")):
    verify_simulation_access(x_token)
    simulation_state["failure_enabled"] = False
    simulation_state["error_rate_percent"] = 100
    simulation_state["target_status_code"] = 500
    simulation_state["latency_enabled"] = False
    simulation_state["latency_ms"] = 500
    SIMULATION_STATE_GAUGE.labels(simulation_type="failure").set(0)
    SIMULATION_STATE_GAUGE.labels(simulation_type="latency").set(0)

    logger.info("Simulation states reset to normal")
    return {"status": "success", "message": "Simulation states reset to operational normal"}

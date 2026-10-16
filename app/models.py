from typing import List, Optional
from pydantic import BaseModel, Field


class InfoResponse(BaseModel):
    app_name: str
    version: str
    build_sha: str
    environment: str
    status: str = "operational"


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    checks: dict


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    # Demonstrates observable feature difference between v1.0.0 and v1.1.0
    tags: Optional[List[str]] = Field(default_factory=list)
    discount_rate: Optional[float] = 0.0


class ProductListResponse(BaseModel):
    version: str
    total_count: int
    products: List[Product]


class VersionResponse(BaseModel):
    version: str
    build_sha: str
    release_type: str = "stable"


class FailureSimulationRequest(BaseModel):
    enabled: bool
    error_rate_percent: int = Field(default=100, ge=0, le=100)
    target_status_code: int = Field(default=500, ge=400, le=599)


class LatencySimulationRequest(BaseModel):
    enabled: bool
    latency_ms: int = Field(default=500, ge=0, le=10000)


class SimulationStatusResponse(BaseModel):
    simulation_feature_active: bool
    failure_enabled: bool
    error_rate_percent: int
    target_status_code: int
    latency_enabled: bool
    latency_ms: int

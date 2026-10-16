import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "release-demo-app"
    assert "version" in data
    assert "build_sha" in data
    assert data["status"] == "operational"


def test_health_liveness_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["process"] == "alive"


def test_ready_readiness_endpoint(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["dependencies"] == "ready"


def test_version_endpoint(client: TestClient):
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1.0.0"


def test_products_endpoint(client: TestClient):
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3
    assert len(data["products"]) == 3
    assert data["products"][0]["name"] == "Kubernetes Cloud Cluster"


def test_prometheus_metrics_endpoint(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "app_version_info" in response.text
    assert "http_requests_total" in response.text or "http_request_duration_seconds" in response.text

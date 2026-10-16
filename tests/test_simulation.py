import pytest
from fastapi.testclient import TestClient


def test_simulation_status(client: TestClient):
    response = client.get("/api/simulate/status")
    assert response.status_code == 200
    data = response.json()
    assert data["simulation_feature_active"] is True
    assert data["failure_enabled"] is False


def test_simulation_auth_protection(client: TestClient):
    # Missing token
    response = client.post(
        "/api/simulate/failure",
        json={"enabled": True, "error_rate_percent": 100, "target_status_code": 500},
    )
    assert response.status_code == 401

    # Invalid token
    response = client.post(
        "/api/simulate/failure",
        headers={"X-Simulation-Token": "wrong-token"},
        json={"enabled": True, "error_rate_percent": 100, "target_status_code": 500},
    )
    assert response.status_code == 401


def test_failure_injection_behavior(client: TestClient):
    # Enable failure simulation with valid token
    enable_resp = client.post(
        "/api/simulate/failure",
        headers={"X-Simulation-Token": "test-secret-token"},
        json={"enabled": True, "error_rate_percent": 100, "target_status_code": 500},
    )
    assert enable_resp.status_code == 200

    # /api/products should now fail with 500
    prod_resp = client.get("/api/products")
    assert prod_resp.status_code == 500

    # /ready probe should also fail with 503
    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 503

    # Reset simulation
    reset_resp = client.post(
        "/api/simulate/reset",
        headers={"X-Simulation-Token": "test-secret-token"},
    )
    assert reset_resp.status_code == 200

    # Verify recovery
    assert client.get("/api/products").status_code == 200
    assert client.get("/ready").status_code == 200


def test_latency_injection(client: TestClient):
    # Enable low artificial latency for testing
    resp = client.post(
        "/api/simulate/latency",
        headers={"X-Simulation-Token": "test-secret-token"},
        json={"enabled": True, "latency_ms": 100},
    )
    assert resp.status_code == 200

    # Verify endpoint still succeeds
    prod_resp = client.get("/api/products")
    assert prod_resp.status_code == 200

    # Reset
    client.post(
        "/api/simulate/reset",
        headers={"X-Simulation-Token": "test-secret-token"},
    )

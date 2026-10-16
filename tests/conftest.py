import os
import pytest
from fastapi.testclient import TestClient

# Configure test environment
os.environ["APP_ENV"] = "test"
os.environ["SIMULATION_ENABLED"] = "true"
os.environ["SIMULATION_AUTH_TOKEN"] = "test-secret-token"
os.environ["APP_VERSION"] = "v1.0.0"

from app.main import app, simulation_state


@pytest.fixture(autouse=True)
def reset_simulation_state():
    """Ensure simulation state is clean before and after each test."""
    simulation_state["failure_enabled"] = False
    simulation_state["error_rate_percent"] = 100
    simulation_state["target_status_code"] = 500
    simulation_state["latency_enabled"] = False
    simulation_state["latency_ms"] = 0
    yield
    simulation_state["failure_enabled"] = False
    simulation_state["error_rate_percent"] = 100
    simulation_state["target_status_code"] = 500
    simulation_state["latency_enabled"] = False
    simulation_state["latency_ms"] = 0


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

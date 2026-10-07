"""Unit tests for FastAPI backend server."""

import pytest
from fastapi.testclient import TestClient

from vcount.server import app

client = TestClient(app)


def test_system_info():
    response = client.get("/api/system")
    assert response.status_code == 200
    data = response.json()
    assert "device" in data
    assert "device_badge" in data
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


def test_status_nonexistent_job():
    response = client.get("/api/pipeline/status/nonexistent_123")
    assert response.status_code == 404


def test_results_nonexistent_job():
    response = client.get("/api/results/nonexistent_123")
    assert response.status_code == 404

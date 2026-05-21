"""Tests for the FastAPI server health and status endpoints."""

from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


def test_health_check():
    """GET /health should return 200 with status=='healthy' and required fields."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "documents_indexed" in data
    assert isinstance(data["documents_indexed"], int)
    assert "entities_count" in data
    assert "timestamp" in data


def test_status_endpoint():
    """GET /status should return 200 with status=='operational' and documents/entities keys."""
    response = client.get("/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "operational"
    assert "documents" in data
    assert "total" in data["documents"]
    assert "by_source" in data["documents"]
    assert "entities" in data


def test_cors_headers():
    """Requests from an allowed origin should carry CORS response headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

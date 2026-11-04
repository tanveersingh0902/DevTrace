"""
Tests for the FastAPI application health and root endpoints.

WHY TEST THESE?
These seem trivial, but they verify:
1. The FastAPI app starts without import errors
2. CORS middleware doesn't break the app
3. Configuration loads correctly
4. The response format matches what the frontend expects

HOW TO RUN:
    cd backend
    pytest tests/ -v
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """The health endpoint should return status 'healthy'."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "DevTrace"
    assert "version" in data


def test_root():
    """The root endpoint should return app information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["app"] == "DevTrace"
    assert data["docs"] == "/docs"


def test_docs_available():
    """The Swagger docs page should be accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


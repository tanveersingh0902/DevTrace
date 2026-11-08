from fastapi.testclient import TestClient

from app.api.deps import get_database
from app.main import create_app


def test_application_starts(client: TestClient) -> None:
    response = client.get("/api/v1")

    assert response.status_code == 200
    assert response.json() == {"name": "DevTrace API", "version": "v1"}
    assert response.headers["X-Request-ID"]


def test_health_confirms_process_liveness(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "health-check"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "health-check"


def test_ready_returns_ready_when_database_connection_succeeds(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_safe_error_when_database_connection_fails() -> None:
    class UnavailableDatabase:
        def check_connection(self) -> bool:
            return False

    app = create_app()
    app.dependency_overrides[get_database] = UnavailableDatabase
    with TestClient(app) as client:
        response = client.get("/ready")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "http_error"
    assert response.json()["detail"] == "Database is unavailable."

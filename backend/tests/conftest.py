import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_database
from app.main import create_app


class AvailableDatabase:
    def check_connection(self) -> bool:
        return True


class UnavailableDatabase:
    def check_connection(self) -> bool:
        return False


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_database] = AvailableDatabase
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

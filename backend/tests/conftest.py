import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.deps import get_database
from app.main import create_app
from app.core.config import Settings
from app.core.database import get_db


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


@pytest.fixture
def migration_config():
    return Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))


@pytest.fixture
def pg_engine(migration_config):
    raw_url = os.getenv("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated local PostgreSQL database ending in _test.")
    url = make_url(raw_url)
    if (url.get_backend_name() != "postgresql"
            or url.host not in {"localhost", "127.0.0.1", "::1"}
            or not (url.database or "").endswith("_test")):
        pytest.fail("TEST_DATABASE_URL must name a local PostgreSQL database ending in _test.")
    schema = "devtrace_test_" + uuid4().hex
    admin_engine = create_engine(url, hide_parameters=True)
    engine = create_engine(
        url, connect_args={"options": f"-csearch_path={schema}"}, hide_parameters=True
    )
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        with engine.begin() as connection:
            migration_config.attributes["connection"] = connection
            command.upgrade(migration_config, "head")
        yield engine
    finally:
        engine.dispose()
        # Only the random schema created by this fixture is removed; never the public schema.
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture
def registration_client(pg_engine):
    app = create_app(Settings(REGISTRATION_RATE_LIMIT=5, REGISTRATION_RATE_WINDOW_SECONDS=3600))

    def session_override():
        with Session(pg_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = session_override
    with TestClient(app) as test_client:
        yield test_client

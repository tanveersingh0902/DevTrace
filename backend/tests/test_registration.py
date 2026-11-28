from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier
from uuid import UUID

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApplicationError
from app.core.passwords import verify_password
from app.main import create_app
from app.models import AuditEvent, AuthRateLimit, User
from app.schemas.auth import RegistrationRequest
from app.services.auth_rate_limits import enforce_rate_limit
from app.services.registration import register_user

pytestmark = pytest.mark.postgres
PAYLOAD = {"email": "person@example.com", "password": "a secure passphrase", "display_name": "Person"}


def test_register_persists_hash_and_atomic_audit(registration_client, pg_engine) -> None:
    response = registration_client.post(
        "/api/v1/auth/register", json={**PAYLOAD, "email": " Person@EXAMPLE.COM "},
        headers={"X-Request-ID": "registration-test"},
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "display_name", "is_active", "created_at", "updated_at"}
    assert body["email"] == "person@example.com"
    assert body["is_active"] is True
    assert datetime.fromisoformat(body["created_at"].replace("Z", "+00:00")).utcoffset() == timedelta(0)
    assert "set-cookie" not in response.headers
    with Session(pg_engine) as session:
        user = session.get(User, UUID(body["id"]))
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(PAYLOAD["password"], user.password_hash)
        audit = session.scalars(select(AuditEvent)).one()
        assert audit.actor_id == audit.target_id == user.id
        assert audit.event_type == "user.registered"
        assert audit.target_type == "user"
        assert audit.request_id == "registration-test"
        assert user.password_hash not in response.text
    assert PAYLOAD["password"] not in response.text


def test_duplicate_email_is_case_insensitive_and_does_not_create_audit(registration_client, pg_engine):
    assert registration_client.post("/api/v1/auth/register", json=PAYLOAD).status_code == 201
    duplicate = registration_client.post(
        "/api/v1/auth/register", json={**PAYLOAD, "email": " PERSON@EXAMPLE.COM "}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "registration_conflict"
    assert PAYLOAD["email"] not in duplicate.text
    assert PAYLOAD["password"] not in duplicate.text
    with Session(pg_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"email": "x" * 255 + "@example.com"}, {"password": "bad-secret"},
    {"password": "x" * 129}, {"password": 123456789012}, {"display_name": "   "},
    {"display_name": "x" * 101}, {"display_name": "Person\nName"}, {"is_active": False},
])
def test_invalid_inputs_are_rejected_without_echoing_body(registration_client, pg_engine, changes):
    payload = {**PAYLOAD, **changes}
    response = registration_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "validation_error"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "input" not in response.text and "ctx" not in response.text
    assert str(payload["password"]) not in response.text
    with Session(pg_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 0


def test_concurrent_registration_has_one_winner(pg_engine):
    barrier = Barrier(2)

    def attempt():
        with Session(pg_engine, expire_on_commit=False) as session:
            barrier.wait(timeout=10)
            try:
                register_user(session, RegistrationRequest(**PAYLOAD), request_id="race")
                return 201
            except ApplicationError as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(outcomes) == [201, 409]
    with Session(pg_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_audit_failure_rolls_back_user_and_does_not_leak_secrets(
    registration_client, pg_engine, monkeypatch, caplog
):
    secret = "database-password-and-token-sentinel"

    def fail_audit(*args, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr("app.services.registration.record_registration", fail_audit)
    response = registration_client.post("/api/v1/auth/register", json=PAYLOAD)
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert secret not in response.text
    logs = caplog.text
    assert "RuntimeError" in logs
    assert secret not in logs
    assert PAYLOAD["password"] not in logs
    assert all(record.exc_info is None for record in caplog.records)
    with Session(pg_engine) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_database_rejects_unnormalized_email(pg_engine):
    with Session(pg_engine) as session:
        session.add(User(email="UPPER@example.com", password_hash="unused", display_name="Person"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_rate_limit_counts_invalid_attempts_and_ignores_forwarded_headers(registration_client):
    for number in range(5):
        response = registration_client.post(
            "/api/v1/auth/register", json={**PAYLOAD, "password": "short"},
            headers={"X-Forwarded-For": f"192.0.2.{number}"},
        )
        assert response.status_code == 422
    limited = registration_client.post("/api/v1/auth/register", json=PAYLOAD)
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
    assert 1 <= int(limited.headers["Retry-After"]) <= 3600


def test_rate_limit_survives_app_restart_and_resets_after_expiry(registration_client, pg_engine):
    for _ in range(5):
        registration_client.post("/api/v1/auth/register", json={})
    other_app = create_app()
    other_app.dependency_overrides[get_db] = registration_client.app.dependency_overrides[get_db]
    with TestClient(other_app) as second_client:
        assert second_client.post("/api/v1/auth/register", json=PAYLOAD).status_code == 429
        with Session(pg_engine) as session, session.begin():
            session.execute(update(AuthRateLimit).values(
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
            ))
        assert second_client.post("/api/v1/auth/register", json=PAYLOAD).status_code == 201


def test_rate_limit_is_atomic_for_concurrent_attempts_and_separate_clients(pg_engine):
    def attempt():
        with Session(pg_engine) as session:
            try:
                enforce_rate_limit(session, client_host="192.0.2.1", scope="registration",
                                   limit=3, window_seconds=3600)
                return True
            except ApplicationError as error:
                assert error.status_code == 429
                return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(8)))
    assert outcomes.count(True) == 3
    with Session(pg_engine) as session:
        enforce_rate_limit(session, client_host="192.0.2.2", scope="registration",
                           limit=3, window_seconds=3600)


def test_migration_round_trip_and_metadata_agree(pg_engine, migration_config):
    with pg_engine.begin() as connection:
        migration_config.attributes["connection"] = connection
        command.check(migration_config)
        command.downgrade(migration_config, "20261108_0001")
        assert set(inspect(connection).get_table_names()) == {"alembic_version"}
        command.upgrade(migration_config, "head")
        command.check(migration_config)
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261128_0003"


def test_invalid_request_id_is_replaced_before_audit(registration_client, pg_engine):
    response = registration_client.post(
        "/api/v1/auth/register", json=PAYLOAD, headers={"X-Request-ID": "x" * 129}
    )
    assert response.status_code == 201
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    with Session(pg_engine) as session:
        assert session.scalars(select(AuditEvent)).one().request_id == request_id


def test_unrelated_integrity_error_stays_generic(registration_client, monkeypatch):
    def fail_insert(*args, **kwargs):
        raise IntegrityError("secret-sql", {"password": "secret-value"}, RuntimeError("secret-db"))

    monkeypatch.setattr("app.services.registration.create_user", fail_insert)
    response = registration_client.post("/api/v1/auth/register", json=PAYLOAD)
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "secret-" not in response.text

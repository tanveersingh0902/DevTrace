from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import Settings
from app.core.tokens import refresh_digest
from app.main import create_app
from app.models import AuditEvent, RefreshSession, RefreshToken, User

pytestmark = pytest.mark.postgres
AUTH = "/api/v1/auth/"
CSRF = {"X-CSRF-Protection": "1"}
COOKIE = "devtrace_refresh"
CREDS = {"email": "person@example.org", "password": "a-test-password"}


@pytest.fixture
def api(pg_engine):
    settings = Settings(_env_file=None, JWT_SIGNING_SECRET=token_urlsafe(48),
                        LOGIN_RATE_LIMIT=3, CORS_ORIGINS="https://ui.example.org")
    app = create_app(settings)

    def session_override():
        with Session(pg_engine, expire_on_commit=False) as db:
            yield db

    app.dependency_overrides[get_db] = session_override
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(AUTH + "register", json=dict(CREDS, display_name="Tester")).status_code == 201
        yield client


def login(api):
    response = api.post(AUTH + "login", json=dict(CREDS, email=" Person@EXAMPLE.org "), headers=CSRF)
    assert response.status_code == 200
    return response


def bearer(response):
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_credentials_validation_limit(api):
    bad = api.post(AUTH + "login", headers=CSRF, json=dict(CREDS, password="wrong"))
    unknown = api.post(AUTH + "login", headers=CSRF, json=dict(CREDS, email="other@example.org"))
    assert bad.status_code == unknown.status_code == 401
    assert bad.json()["detail"] == unknown.json()["detail"]
    assert bad.json()["code"] == unknown.json()["code"]
    invalid = api.post(AUTH + "login", headers=CSRF, json=dict(CREDS, email="invalid"))
    assert invalid.status_code == 422
    assert CREDS["password"] not in invalid.text
    limited = api.post(AUTH + "login", headers=CSRF, json=CREDS)
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0


def test_login_me_rotate_logout(api, pg_engine, caplog):
    assert api.get(AUTH + "me").status_code == 401
    response = login(api)
    first = api.cookies[COOKIE]
    cookie = response.headers["set-cookie"].lower()
    for flag in ["httponly", "secure", "samesite=strict", "path=/api/v1/auth"]:
        assert flag in cookie
    assert response.headers["cache-control"] == "no-store"
    assert first not in response.text
    me = api.get(AUTH + "me", headers=bearer(response))
    assert me.status_code == 200
    assert set(me.json()) == {"id", "email", "display_name", "is_active", "created_at", "updated_at"}
    assert me.json()["email"] == CREDS["email"]
    refreshed = api.post(AUTH + "refresh", headers=CSRF)
    assert refreshed.status_code == 200
    second = api.cookies[COOKIE]
    assert second != first and refreshed.json() != response.json()
    with Session(pg_engine) as db:
        tokens = {t.digest: t.used_at for t in db.scalars(select(RefreshToken))}
        assert set(tokens) == {refresh_digest(first), refresh_digest(second)}
        assert tokens[refresh_digest(first)] and tokens[refresh_digest(second)] is None
    assert api.post(AUTH + "logout", headers=CSRF).status_code == 204
    assert COOKIE not in api.cookies
    assert api.post(AUTH + "logout", headers=CSRF).status_code == 204
    assert api.post(AUTH + "refresh", headers=dict(CSRF, Cookie=f"{COOKIE}={second}")).status_code == 401
    for token in (response, refreshed):
        assert api.get(AUTH + "me", headers=bearer(token)).status_code == 401
    with Session(pg_engine) as db:
        assert sorted(db.scalars(select(AuditEvent.event_type))) == [
            "auth.login", "auth.logout", "auth.refresh", "user.registered"]
    for secret in (first, second, CREDS["password"], response.json()["access_token"],
                   refreshed.json()["access_token"], api.app.state.settings.jwt_signing_secret.get_secret_value()):
        assert secret not in caplog.text


def test_concurrent_refresh_revokes_only_replayed_family(api, pg_engine):
    separate = login(api)
    login(api)
    cookie = f"{COOKIE}={api.cookies[COOKIE]}"
    barrier = Barrier(2)

    def attempt(_):
        with TestClient(api.app, base_url="https://testserver") as client:
            barrier.wait(timeout=10)
            return client.post(AUTH + "refresh", headers=dict(CSRF, Cookie=cookie))

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(attempt, range(2)))
    assert sorted(r.status_code for r in responses) == [200, 401]
    winner = next(r for r in responses if r.status_code == 200)
    assert api.get(AUTH + "me", headers=bearer(winner)).status_code == 401
    assert api.post(AUTH + "refresh", headers=dict(CSRF, Cookie=f"{COOKIE}={winner.cookies[COOKIE]}")).status_code == 401
    assert api.get(AUTH + "me", headers=bearer(separate)).status_code == 200
    with Session(pg_engine) as db:
        assert db.scalar(select(AuditEvent.id).where(AuditEvent.event_type == "auth.refresh_reuse"))


@pytest.mark.parametrize("case", ["expired", "inactive"])
def test_session_checks(api, pg_engine, case):
    response = login(api)
    with Session(pg_engine) as db, db.begin():
        if case == "expired":
            db.execute(update(RefreshSession).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
        else:
            db.execute(update(User).values(is_active=False))
    assert api.get(AUTH + "me", headers=bearer(response)).status_code == 401
    assert api.post(AUTH + "refresh", headers=CSRF).status_code == 401
    if case == "inactive":
        assert api.post(AUTH + "login", headers=CSRF, json=CREDS).status_code == 401


def test_earlier_token_reuse_after_multiple_rotations(api):
    login(api)
    original = api.cookies[COOKIE]
    assert api.post(AUTH + "refresh", headers=CSRF).status_code == 200
    latest = api.post(AUTH + "refresh", headers=CSRF)
    assert latest.status_code == 200
    replay = api.post(AUTH + "refresh", headers=dict(CSRF, Cookie=f"{COOKIE}={original}"))
    assert replay.status_code == 401
    assert api.get(AUTH + "me", headers=bearer(latest)).status_code == 401
    assert api.post(AUTH + "refresh", headers=CSRF).status_code == 401


def test_refresh_audit_failure_rolls_back(api, monkeypatch):
    login(api)
    original = api.cookies[COOKIE]

    def fail(*args):
        raise RuntimeError("audit unavailable")

    with monkeypatch.context() as patch:
        patch.setattr("app.services.authentication.record_auth_event", fail)
        assert api.post(AUTH + "refresh", headers=CSRF).status_code == 500
    assert api.cookies[COOKIE] == original
    assert api.post(AUTH + "refresh", headers=CSRF).status_code == 200


def test_csrf(api):
    login(api)
    for route in ["login", "refresh", "logout"]:
        assert api.post(AUTH + route, json=CREDS).status_code == 403
        assert api.post(AUTH + route, json=CREDS, headers=dict(CSRF, Origin="https://untrusted.example")).status_code == 403
    assert api.post(AUTH + "refresh", headers=dict(CSRF, Origin="https://ui.example.org")).status_code == 200

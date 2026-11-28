from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

import jwt
import pytest

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.core.tokens import issue_access, read_access


@pytest.fixture
def settings():
    return Settings(_env_file=None, JWT_SIGNING_SECRET=token_urlsafe(64))


def test_access_claims_and_deadline(settings):
    now = datetime.now(timezone.utc)
    user, family = uuid4(), uuid4()
    deadline = now + timedelta(seconds=15)
    raw = issue_access(settings, user, family, now, deadline)
    assert read_access(settings, raw) == (user, family)
    claims = jwt.decode(raw, options={"verify_signature": False})
    assert claims["exp"] == int(deadline.timestamp())


@pytest.mark.parametrize("case", [
    "expired", "wrong_key", "wrong_algorithm", "wrong_type", "wrong_issuer",
    "wrong_audience", "missing_sid", "bad_subject", "future_iat", "malformed",
])
def test_invalid_access(settings, case):
    now = datetime.now(timezone.utc)
    raw = issue_access(settings, uuid4(), uuid4(), now, now + timedelta(days=1))
    claims = jwt.decode(raw, options={"verify_signature": False})
    key = settings.jwt_signing_secret.get_secret_value()
    alg = "HS256"
    if case == "expired":
        claims.update(iat=claims["iat"] - 120, exp=claims["iat"] - 60)
    elif case == "wrong_key":
        key = token_urlsafe(48)
    elif case == "wrong_algorithm":
        alg = "HS512"
    elif case == "wrong_type":
        claims["type"] = "refresh"
    elif case == "wrong_issuer":
        claims["iss"] = "another-issuer"
    elif case == "wrong_audience":
        claims["aud"] = "another-api"
    elif case == "missing_sid":
        del claims["sid"]
    elif case == "bad_subject":
        claims["sub"] = "missing-user"
    elif case == "future_iat":
        claims["iat"] += 300
    raw = "invalid" if case == "malformed" else jwt.encode(claims, key, algorithm=alg)
    with pytest.raises(ApplicationError) as exc:
        read_access(settings, raw)
    assert exc.value.status_code == 401

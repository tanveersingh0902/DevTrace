from datetime import datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

import jwt

from app.core.config import Settings
from app.core.errors import ApplicationError


def unauthorized() -> ApplicationError:
    return ApplicationError(401, "invalid_credentials", "Invalid credentials.",
                            headers={"WWW-Authenticate": "Bearer"})


def signing_key(settings: Settings) -> str:
    if settings.jwt_signing_secret is None:
        raise ApplicationError(503, "auth_unavailable", "Authentication is unavailable.")
    return settings.jwt_signing_secret.get_secret_value()


def issue_access(settings: Settings, user_id: UUID, session_id: UUID,
                 now: datetime, deadline: datetime) -> str:
    expiry = min(deadline, now + timedelta(minutes=settings.access_token_minutes))
    return jwt.encode({
        "sub": str(user_id), "sid": str(session_id), "jti": str(uuid4()), "type": "access",
        "iss": settings.jwt_issuer, "aud": settings.jwt_audience, "iat": now, "exp": expiry,
    }, signing_key(settings), algorithm="HS256")


def read_access(settings: Settings, token: str) -> tuple[UUID, UUID]:
    try:
        claims = jwt.decode(token, signing_key(settings), algorithms=["HS256"],
                            issuer=settings.jwt_issuer, audience=settings.jwt_audience,
                            options={"strict_aud": True, "require": [
                                "sub", "sid", "jti", "type", "iss", "aud", "iat", "exp"]})
        if (claims["type"] != "access" or type(claims["iat"]) is not int
                or type(claims["exp"]) is not int or claims["exp"] <= claims["iat"]):
            raise unauthorized()
        return UUID(claims["sub"]), UUID(claims["sid"])
    except (jwt.InvalidTokenError, ValueError, AttributeError, TypeError, OverflowError):
        raise unauthorized() from None


def new_refresh() -> str:
    return token_urlsafe(32)


def refresh_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()

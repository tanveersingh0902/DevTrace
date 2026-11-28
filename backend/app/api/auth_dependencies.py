from datetime import datetime, timezone

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApplicationError
from app.core.tokens import read_access, unauthorized
from app.models import User
from app.repositories.sessions import user_for_session


def require_csrf_header(
    request: Request, x_csrf_protection: str | None = Header(default=None),
) -> None:
    origin = request.headers.get("origin")
    if (x_csrf_protection != "1"
            or (origin is not None and origin not in request.app.state.settings.cors_origins)):
        raise ApplicationError(403, "csrf_failed", "Request origin or CSRF header is invalid.")


def current_user(request: Request, db: Session = Depends(get_db),
                 credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))) -> User:
    if credentials is None:
        raise unauthorized()
    user_id, session_id = read_access(request.app.state.settings, credentials.credentials)
    user = user_for_session(db, user_id, session_id, datetime.now(timezone.utc))
    if user is None:
        raise unauthorized()
    return user

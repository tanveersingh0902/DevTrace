from hashlib import sha256
from math import ceil

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.repositories.auth_rate_limits import consume_attempt


def enforce_rate_limit(
    session: Session, *, client_host: str, scope: str, limit: int, window_seconds: int
) -> None:
    key_hash = sha256(client_host.encode("utf-8")).hexdigest()
    # Persist even when validation or registration later fails.
    with session.begin():
        attempts, expires_at, now = consume_attempt(
            session, scope=scope, key_hash=key_hash, limit=limit, window_seconds=window_seconds
        )
    if attempts > limit:
        raise ApplicationError(
            429, "rate_limited", "Too many attempts. Try again later.",
            headers={"Retry-After": str(max(1, ceil((expires_at - now).total_seconds())))},
        )

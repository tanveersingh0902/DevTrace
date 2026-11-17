from datetime import datetime, timedelta

from sqlalchemy import case, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import AuthRateLimit


def consume_attempt(
    session: Session, *, scope: str, key_hash: str, limit: int, window_seconds: int
) -> tuple[int, datetime, datetime]:
    """Atomically consume a shared budget; PostgreSQL serializes concurrent callers."""
    now = func.now()
    session.execute(delete(AuthRateLimit).where(AuthRateLimit.expires_at <= now))
    expiry = now + timedelta(seconds=window_seconds)
    expired = AuthRateLimit.expires_at <= now
    statement = insert(AuthRateLimit).values(
        scope=scope, key_hash=key_hash, attempts=1, expires_at=expiry
    ).on_conflict_do_update(
        index_elements=[AuthRateLimit.scope, AuthRateLimit.key_hash],
        set_={
            "attempts": case(
                (expired, 1), else_=func.least(AuthRateLimit.attempts + 1, limit + 1)
            ),
            "expires_at": case((expired, expiry), else_=AuthRateLimit.expires_at),
        },
    ).returning(AuthRateLimit.attempts, AuthRateLimit.expires_at, now)
    row = session.execute(statement).one()
    return row[0], row[1], row[2]

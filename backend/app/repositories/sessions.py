from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RefreshSession, RefreshToken, User


def lock_family(db: Session, digest: str) -> tuple[RefreshSession, RefreshToken] | None:
    # Lock the stable parent first. Read rotation state in a fresh READ COMMITTED
    # statement after acquiring the lock, including when a concurrent caller just won.
    family = db.scalar(select(RefreshSession).join(RefreshToken)
                       .where(RefreshToken.digest == digest).with_for_update(of=RefreshSession))
    if family is None:
        return None
    token = db.scalars(select(RefreshToken).where(RefreshToken.digest == digest)).one()
    return family, token


def user_for_session(db: Session, user_id: UUID, session_id: UUID, now: datetime) -> User | None:
    return db.scalar(select(User).join(RefreshSession).where(
        User.id == user_id, User.is_active.is_(True), RefreshSession.id == session_id,
        RefreshSession.expires_at > now, RefreshSession.revoked_at.is_(None),
    ))

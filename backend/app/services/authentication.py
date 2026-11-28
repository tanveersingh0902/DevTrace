from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.passwords import hash_password, verify_password
from app.core.tokens import issue_access, new_refresh, refresh_digest, unauthorized
from app.models import RefreshSession, RefreshToken, User
from app.repositories.audit_events import record_auth_event
from app.repositories.sessions import lock_family
from app.repositories.users import find_by_email
from app.schemas.auth import LoginRequest

# Unknown email performs the same Argon2id verification as a known account.
_DUMMY_HASH = hash_password(new_refresh())


def issue_pair(db: Session, family: RefreshSession, settings: Settings,
               now: datetime) -> tuple[str, str, datetime]:
    access = issue_access(settings, family.user_id, family.id, now, family.expires_at)
    refresh = new_refresh()
    db.add(RefreshToken(session_id=family.id, digest=refresh_digest(refresh)))
    return access, refresh, family.expires_at


def login(db: Session, data: LoginRequest, settings: Settings, request_id: str):
    with db.begin():
        user = find_by_email(db, data.email)
        valid = verify_password(data.password.get_secret_value(),
                                user.password_hash if user else _DUMMY_HASH)
        if valid and user and user.is_active:
            now = datetime.now(timezone.utc)
            family = RefreshSession(user_id=user.id, expires_at=now + timedelta(days=settings.refresh_session_days))
            db.add(family)
            db.flush()
            pair = issue_pair(db, family, settings, now)
            record_auth_event(db, "auth.login", request_id, family)
            return pair
        record_auth_event(db, "auth.login_failed", request_id)
    raise unauthorized()


def rotate(db: Session, raw: str, settings: Settings, request_id: str):
    with db.begin():
        locked = lock_family(db, refresh_digest(raw))
        if locked:
            family, token = locked
            now = datetime.now(timezone.utc)
            if family.revoked_at is None and family.expires_at > now:
                if token.used_at is not None:
                    family.revoked_at = now
                    record_auth_event(db, "auth.refresh_reuse", request_id, family)
                elif db.get(User, family.user_id).is_active:
                    token.used_at = now
                    pair = issue_pair(db, family, settings, now)
                    record_auth_event(db, "auth.refresh", request_id, family)
                    return pair
    # Raising inside the transaction would roll back a replay revocation.
    raise unauthorized()


def logout(db: Session, raw: str, request_id: str) -> None:
    with db.begin():
        locked = lock_family(db, refresh_digest(raw))
        if locked:
            family, _ = locked
            if family.revoked_at is None:
                family.revoked_at = datetime.now(timezone.utc)
                record_auth_event(db, "auth.logout", request_id, family)

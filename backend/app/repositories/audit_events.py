from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models import AuditEvent, RefreshSession


def record_auth_event(session: Session, event: str, request_id: str,
                      family: RefreshSession | None = None) -> None:
    session.add(AuditEvent(
        actor_id=family.user_id if family else None, event_type=event,
        target_type="session" if family else "login_attempt",
        target_id=family.id if family else uuid4(), request_id=request_id,
    ))


def record_registration(session: Session, *, user_id: UUID, request_id: str | None) -> None:
    # Deliberately no request body, email, password, token, or arbitrary details payload.
    session.add(AuditEvent(
        actor_id=user_id,
        event_type="user.registered",
        target_type="user",
        target_id=user_id,
        request_id=request_id,
    ))

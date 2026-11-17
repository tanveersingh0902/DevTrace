from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_registration(session: Session, *, user_id: UUID, request_id: str | None) -> None:
    # Deliberately no request body, email, password, token, or arbitrary details payload.
    session.add(AuditEvent(
        actor_id=user_id,
        event_type="user.registered",
        target_type="user",
        target_id=user_id,
        request_id=request_id,
    ))

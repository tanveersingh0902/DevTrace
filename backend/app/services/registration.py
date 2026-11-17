from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.core.passwords import hash_password
from app.models import User
from app.repositories.audit_events import record_registration
from app.repositories.users import create_user
from app.schemas.auth import RegistrationRequest


def register_user(
    session: Session, data: RegistrationRequest, *, request_id: str | None
) -> User:
    # Hash on both success and duplicate paths; database uniqueness handles races.
    encoded_hash = hash_password(data.password.get_secret_value())
    try:
        with session.begin():
            user = create_user(
                session, email=str(data.email), password_hash=encoded_hash,
                display_name=data.display_name,
            )
            record_registration(session, user_id=user.id, request_id=request_id)
    except IntegrityError as exc:
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_users_email":
            raise ApplicationError(
                409, "registration_conflict", "Registration could not be completed."
            ) from None
        raise
    return user

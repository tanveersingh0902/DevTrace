from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import RegistrationRequest, UserResponse
from app.services.auth_rate_limits import enforce_rate_limit
from app.services.registration import register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def limit_registration(request: Request, session: Session = Depends(get_db)) -> None:
    settings = request.app.state.settings
    enforce_rate_limit(
        session, client_host=request.client.host if request.client else "unknown",
        scope="registration", limit=settings.registration_rate_limit,
        window_seconds=settings.registration_rate_window_seconds,
    )


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse,
    dependencies=[Depends(limit_registration)],
)
def register(
    data: RegistrationRequest, request: Request, session: Session = Depends(get_db)
) -> UserResponse:
    user = register_user(session, data, request_id=request.state.request_id)
    return UserResponse.model_validate(user)

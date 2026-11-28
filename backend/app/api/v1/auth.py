from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.auth_dependencies import current_user, require_csrf_header
from app.core.database import get_db
from app.core.tokens import unauthorized
from app.models import User
from app.schemas.auth import AccessResponse, LoginRequest, RegistrationRequest, UserResponse
from app.services import authentication
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


def limit_login(request: Request, session: Session = Depends(get_db)) -> None:
    settings = request.app.state.settings
    enforce_rate_limit(session, client_host=request.client.host if request.client else "unknown",
                       scope="login", limit=settings.login_rate_limit,
                       window_seconds=settings.login_rate_window_seconds)


def cookie_options(request: Request) -> dict:
    return dict(key="devtrace_refresh", path=request.app.state.settings.api_v1_prefix + "/auth",
                httponly=True, secure=True, samesite="strict")


def send_tokens(request: Request, response: Response, pair: tuple[str, str, datetime]) -> AccessResponse:
    access, refresh, expires = pair
    response.set_cookie(value=refresh, expires=expires.astimezone(timezone.utc), **cookie_options(request))
    response.headers["Cache-Control"] = "no-store"
    return AccessResponse(access_token=access)


@router.post("/login", dependencies=[Depends(require_csrf_header), Depends(limit_login)])
def login(data: LoginRequest, request: Request, response: Response,
          session: Session = Depends(get_db)) -> AccessResponse:
    pair = authentication.login(session, data, request.app.state.settings, request.state.request_id)
    return send_tokens(request, response, pair)


@router.post("/refresh", dependencies=[Depends(require_csrf_header)])
def refresh(request: Request, response: Response, session: Session = Depends(get_db)) -> AccessResponse:
    raw = request.cookies.get("devtrace_refresh")
    if not raw:
        raise unauthorized()
    pair = authentication.rotate(session, raw, request.app.state.settings, request.state.request_id)
    return send_tokens(request, response, pair)


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf_header)])
def logout(request: Request, session: Session = Depends(get_db)) -> Response:
    raw = request.cookies.get("devtrace_refresh")
    if raw:
        authentication.logout(session, raw, request.state.request_id)
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(**cookie_options(request))
    return response


@router.get("/me")
def me(response: Response, user: User = Depends(current_user)) -> UserResponse:
    response.headers["Cache-Control"] = "no-store"
    return UserResponse.model_validate(user)

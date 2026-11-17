from fastapi import APIRouter

from app.api.v1.auth import router as auth_router


router = APIRouter()
router.include_router(auth_router)


@router.get("", tags=["system"])
def api_metadata() -> dict[str, str]:
    """Expose only stable API metadata for the foundation release."""

    return {"name": "DevTrace API", "version": "v1"}

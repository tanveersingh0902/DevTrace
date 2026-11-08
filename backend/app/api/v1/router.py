from fastapi import APIRouter


router = APIRouter()


@router.get("", tags=["system"])
def api_metadata() -> dict[str, str]:
    """Expose only stable API metadata for the foundation release."""

    return {"name": "DevTrace API", "version": "v1"}

from fastapi import APIRouter, Depends, status

from app.api.deps import Database, get_database

router = APIRouter(tags=["system"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health() -> dict[str, str]:
    """Liveness probe: the HTTP application process is accepting requests."""

    return {"status": "ok"}


@router.get("/ready")
def ready(database: Database = Depends(get_database)) -> dict[str, str]:
    """Readiness probe: verifies a real SQLAlchemy PostgreSQL connection."""

    if not database.check_connection():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )
    return {"status": "ready"}

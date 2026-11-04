"""HTTP endpoint for scanning an allowed local repository."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.scanner.models import ScanSummary
from app.scanner.scanner import (
    InvalidRepositoryPathError,
    RepositoryNotDirectoryError,
    RepositoryNotFoundError,
    RepositoryPermissionError,
    ScanError,
    ScanLimitExceededError,
    UnsafeRepositoryError,
    scan_repository,
)

router = APIRouter(tags=["Scanner"])


class ScanRequest(BaseModel):
    """Request body for a local repository scan."""

    repository_path: str = Field(min_length=1, max_length=4096)

    @field_validator("repository_path")
    @classmethod
    def require_local_path(cls, value: str) -> str:
        """Reject remote URLs before they reach filesystem path handling."""
        if "://" in value:
            raise ValueError("A local filesystem path is required.")
        return value


@router.post("/scan", response_model=ScanSummary, status_code=status.HTTP_200_OK)
def scan_local_repository(request: ScanRequest) -> ScanSummary:
    """Return file metadata for a repository within configured scan roots."""
    try:
        return scan_repository(request.repository_path)
    except RepositoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository path not found.",
        ) from error
    except RepositoryNotDirectoryError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository path must be a directory.",
        ) from error
    except InvalidRepositoryPathError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid local repository path.",
        ) from error
    except UnsafeRepositoryError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository path is outside configured scan boundaries or is unsafe.",
        ) from error
    except RepositoryPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The server cannot access the requested repository.",
        ) from error
    except ScanLimitExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Repository exceeds configured scan limits.",
        ) from error
    except ScanError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository scan could not be completed.",
        ) from error

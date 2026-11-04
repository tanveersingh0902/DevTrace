"""Structured models returned by the repository scanner."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryInfo(BaseModel):
    """Public, non-sensitive identity for the scanned repository."""

    name: str


class FileInfo(BaseModel):
    """Metadata for one discovered regular file."""

    model_config = ConfigDict(frozen=True)

    path: str
    language: str
    extension: str
    size_bytes: int = Field(ge=0)
    modified_at: datetime


class LanguageStatistics(BaseModel):
    """File count and aggregate size for one detected language."""

    file_count: int = Field(ge=0)
    total_size_bytes: int = Field(ge=0)


class ScanSummary(BaseModel):
    """Complete inventory and aggregate statistics for a repository scan."""

    repository: RepositoryInfo
    total_files: int = Field(ge=0)
    total_size_bytes: int = Field(ge=0)
    total_directories: int = Field(ge=0)
    skipped_files: int = Field(ge=0)
    languages: dict[str, LanguageStatistics]
    directories: list[str]
    files: list[FileInfo]

"""Repository scan orchestration and safe path validation."""

import os
import stat
from pathlib import Path

from app.config import Settings, settings
from app.scanner.file_discovery import discover_files
from app.scanner.language_detector import detect_language
from app.scanner.models import (
    FileInfo,
    LanguageStatistics,
    RepositoryInfo,
    ScanSummary,
)


class ScanError(Exception):
    """Base class for expected repository scan failures."""


class RepositoryNotFoundError(ScanError):
    """The requested repository path does not exist."""


class RepositoryNotDirectoryError(ScanError):
    """The requested repository path is not a directory."""


class UnsafeRepositoryError(ScanError):
    """The requested path is outside the configured scan boundaries."""


class RepositoryPermissionError(ScanError):
    """The scanner cannot access required repository metadata."""


class ScanLimitExceededError(ScanError):
    """The repository exceeds a configured scan safety limit."""


class InvalidRepositoryPathError(ScanError):
    """The requested path is not a supported local filesystem path."""


def _validate_repository_path(repository_path: str | Path, config: Settings) -> Path:
    """Resolve and authorize a repository path without accepting symlink roots."""
    path_text = str(repository_path)
    if not path_text or "://" in path_text:
        raise InvalidRepositoryPathError("Only local filesystem paths are supported.")

    try:
        candidate = Path(path_text).expanduser()
        absolute_candidate = Path(os.path.abspath(candidate))
    except (OSError, ValueError) as error:
        raise InvalidRepositoryPathError("The repository path is invalid.") from error

    allowed_roots: list[Path] = []
    for allowed_root in config.scan_allowed_roots:
        try:
            allowed_roots.append(allowed_root.expanduser().resolve(strict=False))
        except (OSError, RuntimeError, ValueError) as error:
            raise InvalidRepositoryPathError("The configured scan boundary is invalid.") from error

    if not any(
        absolute_candidate == allowed or allowed in absolute_candidate.parents
        for allowed in allowed_roots
    ):
        raise UnsafeRepositoryError("The repository is outside configured scan boundaries.")
    if absolute_candidate.parent == absolute_candidate:
        raise UnsafeRepositoryError("Filesystem roots cannot be scanned.")

    current = Path(absolute_candidate.anchor)
    for component in absolute_candidate.parts[1:]:
        current /= component
        try:
            if current.is_symlink():
                raise UnsafeRepositoryError("Symbolic links are not allowed in scan paths.")
        except PermissionError as error:
            raise RepositoryPermissionError("Unable to validate the repository path.") from error

    try:
        root = absolute_candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise RepositoryNotFoundError("The repository path does not exist.") from error
    except PermissionError as error:
        raise RepositoryPermissionError("Unable to access the repository path.") from error
    except (OSError, RuntimeError, ValueError) as error:
        raise InvalidRepositoryPathError("The repository path is invalid.") from error

    if not any(root == allowed or allowed in root.parents for allowed in allowed_roots):
        raise UnsafeRepositoryError("The repository is outside configured scan boundaries.")

    try:
        metadata = root.stat()
    except FileNotFoundError as error:
        raise RepositoryNotFoundError("The repository path does not exist.") from error
    except PermissionError as error:
        raise RepositoryPermissionError("Unable to access the repository path.") from error
    if not stat.S_ISDIR(metadata.st_mode):
        raise RepositoryNotDirectoryError("The repository path is not a directory.")
    return root


def scan_repository(
    repository_path: str | Path,
    config: Settings = settings,
) -> ScanSummary:
    """Build a bounded metadata inventory for an allowed local repository."""
    root = _validate_repository_path(repository_path, config)
    try:
        discovery = discover_files(
            root,
            max_file_size_bytes=config.max_file_size_bytes,
            max_files=config.max_files,
        )
    except PermissionError as error:
        raise RepositoryPermissionError("Unable to access repository metadata.") from error
    except OverflowError as error:
        raise ScanLimitExceededError(
            "The repository exceeds the configured file-count limit."
        ) from error
    except OSError as error:
        raise ScanError("Unable to complete the repository scan.") from error
    except ValueError as error:
        raise ScanLimitExceededError("Repository ignore rules exceed supported limits.") from error

    files: list[FileInfo] = []
    language_counts: dict[str, tuple[int, int]] = {}
    for discovered_file in discovery.files:
        language = detect_language(Path(discovered_file.relative_path))
        files.append(
            FileInfo(
                path=discovered_file.relative_path,
                language=language,
                extension=discovered_file.extension,
                size_bytes=discovered_file.size_bytes,
                modified_at=discovered_file.modified_at,
            )
        )
        count, total_size = language_counts.get(language, (0, 0))
        language_counts[language] = (count + 1, total_size + discovered_file.size_bytes)

    files.sort(key=lambda file_info: file_info.path)
    languages = {
        language: LanguageStatistics(file_count=count, total_size_bytes=size)
        for language, (count, size) in sorted(language_counts.items())
    }
    return ScanSummary(
        repository=RepositoryInfo(name=root.name),
        total_files=len(files),
        total_size_bytes=sum(file_info.size_bytes for file_info in files),
        total_directories=len(discovery.directories),
        skipped_files=discovery.skipped_files,
        languages=languages,
        directories=sorted(discovery.directories),
        files=files,
    )

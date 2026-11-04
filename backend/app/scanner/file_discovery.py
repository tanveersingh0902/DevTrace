"""Safe recursive discovery of repository directories and file metadata."""

import os
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.scanner.ignore_rules import (
    GitIgnoreRule,
    is_ignored_by_gitignore,
    is_ignored_name,
    load_gitignore_rules,
)


@dataclass(frozen=True)
class DiscoveredFile:
    """Filesystem metadata needed to construct a public file record."""

    relative_path: str
    extension: str
    size_bytes: int
    modified_at: datetime


@dataclass(frozen=True)
class DiscoveryResult:
    """Files, directories, and size-limited files from one traversal."""

    files: list[DiscoveredFile]
    directories: list[str]
    skipped_files: int


def discover_files(
    repository_root: Path,
    max_file_size_bytes: int,
    max_files: int,
) -> DiscoveryResult:
    """Walk a repository without following symlinks or reading source files."""
    discovered: list[DiscoveredFile] = []
    directories: list[str] = []
    skipped_files = 0
    discovered_file_count = 0
    rules_by_directory: dict[Path, list[GitIgnoreRule]] = {}

    def raise_walk_error(error: OSError) -> None:
        raise error

    for current_root, child_directories, file_names in os.walk(
        repository_root,
        topdown=True,
        onerror=raise_walk_error,
        followlinks=False,
    ):
        current_path = Path(current_root)
        relative_directory = current_path.relative_to(repository_root)
        inherited_rules = rules_by_directory.get(relative_directory.parent, [])

        try:
            local_rules = load_gitignore_rules(current_path, relative_directory)
        except ValueError as error:
            raise ValueError("A repository .gitignore file is too large.") from error
        rules = [*inherited_rules, *local_rules]
        rules_by_directory[relative_directory] = rules

        retained_directories: list[str] = []
        for directory_name in sorted(child_directories):
            directory_path = current_path / directory_name
            relative_path = directory_path.relative_to(repository_root)
            if directory_path.is_symlink():
                continue
            if is_ignored_name(directory_name, is_directory=True):
                continue
            if is_ignored_by_gitignore(relative_path, True, rules):
                continue
            retained_directories.append(directory_name)
            directories.append(relative_path.as_posix())
        child_directories[:] = retained_directories

        for file_name in sorted(file_names):
            file_path = current_path / file_name
            relative_path = file_path.relative_to(repository_root)
            if file_path.is_symlink() or is_ignored_name(file_name, is_directory=False):
                continue
            if is_ignored_by_gitignore(relative_path, False, rules):
                continue

            try:
                metadata = file_path.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(metadata.st_mode):
                continue

            discovered_file_count += 1
            if discovered_file_count > max_files:
                raise OverflowError("The repository exceeds the configured file-count limit.")
            if metadata.st_size > max_file_size_bytes:
                skipped_files += 1
                continue

            discovered.append(
                DiscoveredFile(
                    relative_path=relative_path.as_posix(),
                    extension=file_path.suffix.lower(),
                    size_bytes=metadata.st_size,
                    modified_at=datetime.fromtimestamp(metadata.st_mtime, tz=UTC),
                )
            )

    return DiscoveryResult(
        files=discovered,
        directories=directories,
        skipped_files=skipped_files,
    )

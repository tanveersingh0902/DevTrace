"""Tests for safe repository discovery and scan summaries."""

import os
from pathlib import Path

import pytest

from app.config import Settings
from app.scanner.scanner import (
    RepositoryNotDirectoryError,
    RepositoryNotFoundError,
    RepositoryPermissionError,
    ScanLimitExceededError,
    UnsafeRepositoryError,
    scan_repository,
)


def scanner_settings(
    allowed_root: Path,
    *,
    max_file_size_bytes: int = 1_000_000,
    max_files: int = 10_000,
) -> Settings:
    """Create isolated scanner settings for a temporary repository."""
    return Settings(
        scan_allowed_roots=[allowed_root],
        max_file_size_bytes=max_file_size_bytes,
        max_files=max_files,
    )


def test_scans_valid_repository_and_returns_file_metadata(tmp_path: Path):
    source = tmp_path / "main.py"
    source.write_text("print('hello')\n", encoding="utf-8")

    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert summary.repository.name == tmp_path.name
    assert summary.total_files == 1
    assert summary.total_size_bytes == source.stat().st_size
    assert summary.files[0].path == "main.py"
    assert summary.files[0].language == "Python"
    assert summary.files[0].extension == ".py"
    assert summary.files[0].modified_at.tzinfo is not None
    assert summary.languages["Python"].file_count == 1
    assert not hasattr(summary.repository, "root_path")


def test_rejects_nonexistent_repository_path(tmp_path: Path):
    with pytest.raises(RepositoryNotFoundError):
        scan_repository(tmp_path / "missing", scanner_settings(tmp_path))


def test_rejects_file_as_repository(tmp_path: Path):
    file_path = tmp_path / "not-a-directory.py"
    file_path.touch()

    with pytest.raises(RepositoryNotDirectoryError):
        scan_repository(file_path, scanner_settings(tmp_path))


def test_scans_empty_repository(tmp_path: Path):
    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert summary.total_files == 0
    assert summary.total_size_bytes == 0
    assert summary.total_directories == 0
    assert summary.languages == {}


def test_records_nested_directories_and_files(tmp_path: Path):
    nested = tmp_path / "src" / "features"
    nested.mkdir(parents=True)
    (nested / "feature.ts").write_text("export {};\n", encoding="utf-8")

    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert summary.directories == ["src", "src/features"]
    assert summary.total_directories == 2
    assert summary.files[0].path == "src/features/feature.ts"


def test_detects_multiple_languages_and_unknown_extensions(tmp_path: Path):
    (tmp_path / "main.py").touch()
    (tmp_path / "App.java").touch()
    (tmp_path / "app.ts").touch()
    (tmp_path / "notes.custom").touch()

    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert {file.language for file in summary.files} == {
        "Python",
        "Java",
        "TypeScript",
        "Unknown",
    }
    assert summary.languages["Unknown"].file_count == 1


def test_applies_default_and_gitignore_exclusions(tmp_path: Path):
    (tmp_path / ".gitignore").write_text(
        "*.log\n!keep.log\nignored-by-rule/\n",
        encoding="utf-8",
    )
    (tmp_path / ".hidden.py").touch()
    (tmp_path / "discard.log").touch()
    (tmp_path / "keep.log").touch()
    (tmp_path / "compiled.pyc").touch()
    (tmp_path / "temporary.tmp").touch()
    (tmp_path / ".DS_Store").touch()
    (tmp_path / "ignored-by-rule").mkdir()
    (tmp_path / "ignored-by-rule" / "hidden.py").touch()
    for ignored_directory in (".git", "node_modules", "__pycache__", "dist"):
        directory = tmp_path / ignored_directory
        directory.mkdir()
        (directory / "generated.py").touch()

    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert {file.path for file in summary.files} == {
        ".gitignore",
        ".hidden.py",
        "keep.log",
    }
    assert "ignored-by-rule" not in summary.directories


def test_skips_oversized_files_and_reports_count(tmp_path: Path):
    (tmp_path / "large.py").write_bytes(b"x" * 11)
    (tmp_path / "small.py").write_bytes(b"x" * 10)

    summary = scan_repository(
        tmp_path,
        scanner_settings(tmp_path, max_file_size_bytes=10),
    )

    assert [file.path for file in summary.files] == ["small.py"]
    assert summary.skipped_files == 1


def test_enforces_maximum_file_count(tmp_path: Path):
    (tmp_path / "one.py").touch()
    (tmp_path / "two.py").touch()

    with pytest.raises(ScanLimitExceededError):
        scan_repository(tmp_path, scanner_settings(tmp_path, max_files=1))


def test_skips_symbolic_links_by_default(tmp_path: Path):
    target_file = tmp_path / "target.py"
    target_file.touch()
    target_directory = tmp_path / "target-directory"
    target_directory.mkdir()
    (target_directory / "nested.py").touch()
    try:
        (tmp_path / "linked-file.py").symlink_to(target_file)
        (tmp_path / "linked-directory").symlink_to(target_directory, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Cannot create symbolic links on this system: {error}")

    summary = scan_repository(tmp_path, scanner_settings(tmp_path))

    assert {file.path for file in summary.files} == {"target.py", "target-directory/nested.py"}
    assert summary.directories == ["target-directory"]


def test_rejects_repository_outside_configured_roots(tmp_path: Path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside_root = tmp_path / "outside"

    with pytest.raises(UnsafeRepositoryError):
        scan_repository(outside_root, scanner_settings(allowed_root))


def test_reports_permission_errors_during_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def permission_denied(*args, onerror, **kwargs):
        onerror(PermissionError("denied"))
        yield

    monkeypatch.setattr("app.scanner.file_discovery.os.walk", permission_denied)

    with pytest.raises(RepositoryPermissionError):
        scan_repository(tmp_path, scanner_settings(tmp_path))


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="Symbolic links are unavailable.")
def test_rejects_symlinked_repository_root(tmp_path: Path):
    real_root = tmp_path / "real"
    real_root.mkdir()
    link_root = tmp_path / "link"
    try:
        link_root.symlink_to(real_root, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Cannot create symbolic links on this system: {error}")

    with pytest.raises(UnsafeRepositoryError):
        scan_repository(link_root, scanner_settings(tmp_path))

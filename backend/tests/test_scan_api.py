"""API tests for the repository scan endpoint."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def allow_repository_root(monkeypatch, root: Path) -> None:
    """Allow a temporary repository in an API test."""
    monkeypatch.setattr(settings, "scan_allowed_roots", [root])


def test_scan_endpoint_returns_structured_summary(tmp_path: Path, monkeypatch):
    allow_repository_root(monkeypatch, tmp_path)
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

    response = client.post(
        "/api/v1/scan",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["repository"] == {"name": tmp_path.name}
    assert result["total_files"] == 1
    assert result["languages"]["Python"]["file_count"] == 1
    assert result["files"][0]["path"] == "main.py"
    assert "root_path" not in result["repository"]
    assert str(tmp_path) not in response.text


def test_scan_endpoint_rejects_empty_path():
    response = client.post("/api/v1/scan", json={"repository_path": ""})

    assert response.status_code == 422


def test_scan_endpoint_rejects_remote_url():
    response = client.post(
        "/api/v1/scan",
        json={"repository_path": "https://example.com/repository"},
    )

    assert response.status_code == 422


def test_scan_endpoint_handles_missing_path_safely(tmp_path: Path, monkeypatch):
    allow_repository_root(monkeypatch, tmp_path)
    missing_path = tmp_path / "missing"

    response = client.post(
        "/api/v1/scan",
        json={"repository_path": str(missing_path)},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository path not found."
    assert str(tmp_path) not in response.text


def test_scan_endpoint_rejects_non_directory_path(tmp_path: Path, monkeypatch):
    allow_repository_root(monkeypatch, tmp_path)
    file_path = tmp_path / "file.py"
    file_path.touch()

    response = client.post(
        "/api/v1/scan",
        json={"repository_path": str(file_path)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository path must be a directory."


def test_scan_endpoint_forbids_paths_outside_configured_roots(tmp_path: Path, monkeypatch):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside_root = tmp_path / "outside"
    allow_repository_root(monkeypatch, allowed_root)

    response = client.post(
        "/api/v1/scan",
        json={"repository_path": str(outside_root)},
    )

    assert response.status_code == 403

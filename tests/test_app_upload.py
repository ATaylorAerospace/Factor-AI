"""Tests for upload handling in the analyze endpoint."""

from __future__ import annotations


from fastapi.testclient import TestClient

from factor.app import app


def test_upload_filename_traversal_is_sanitized(tmp_path, monkeypatch):
    """A filename containing path traversal must not escape the upload dir."""
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/v1/analyze",
        files={"files": ("../../escape.txt", b"Section 1. Test provision text.", "text/plain")},
    )
    assert response.status_code == 200
    # Analysis ran (session event streamed), i.e. the file was accepted
    assert "session_id" in response.text

    # Nothing may be written outside uploads/<session_id>/
    assert not (tmp_path / "escape.txt").exists()
    assert not (tmp_path.parent / "escape.txt").exists()
    assert not (tmp_path.parent.parent / "escape.txt").exists()

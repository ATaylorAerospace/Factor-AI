"""Tests for upload handling in the analyze endpoint."""

from __future__ import annotations

import json

import fitz
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


# ---------------------------------------------------------------------------
# Regression tests for the batch pipeline
# ---------------------------------------------------------------------------


def _events(response_text: str) -> list[tuple[str, dict]]:
    """Parse the raw SSE body into (event, data) pairs."""
    events = []
    for block in response_text.replace("\r\n", "\n").split("\n\n"):
        event = data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        if event:
            events.append((event, data))
    return events


def _contract(sections: int, tag: str = "") -> bytes:
    return "\n".join(
        f"{i}. Clause {i}{tag}: the parties agree to the obligations set out here in detail."
        for i in range(1, sections + 1)
    ).encode()


def _analyze(client: TestClient, files: list[tuple[str, bytes, str]]):
    response = client.post("/api/v1/analyze", files=[("files", f) for f in files])
    return response, _events(response.text)


def _section(report: dict, title: str) -> list[dict]:
    return next(s["items"] for s in report["sections"] if s["title"] == title)


def test_large_batch_is_not_halted_by_step_limit(tmp_path, monkeypatch):
    """250 clauses exceed guardrail_max_steps (200) but make no LLM calls."""
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    _, events = _analyze(client, [(f"c{i}.txt", _contract(25), "text/plain") for i in range(10)])

    names = [e for e, _ in events]
    assert "guardrail_halt" not in names
    report = next(d for e, d in events if e == "report")
    assert len(_section(report, "Risk Assessment")) == 250


def test_same_filename_uploads_are_both_analyzed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    _, events = _analyze(client, [
        ("Agreement.txt", _contract(3, " A"), "text/plain"),
        ("Agreement.txt", _contract(6, " B"), "text/plain"),
    ])

    ingested = [(d["document"], d["provisions_found"]) for e, d in events
                if e == "progress" and d["stage"] == "ingestion"]
    assert ingested == [("Agreement.txt", 3), ("Agreement.txt (2)", 6)]


def test_results_are_labeled_with_filenames(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    _, events = _analyze(client, [("msa.txt", _contract(3), "text/plain")])

    report = next(d for e, d in events if e == "report")
    for item in _section(report, "Risk Assessment"):
        assert item["document"] == "msa.txt"
        assert item["provision_type"]
        assert item["excerpt"]
    for gap in _section(report, "Gap Analysis"):
        assert gap["document"] == "msa.txt"


def test_legacy_doc_upload_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze",
        files={"files": ("legacy.doc", b"\xd0\xcf\x11\xe0" + b"\x00" * 64, "application/msword")},
    )
    assert response.status_code == 400
    uploads = tmp_path / "uploads"
    assert not uploads.exists() or not any(uploads.iterdir())


def test_unreadable_files_are_skipped_and_batch_continues(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blank = fitz.open()
    blank.new_page()
    client = TestClient(app)
    _, events = _analyze(client, [
        ("broken.pdf", b"%PDF-1.7\n" + b"\x00garbage" * 64, "application/pdf"),
        ("scanned.pdf", blank.tobytes(), "application/pdf"),
        ("good.txt", _contract(3), "text/plain"),
    ])

    skipped = [d["document"] for e, d in events if e == "document_skipped"]
    assert skipped == ["broken.pdf", "scanned.pdf"]
    report = next(d for e, d in events if e == "report")
    assert [d["document"] for d in report["skipped_documents"]] == ["broken.pdf", "scanned.pdf"]
    # The scanned PDF must not be reported as "missing" every provision.
    assert {g["document"] for g in _section(report, "Gap Analysis")} <= {"good.txt"}


def test_all_files_unreadable_gives_unknown_risk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blank = fitz.open()
    blank.new_page()
    client = TestClient(app)
    _, events = _analyze(client, [("scanned.pdf", blank.tobytes(), "application/pdf")])

    report = next(d for e, d in events if e == "report")
    assert report["overall_risk"] == "unknown"


def test_unexpected_error_emits_error_event(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def boom(**_kwargs):
        raise RuntimeError("comparison exploded")

    monkeypatch.setattr("factor.app.compare_across_documents", boom)
    client = TestClient(app)
    _, events = _analyze(client, [("a.txt", _contract(3), "text/plain")])

    error = next(d for e, d in events if e == "error")
    assert "comparison exploded" in error["detail"]
    session = client.get(f"/api/v1/sessions/{error['session_id']}").json()
    assert session["status"] == "failed"


def test_export_downloads_file_and_delete_removes_session(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    _, events = _analyze(client, [("a.txt", _contract(3), "text/plain")])
    session_id = next(d["session_id"] for e, d in events if e == "session")

    excel = client.get(f"/api/v1/reports/{session_id}/export", params={"format": "excel"})
    assert excel.status_code == 200
    assert "attachment" in excel.headers["content-disposition"]
    assert excel.content[:2] == b"PK"  # xlsx is a zip archive

    html = client.get(f"/api/v1/reports/{session_id}/export", params={"format": "html"})
    assert html.status_code == 200
    assert b"Due Diligence Risk Report" in html.content

    assert client.delete(f"/api/v1/sessions/{session_id}").status_code == 200
    assert client.get(f"/api/v1/sessions/{session_id}").status_code == 404
    assert not (tmp_path / "reports" / session_id).exists()

"""Tests for the in-memory session store."""

from __future__ import annotations

from factor.db.database import SessionStore


def test_expired_sessions_are_evicted_with_their_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SessionStore(ttl_seconds=0)
    store.create_session("old", ["a.pdf"])
    (tmp_path / "reports" / "old").mkdir(parents=True)

    store.create_session("new", ["b.pdf"])

    assert store.get_session("old") is None
    assert not (tmp_path / "reports" / "old").exists()


def test_store_is_capped_at_max_sessions():
    store = SessionStore(max_sessions=2)
    for sid in ("s1", "s2", "s3"):
        store.create_session(sid, [])
    assert [s["session_id"] for s in store.list_sessions()] == ["s2", "s3"]


def test_get_session_returns_a_copy():
    store = SessionStore()
    store.create_session("s1", [])
    store.store_result("s1", {"title": "Report"})

    copy = store.get_session("s1")
    copy["result"]["title"] = "changed"
    assert store.get_session("s1")["result"]["title"] == "Report"

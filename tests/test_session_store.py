"""Tests for the in-memory session store."""

from __future__ import annotations

import pytest

from factor.db.database import SessionStore, safe_session_subdir


def test_expired_sessions_are_evicted_with_their_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SessionStore(ttl_seconds=0)
    store.create_session("old", ["a.pdf"])
    (tmp_path / "reports" / "old").mkdir(parents=True)

    store.create_session("new", ["b.pdf"])

    assert store.get_session("old") is None
    assert not (tmp_path / "reports" / "old").exists()


def test_expired_session_evicted_on_get_without_new_session(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SessionStore(ttl_seconds=0)
    store.create_session("s1", ["a.pdf"])
    (tmp_path / "reports" / "s1").mkdir(parents=True)

    assert store.get_session("s1") is None
    assert not (tmp_path / "reports" / "s1").exists()


def test_expired_sessions_evicted_on_list_sessions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SessionStore(ttl_seconds=0)
    store.create_session("s1", ["a.pdf"])
    (tmp_path / "uploads" / "s1").mkdir(parents=True)

    assert store.list_sessions() == []
    assert not (tmp_path / "uploads" / "s1").exists()


@pytest.mark.parametrize(
    "bad_session_id",
    ["", ".", "..", "../secret", "a/b", "a\\b", "/etc/passwd"],
)
def test_safe_session_subdir_rejects_traversal(bad_session_id):
    with pytest.raises(ValueError, match="Invalid session_id"):
        safe_session_subdir("reports", bad_session_id)


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

"""In-memory session store (local dev) with DynamoDB interface for production."""

from __future__ import annotations

import copy
import logging
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


logger = logging.getLogger(__name__)


def _session_dirs(session_id: str) -> tuple[Path, Path]:
    return Path(f"uploads/{session_id}"), Path(f"reports/{session_id}")


class SessionStore:
    """Session and result storage.

    Uses in-memory dict for development. In production, backs to DynamoDB
    via AgentCore. Thread-safe for concurrent FastAPI requests.

    Sessions expire after ``ttl_seconds`` and the store never holds more than
    ``max_sessions``; expired or evicted sessions are removed together with
    their upload and report files, so memory and disk use stay bounded.
    """

    def __init__(self, ttl_seconds: float = 24 * 3600, max_sessions: int = 500):
        self._sessions: dict[str, dict] = {}
        self._created: dict[str, float] = {}
        self._lock = threading.Lock()
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions

    def _evict_unlocked(self) -> list[str]:
        """Drop expired sessions, then the oldest ones, leaving room for one new session."""
        now = time.monotonic()
        evicted = [sid for sid, t in self._created.items() if now - t > self.ttl_seconds]
        overflow = len(self._created) - len(evicted) - (self.max_sessions - 1)
        if overflow > 0:
            remaining = sorted(
                (t, sid) for sid, t in self._created.items() if sid not in evicted
            )
            evicted.extend(sid for _, sid in remaining[:overflow])
        for sid in evicted:
            self._sessions.pop(sid, None)
            self._created.pop(sid, None)
        return evicted

    @staticmethod
    def _remove_files(session_ids: list[str]) -> None:
        for sid in session_ids:
            for directory in _session_dirs(sid):
                shutil.rmtree(directory, ignore_errors=True)

    def create_session(self, session_id: str, filenames: list[str]) -> dict:
        """Create a new analysis session.

        Args:
            session_id: Unique session identifier.
            filenames: List of uploaded document filenames.

        Returns:
            Session record dictionary.
        """
        session = {
            "session_id": session_id,
            "status": "created",
            "filenames": filenames,
            "document_count": len(filenames),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "trace": [],
        }
        with self._lock:
            evicted = self._evict_unlocked()
            self._sessions[session_id] = session
            self._created[session_id] = time.monotonic()
        self._remove_files(evicted)
        if evicted:
            logger.info("Evicted %d expired sessions", len(evicted))
        logger.info("Created session %s with %d documents", session_id, len(filenames))
        return copy.deepcopy(session)

    def get_session(self, session_id: str) -> dict | None:
        """Retrieve a copy of a session by ID.

        Args:
            session_id: The session to retrieve.

        Returns:
            Session dict or None if not found. Callers may modify the copy freely.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return copy.deepcopy(session) if session is not None else None

    def update_status(self, session_id: str, status: str, error: str | None = None) -> None:
        """Update session status.

        Args:
            session_id: The session to update.
            status: New status string.
            error: Optional error message to record with the status.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["status"] = status
                self._sessions[session_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
                if error is not None:
                    self._sessions[session_id]["error"] = error

    def store_result(self, session_id: str, result: dict) -> None:
        """Store analysis result for a session.

        Args:
            session_id: The session to store results for.
            result: The analysis/report result dictionary.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["result"] = result
                self._sessions[session_id]["status"] = "completed"
                self._sessions[session_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                logger.info("Stored result for session %s", session_id)

    def add_trace(self, session_id: str, trace_entry: dict) -> None:
        """Add a trace entry to a session.

        Args:
            session_id: The session to add trace to.
            trace_entry: Trace event dictionary.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["trace"].append(trace_entry)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its data (privacy compliance).

        Args:
            session_id: The session to delete.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            del self._sessions[session_id]
            self._created.pop(session_id, None)
        self._remove_files([session_id])
        logger.info("Deleted session %s", session_id)
        return True

    def list_sessions(self) -> list[dict]:
        """List all sessions (dev only).

        Returns:
            List of session summaries.
        """
        with self._lock:
            return [
                {
                    "session_id": s["session_id"],
                    "status": s["status"],
                    "document_count": s["document_count"],
                    "created_at": s["created_at"],
                }
                for s in self._sessions.values()
            ]

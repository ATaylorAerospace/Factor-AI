"""In-memory session store (local dev) with DynamoDB interface for production."""

from __future__ import annotations

import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from factor.config import settings

logger = logging.getLogger(__name__)


class SessionStore:
    """Session and result storage.

    Uses in-memory dict for development. In production, backs to DynamoDB
    via AgentCore. Thread-safe for concurrent FastAPI requests.
    """

    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()

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
            self._sessions[session_id] = session
        logger.info("Created session %s with %d documents", session_id, len(filenames))
        return session

    def get_session(self, session_id: str) -> dict | None:
        """Retrieve a session by ID.

        Args:
            session_id: The session to retrieve.

        Returns:
            Session dict or None if not found.
        """
        with self._lock:
            return self._sessions.get(session_id)

    def update_status(self, session_id: str, status: str) -> None:
        """Update session status.

        Args:
            session_id: The session to update.
            status: New status string.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["status"] = status
                self._sessions[session_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

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
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info("Deleted session %s", session_id)
                # Clean up associated files on disk
                for directory in (Path(f"uploads/{session_id}"), Path(f"reports/{session_id}")):
                    if directory.exists():
                        shutil.rmtree(directory, ignore_errors=True)
                return True
            return False

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

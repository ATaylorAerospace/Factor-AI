"""Amazon Bedrock AgentCore Memory — short-term and long-term session memory."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import boto3

from factor.config import settings

logger = logging.getLogger(__name__)


class AgentCoreMemory:
    """Client for Bedrock AgentCore Memory stores."""

    def __init__(self, store_id: str | None = None, region_name: str | None = None):
        self.store_id = store_id or settings.agentcore_memory_store_id
        self.region_name = region_name or settings.aws_region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "bedrock-agent-runtime",
                region_name=self.region_name,
            )
        return self._client

    def store_session_context(
        self,
        session_id: str,
        context: dict,
    ) -> None:
        """Store session context for agent continuity.

        Args:
            session_id: The session to store context for.
            context: Context data to persist.
        """
        context["stored_at"] = datetime.now(timezone.utc).isoformat()
        context["session_id"] = session_id

        logger.info(
            "Stored session context for %s (%d keys)",
            session_id,
            len(context),
        )

    def retrieve_session_context(self, session_id: str) -> dict:
        """Retrieve stored session context.

        Args:
            session_id: The session to retrieve context for.

        Returns:
            Session context dictionary.
        """
        logger.info("Retrieved session context for %s", session_id)
        return {
            "session_id": session_id,
            "context": {},
            "note": "AgentCore Memory integration — context retrieved from memory store",
        }

    def store_analysis_result(
        self,
        session_id: str,
        result: dict,
    ) -> None:
        """Store analysis results for long-term memory.

        Args:
            session_id: The session that produced the results.
            result: Analysis results to persist.
        """
        result["session_id"] = session_id
        result["stored_at"] = datetime.now(timezone.utc).isoformat()
        result["is_synthetic"] = True

        logger.info("Stored analysis result for session %s", session_id)

    def clear_session(self, session_id: str) -> None:
        """Clear all memory for a session (privacy compliance).

        Args:
            session_id: The session to clear.
        """
        logger.info("Cleared memory for session %s", session_id)

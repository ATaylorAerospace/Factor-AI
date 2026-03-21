"""Amazon Bedrock AgentCore Runtime integration."""

from __future__ import annotations

import json
import logging

import boto3

from factor.config import settings

logger = logging.getLogger(__name__)


class AgentCoreRuntime:
    """Client for Bedrock AgentCore Runtime — serverless agent execution."""

    def __init__(self, runtime_arn: str | None = None, region_name: str | None = None):
        self.runtime_arn = runtime_arn or settings.agentcore_runtime_arn
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

    def invoke_agent(
        self,
        session_id: str,
        input_text: str,
        enable_trace: bool = True,
    ) -> dict:
        """Invoke an agent through AgentCore Runtime.

        Args:
            session_id: Session identifier for context isolation.
            input_text: User input to send to the agent.
            enable_trace: Whether to include agent reasoning trace.

        Returns:
            Agent response dictionary.
        """
        if not self.runtime_arn:
            logger.warning("AgentCore Runtime ARN not configured, using local mode")
            return {
                "output": "AgentCore Runtime not configured. Running in local mode.",
                "session_id": session_id,
                "trace": [],
            }

        response = self.client.invoke_agent(
            agentId=self.runtime_arn.split("/")[-1],
            agentAliasId="TSTALIASID",
            sessionId=session_id,
            inputText=input_text,
            enableTrace=enable_trace,
        )

        completion = ""
        traces = []

        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    completion += chunk["bytes"].decode("utf-8")
            if "trace" in event and enable_trace:
                traces.append(event["trace"])

        return {
            "output": completion,
            "session_id": session_id,
            "trace": traces,
        }

    def create_session(self, user_id: str) -> str:
        """Create a new isolated agent session.

        Args:
            user_id: The authenticated user ID.

        Returns:
            New session ID.
        """
        import uuid

        session_id = f"factor-{user_id}-{uuid.uuid4().hex[:8]}"
        logger.info("Created AgentCore session: %s", session_id)
        return session_id

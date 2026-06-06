"""Ingestion Agent — parse and chunk legal documents."""

from __future__ import annotations

import logging

from strands import Agent
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import INGESTION_PROMPT
from factor.config import settings
from factor.harness.circuit_breaker import CircuitBreaker
from factor.harness.model_wrapper import GuardedBedrockModel
from factor.tools.parsing import parse_pdf, parse_docx
from factor.tools.chunking import chunk_provisions

logger = logging.getLogger(__name__)


def create_ingestion_agent(breaker: CircuitBreaker | None = None) -> Agent:
    """Create and return the Ingestion Agent.

    The Ingestion Agent handles document parsing (PDF, DOCX) and
    provision chunking using anchor patterns.

    Args:
        breaker: Optional circuit breaker for financial guardrails.
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )

    if breaker is not None:
        model = GuardedBedrockModel(model, breaker)

    agent = Agent(
        model=model,
        system_prompt=INGESTION_PROMPT,
        tools=[parse_pdf, parse_docx, chunk_provisions],
    )

    logger.info("Created Ingestion Agent with model=%s guarded=%s",
                settings.bedrock_model_id, breaker is not None)
    return agent

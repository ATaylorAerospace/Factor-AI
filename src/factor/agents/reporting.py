"""Reporting Agent — assemble and export risk reports."""

from __future__ import annotations

import logging

from strands import Agent
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import REPORTING_PROMPT
from factor.config import settings
from factor.harness.circuit_breaker import CircuitBreaker
from factor.harness.model_wrapper import GuardedBedrockModel
from factor.tools.export import build_risk_report, export_excel, export_html

logger = logging.getLogger(__name__)


def create_reporting_agent(breaker: CircuitBreaker | None = None) -> Agent:
    """Create and return the Reporting Agent.

    The Reporting Agent assembles structured risk reports and exports
    them in multiple formats (JSON, Excel, HTML).

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
        system_prompt=REPORTING_PROMPT,
        tools=[build_risk_report, export_excel, export_html],
    )

    logger.info("Created Reporting Agent with model=%s guarded=%s",
                settings.bedrock_model_id, breaker is not None)
    return agent

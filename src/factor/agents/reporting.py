"""Reporting Agent — assemble and export risk reports."""

from __future__ import annotations

import logging

from strands import Agent
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import REPORTING_PROMPT
from factor.config import settings
from factor.tools.export import build_risk_report, export_excel, export_html

logger = logging.getLogger(__name__)


def create_reporting_agent() -> Agent:
    """Create and return the Reporting Agent.

    The Reporting Agent assembles structured risk reports and exports
    them in multiple formats (JSON, Excel, HTML).
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )

    agent = Agent(
        model=model,
        system_prompt=REPORTING_PROMPT,
        tools=[build_risk_report, export_excel, export_html],
    )

    logger.info("Created Reporting Agent with model=%s", settings.bedrock_model_id)
    return agent

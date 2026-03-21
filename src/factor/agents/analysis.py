"""Analysis Agent — detect, score, and compare provisions."""

from __future__ import annotations

import logging

from strands import Agent
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import ANALYSIS_PROMPT
from factor.config import settings
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents

logger = logging.getLogger(__name__)


def create_analysis_agent() -> Agent:
    """Create and return the Analysis Agent.

    The Analysis Agent handles provision classification, risk scoring,
    gap analysis, and cross-document comparison.
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )

    agent = Agent(
        model=model,
        system_prompt=ANALYSIS_PROMPT,
        tools=[detect_provision_type, score_risk, find_gaps, compare_across_documents],
    )

    logger.info("Created Analysis Agent with model=%s", settings.bedrock_model_id)
    return agent

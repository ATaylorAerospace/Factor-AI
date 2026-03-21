"""Knowledge Agent — search synthetic knowledge base."""

from __future__ import annotations

import logging

from strands import Agent
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import KNOWLEDGE_PROMPT
from factor.config import settings
from factor.tools.rag import search_synthetic_knowledge
from factor.tools.classification import classify_domain
from factor.tools.citations import extract_citations

logger = logging.getLogger(__name__)


def create_knowledge_agent() -> Agent:
    """Create and return the Knowledge Agent.

    The Knowledge Agent searches the synthetic legal knowledge base,
    classifies provisions by domain, and extracts/labels citations.
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )

    agent = Agent(
        model=model,
        system_prompt=KNOWLEDGE_PROMPT,
        tools=[search_synthetic_knowledge, classify_domain, extract_citations],
    )

    logger.info("Created Knowledge Agent with model=%s", settings.bedrock_model_id)
    return agent

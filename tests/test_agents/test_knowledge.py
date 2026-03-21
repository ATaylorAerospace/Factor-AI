"""Tests for the Knowledge Agent."""

from unittest.mock import patch, MagicMock

from factor.agents.prompts import KNOWLEDGE_PROMPT


def test_knowledge_prompt_includes_disclaimer():
    assert "SYNTHETIC" in KNOWLEDGE_PROMPT
    assert "Taylor658/synthetic-legal" in KNOWLEDGE_PROMPT
    assert "NOT legally accurate" in KNOWLEDGE_PROMPT


def test_knowledge_prompt_warns_about_citations():
    assert "citation" in KNOWLEDGE_PROMPT.lower()
    assert "NEVER present synthetic content as real" in KNOWLEDGE_PROMPT


@patch("factor.agents.knowledge.BedrockModel")
@patch("factor.agents.knowledge.Agent")
def test_create_knowledge_agent(mock_agent_cls, mock_model_cls):
    from factor.agents.knowledge import create_knowledge_agent

    mock_model_cls.return_value = MagicMock()
    mock_agent_cls.return_value = MagicMock()

    agent = create_knowledge_agent()
    mock_model_cls.assert_called_once()
    mock_agent_cls.assert_called_once()
    assert agent is not None

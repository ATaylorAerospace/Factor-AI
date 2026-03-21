"""Tests for the Ingestion Agent."""

from unittest.mock import patch, MagicMock

from factor.agents.prompts import INGESTION_PROMPT, SYNTHETIC_DISCLAIMER_BLOCK


def test_ingestion_prompt_includes_disclaimer():
    assert "SYNTHETIC" in INGESTION_PROMPT
    assert "Taylor658/synthetic-legal" in INGESTION_PROMPT
    assert "NOT legally accurate" in INGESTION_PROMPT


def test_ingestion_prompt_includes_role():
    assert "Ingestion Agent" in INGESTION_PROMPT
    assert "parsing" in INGESTION_PROMPT.lower()
    assert "chunking" in INGESTION_PROMPT.lower()


@patch("factor.agents.ingestion.BedrockModel")
@patch("factor.agents.ingestion.Agent")
def test_create_ingestion_agent(mock_agent_cls, mock_model_cls):
    from factor.agents.ingestion import create_ingestion_agent

    mock_model_cls.return_value = MagicMock()
    mock_agent_cls.return_value = MagicMock()

    agent = create_ingestion_agent()
    mock_model_cls.assert_called_once()
    mock_agent_cls.assert_called_once()
    assert agent is not None

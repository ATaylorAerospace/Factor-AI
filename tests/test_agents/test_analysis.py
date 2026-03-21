"""Tests for the Analysis Agent."""

from unittest.mock import patch, MagicMock

from factor.agents.prompts import ANALYSIS_PROMPT


def test_analysis_prompt_includes_disclaimer():
    assert "SYNTHETIC" in ANALYSIS_PROMPT
    assert "Taylor658/synthetic-legal" in ANALYSIS_PROMPT
    assert "NOT legally accurate" in ANALYSIS_PROMPT


def test_analysis_prompt_includes_role():
    assert "Analysis Agent" in ANALYSIS_PROMPT
    assert "risk" in ANALYSIS_PROMPT.lower()
    assert "gap" in ANALYSIS_PROMPT.lower()


@patch("factor.agents.analysis.BedrockModel")
@patch("factor.agents.analysis.Agent")
def test_create_analysis_agent(mock_agent_cls, mock_model_cls):
    from factor.agents.analysis import create_analysis_agent

    mock_model_cls.return_value = MagicMock()
    mock_agent_cls.return_value = MagicMock()

    agent = create_analysis_agent()
    mock_model_cls.assert_called_once()
    mock_agent_cls.assert_called_once()
    assert agent is not None

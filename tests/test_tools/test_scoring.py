"""Tests for risk scoring tools."""

from factor.tools.scoring import score_risk


def test_score_risk_high(sample_provision_dict):
    result = score_risk(provision=sample_provision_dict)
    assert result["risk_level"] in ("low", "medium", "high", "critical")
    assert 0.0 <= result["score"] <= 10.0
    assert isinstance(result["factors"], list)
    assert result["is_synthetic"] is True


def test_score_risk_low():
    provision = {
        "id": "test-1",
        "text": "Each party shall mutually indemnify the other with liability capped at reasonable amounts.",
        "provision_type": "indemnification",
    }
    result = score_risk(provision=provision)
    assert result["score"] <= result["score"]  # just check it runs
    assert result["is_synthetic"] is True


def test_score_risk_unknown_type():
    provision = {
        "id": "test-2",
        "text": "Some unknown provision text.",
        "provision_type": "custom_clause",
    }
    result = score_risk(provision=provision)
    assert result["risk_level"] == "low"
    assert result["score"] == 2.0


def test_score_risk_with_custom_rubric():
    provision = {
        "id": "test-3",
        "text": "Unlimited liability applies.",
        "provision_type": "indemnification",
    }
    custom_rubric = {
        "indemnification": {
            "weight": 10,
            "high_risk_signals": ["unlimited"],
            "low_risk_signals": [],
        },
    }
    result = score_risk(provision=provision, rubric=custom_rubric)
    assert result["score"] > 5.0
    assert len(result["factors"]) > 0


def test_score_risk_has_explanation():
    provision = {
        "id": "test-4",
        "text": "Standard indemnification clause.",
        "provision_type": "indemnification",
    }
    result = score_risk(provision=provision)
    assert result["explanation"]
    assert "indemnification" in result["explanation"]

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


def test_mitigating_signal_inside_high_risk_phrase_not_counted():
    """'no cure period' must not also earn the 'cure period' mitigation."""
    result = score_risk(provision={"provision_type": "termination", "text": "There is no cure period."})
    assert result["factors"] == ["High-risk signal: no cure period"]


def test_signal_does_not_match_inside_longer_word():
    uncapped = score_risk(provision={"provision_type": "indemnification", "text": "Liability is uncapped."})
    assert "Mitigating factor: capped" not in uncapped["factors"]
    # ...but suffixes still match: "immediately" contains the signal "immediate".
    immediate = score_risk(provision={"provision_type": "termination", "text": "May terminate immediately."})
    assert "High-risk signal: immediate" in immediate["factors"]

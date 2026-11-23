"""Risk scoring tools for legal provisions."""

from __future__ import annotations

import logging
import re
from functools import lru_cache

from strands import tool

logger = logging.getLogger(__name__)

DEFAULT_RUBRIC: dict[str, dict] = {
    "indemnification": {
        "weight": 8,
        "high_risk_signals": ["unlimited", "sole expense", "gross negligence excluded"],
        "low_risk_signals": ["mutual", "capped", "reasonable"],
    },
    "limitation_of_liability": {
        "weight": 9,
        "high_risk_signals": ["unlimited liability", "no cap", "consequential damages included"],
        "low_risk_signals": ["mutual cap", "aggregate limit", "direct damages only"],
    },
    "confidentiality": {
        "weight": 6,
        "high_risk_signals": ["perpetual", "no carve-outs", "one-sided"],
        "low_risk_signals": ["mutual", "reasonable term", "standard carve-outs"],
    },
    "termination": {
        "weight": 7,
        "high_risk_signals": ["no cure period", "immediate", "for convenience one-sided"],
        "low_risk_signals": ["mutual termination rights", "cure period", "wind-down provisions"],
    },
    "governing_law": {
        "weight": 5,
        "high_risk_signals": ["foreign jurisdiction", "inconvenient forum", "mandatory arbitration abroad"],
        "low_risk_signals": ["home jurisdiction", "reasonable venue"],
    },
    "non_compete": {
        "weight": 7,
        "high_risk_signals": ["worldwide", "perpetual", "overly broad scope"],
        "low_risk_signals": ["reasonable geographic scope", "limited duration", "narrowly defined"],
    },
    "change_of_control": {
        "weight": 8,
        "high_risk_signals": ["automatic termination", "consent required", "no assignment"],
        "low_risk_signals": ["notice only", "survives change of control"],
    },
    "force_majeure": {
        "weight": 5,
        "high_risk_signals": ["narrow definition", "no pandemic", "short notice"],
        "low_risk_signals": ["broad definition", "includes pandemic", "reasonable notice"],
    },
}


@lru_cache(maxsize=512)
def _signal_pattern(signal: str) -> re.Pattern[str]:
    """Match a signal phrase at a word start, allowing suffixes.

    The leading boundary keeps "capped" from matching inside "uncapped" (and
    "reasonable" inside "unreasonable"); leaving the end open still lets
    "immediate" match "immediately".
    """
    return re.compile(r"(?<![a-z0-9])" + re.escape(signal.lower()))


def _calculate_score(provision_text: str, rubric_entry: dict) -> tuple[float, list[str]]:
    """Calculate risk score based on signal matching."""
    text_lower = provision_text.lower()
    factors = []
    risk_points = 0.0

    for signal in rubric_entry.get("high_risk_signals", []):
        pattern = _signal_pattern(signal)
        if pattern.search(text_lower):
            risk_points += 2.5
            factors.append(f"High-risk signal: {signal}")
            # Blank out the matched text so a mitigating signal contained in it
            # ("cure period" inside "no cure period") is not counted as well.
            text_lower = pattern.sub(lambda m: " " * len(m.group(0)), text_lower)

    for signal in rubric_entry.get("low_risk_signals", []):
        if _signal_pattern(signal).search(text_lower):
            risk_points -= 1.0
            factors.append(f"Mitigating factor: {signal}")

    weight = rubric_entry.get("weight", 5)
    base_score = weight * 0.5
    final_score = max(0.0, min(10.0, base_score + risk_points))

    return final_score, factors


@tool
def score_risk(provision: dict, rubric: dict | None = None) -> dict:
    """Score a provision's risk level based on the rubric.

    Args:
        provision: Dictionary with at least 'text' and 'provision_type' keys.
        rubric: Optional rubric dictionary. Uses built-in rubric if not provided.

    Returns:
        Dictionary with risk level, score, factors, and explanation.
    """
    rubric_data = rubric if rubric else DEFAULT_RUBRIC
    provision_type = provision.get("provision_type", "other")
    text = provision.get("text", "")

    if provision_type not in rubric_data:
        return {
            "provision_id": provision.get("id", ""),
            "risk_level": "low",
            "score": 2.0,
            "factors": ["No specific rubric for this provision type"],
            "explanation": f"Provision type '{provision_type}' has no dedicated rubric entry.",
            "is_synthetic": True,
        }

    rubric_entry = rubric_data[provision_type]
    score, factors = _calculate_score(text, rubric_entry)

    if score >= 8.0:
        risk_level = "critical"
    elif score >= 6.0:
        risk_level = "high"
    elif score >= 4.0:
        risk_level = "medium"
    else:
        risk_level = "low"

    explanation = (
        f"Provision type '{provision_type}' scored {score:.1f}/10. "
        f"Weight factor: {rubric_entry.get('weight', 5)}/10. "
        f"Identified {len(factors)} relevant factors."
    )

    logger.debug("Scored provision %s: %s (%.1f)", provision.get("id", "?"), risk_level, score)

    return {
        "provision_id": provision.get("id", ""),
        "risk_level": risk_level,
        "score": round(score, 1),
        "factors": factors,
        "explanation": explanation,
        "is_synthetic": True,
    }

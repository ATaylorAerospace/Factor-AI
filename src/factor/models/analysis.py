"""Analysis result data models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskScore(BaseModel):
    """Risk score for a single provision."""

    provision_id: str
    risk_level: RiskLevel = RiskLevel.LOW
    score: float = Field(default=0.0, ge=0.0, le=10.0)
    factors: list[str] = Field(default_factory=list)
    explanation: str = ""
    is_synthetic: bool = Field(
        default=True,
        description="Whether analysis used synthetic dataset content",
    )


class ProvisionClassification(BaseModel):
    """Classification result for a provision."""

    provision_id: str
    predicted_type: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    legal_domain: str = ""
    is_standard: bool = True
    deviations: list[str] = Field(default_factory=list)


class GapResult(BaseModel):
    """A missing provision identified by gap analysis."""

    document_id: str
    missing_provision: str
    severity: RiskLevel = RiskLevel.MEDIUM
    recommendation: str = ""
    reference_standard: str = ""
    is_synthetic: bool = Field(
        default=True,
        description="Whether reference data is from synthetic dataset",
    )


class ComparisonResult(BaseModel):
    """Cross-document comparison result."""

    provision_type: str
    documents_compared: list[str] = Field(default_factory=list)
    inconsistencies: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    details: str = ""


class AnalysisResult(BaseModel):
    """Complete analysis result for a document batch."""

    session_id: str
    document_ids: list[str] = Field(default_factory=list)
    risk_scores: list[RiskScore] = Field(default_factory=list)
    gaps: list[GapResult] = Field(default_factory=list)
    comparisons: list[ComparisonResult] = Field(default_factory=list)
    classifications: list[ProvisionClassification] = Field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.LOW
    summary: str = ""
    disclaimer: str = (
        "All analysis is AI-generated and may contain errors. "
        "Knowledge base content is synthetic (Taylor658/synthetic-legal). "
        "Not legal advice."
    )
    agent_trace: list[dict] = Field(default_factory=list)
    synthetic_content_used: bool = True

    def overall_risk_score(self) -> float:
        if not self.risk_scores:
            return 0.0
        return sum(s.score for s in self.risk_scores) / len(self.risk_scores)

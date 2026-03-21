"""Report data models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from factor import DISCLAIMER


class ExportFormat(str, Enum):
    JSON = "json"
    EXCEL = "excel"
    HTML = "html"


class ReportSection(BaseModel):
    """A section of a due diligence report."""

    title: str
    content: str
    risk_level: Optional[str] = None
    items: list[dict] = Field(default_factory=list)
    synthetic_content: bool = True


class Report(BaseModel):
    """Complete due diligence report."""

    id: str
    session_id: str
    title: str = "Due Diligence Report"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sections: list[ReportSection] = Field(default_factory=list)
    document_count: int = 0
    overall_risk: str = "low"
    executive_summary: str = ""
    disclaimer: str = DISCLAIMER
    metadata: dict = Field(default_factory=dict)
    synthetic_dataset_used: bool = True

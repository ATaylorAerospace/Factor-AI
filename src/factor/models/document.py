"""Document and provision data models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    NDA = "nda"
    LEASE = "lease"
    LOAN = "loan"
    MERGER = "merger"
    EMPLOYMENT = "employment"
    SUPPLY = "supply"
    LICENSE = "license"
    PARTNERSHIP = "partnership"
    UNKNOWN = "unknown"


class Document(BaseModel):
    """Represents an uploaded legal document."""

    id: str = Field(..., description="Unique document identifier")
    filename: str
    doc_type: DocumentType = DocumentType.UNKNOWN
    text: str = ""
    page_count: int = 0
    file_size_bytes: int = 0
    session_id: str = ""
    metadata: dict = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A chunk of a document, typically a section or paragraph."""

    id: str
    document_id: str
    text: str
    start_page: int = 0
    end_page: int = 0
    chunk_index: int = 0
    metadata: dict = Field(default_factory=dict)


class ProvisionType(str, Enum):
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    NON_ASSIGNMENT = "non_assignment"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    TERMINATION = "termination"
    GOVERNING_LAW = "governing_law"
    FORCE_MAJEURE = "force_majeure"
    CHANGE_OF_CONTROL = "change_of_control"
    REPRESENTATIONS_WARRANTIES = "representations_warranties"
    ENTIRE_AGREEMENT = "entire_agreement"
    SEVERABILITY = "severability"
    WAIVER = "waiver"
    NOTICE = "notice"
    OTHER = "other"


class Provision(BaseModel):
    """A legal provision extracted from a document."""

    id: str
    document_id: str
    provision_type: ProvisionType = ProvisionType.OTHER
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    page_number: int = 0
    section_header: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

"""Shared test fixtures for Factor test suite."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sample_nda_text():
    """Sample NDA document text for testing."""
    return """NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of January 1, 2025.

1. CONFIDENTIAL INFORMATION
The Receiving Party agrees to hold in confidence all Confidential Information
disclosed by the Disclosing Party. Confidential Information includes any
proprietary information, trade secrets, and business plans.

2. NON-COMPETE
The Receiving Party agrees not to compete with the Disclosing Party in any
related business activities for a period of two years within the United States.

3. INDEMNIFICATION
Each Party shall indemnify and hold harmless the other Party from any losses
arising from breach of this Agreement. Liability shall be capped at the
aggregate amount of fees paid.

4. LIMITATION OF LIABILITY
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR CONSEQUENTIAL DAMAGES.
The aggregate liability shall not exceed $1,000,000.

5. TERMINATION
Either Party may terminate this Agreement upon 30 days written notice.
A cure period of 15 days shall apply for material breaches.

6. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

7. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and
supersedes all prior agreements.

8. SEVERABILITY
If any provision of this Agreement is found invalid, the remaining provisions
shall continue in full force and effect.

9. NOTICE
All notices shall be in writing and delivered to the addresses specified herein.
"""


@pytest.fixture
def sample_provision_text():
    """Single provision text for testing."""
    return (
        "Each Party shall indemnify and hold harmless the other Party from "
        "any and all losses, damages, liabilities, and expenses arising from "
        "breach of this Agreement. The aggregate liability under this provision "
        "shall be capped at the total fees paid under this Agreement."
    )


@pytest.fixture
def sample_provisions():
    """List of detected provision type strings."""
    return [
        "confidentiality",
        "non_compete",
        "indemnification",
        "limitation_of_liability",
        "termination",
        "governing_law",
        "entire_agreement",
        "severability",
        "notice",
    ]


@pytest.fixture
def sample_provision_dict():
    """Sample provision dictionary for scoring."""
    return {
        "id": str(uuid.uuid4()),
        "text": (
            "The Borrower shall indemnify the Lender against all losses. "
            "Liability is unlimited and at sole expense of the Borrower."
        ),
        "provision_type": "indemnification",
        "doc_type": "loan",
    }


@pytest.fixture
def sample_provisions_by_doc():
    """Provisions grouped by document for comparison testing."""
    return {
        "doc-1": [
            {
                "provision_type": "governing_law",
                "text": "This Agreement shall be governed by the laws of New York.",
            },
            {
                "provision_type": "indemnification",
                "text": "Party A shall indemnify Party B. Liability is capped at $500,000.",
            },
        ],
        "doc-2": [
            {
                "provision_type": "governing_law",
                "text": "This Agreement shall be governed by the laws of California.",
            },
            {
                "provision_type": "indemnification",
                "text": "Party A shall indemnify Party B. No liability cap applies.",
            },
        ],
    }


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_pdf_path(temp_dir):
    """Create a minimal text file simulating a document for testing."""
    path = Path(temp_dir) / "test_document.txt"
    path.write_text(
        "SAMPLE AGREEMENT\n\n"
        "1. INDEMNIFICATION\n"
        "Party A shall indemnify Party B.\n\n"
        "2. TERMINATION\n"
        "Either party may terminate with 30 days notice.\n"
    )
    return str(path)


@pytest.fixture
def mock_bedrock_model():
    """Mock BedrockModel for agent testing."""
    mock = MagicMock()
    mock.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    mock.region_name = "us-west-2"
    return mock


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for report testing."""
    return {
        "risk_scores": [
            {
                "provision_id": "prov-1",
                "risk_level": "high",
                "score": 7.5,
                "factors": ["High-risk signal: unlimited"],
                "explanation": "High risk due to unlimited liability.",
                "is_synthetic": True,
            },
            {
                "provision_id": "prov-2",
                "risk_level": "low",
                "score": 2.0,
                "factors": ["Mitigating factor: mutual"],
                "explanation": "Low risk with mutual terms.",
                "is_synthetic": True,
            },
        ],
        "gaps": [
            {
                "missing_provision": "force_majeure",
                "severity": "medium",
                "recommendation": "Consider adding a force majeure clause.",
                "is_synthetic": True,
            },
        ],
        "comparisons": [
            {
                "provision_type": "governing_law",
                "documents_compared": ["doc-1", "doc-2"],
                "inconsistencies": ["Multiple jurisdictions: New York, California"],
                "risk_level": "medium",
            },
        ],
        "document_count": 2,
    }


@pytest.fixture
def chroma_temp_dir(temp_dir):
    """Temporary directory for ChromaDB during testing."""
    chroma_path = Path(temp_dir) / "chroma"
    chroma_path.mkdir()
    return str(chroma_path)

"""Tests for the Coordinator Agent."""


from factor.agents.coordinator import analyze_provisions, ingest_documents
from factor.tools.doc_type import infer_doc_type as _infer_doc_type


def test_infer_doc_type_nda():
    text = "This Non-Disclosure Agreement (NDA) is entered into..."
    assert _infer_doc_type(text, "nda_contract.pdf") == "nda"


def test_infer_doc_type_lease():
    text = "This Lease Agreement between Landlord and Tenant for the premises..."
    assert _infer_doc_type(text, "lease.pdf") == "lease"


def test_infer_doc_type_merger():
    text = "This Merger and Acquisition Agreement between Target Company..."
    assert _infer_doc_type(text, "merger.pdf") == "merger"


def test_infer_doc_type_loan():
    text = "This Loan Agreement between Borrower and Lender for the principal amount..."
    assert _infer_doc_type(text, "loan.pdf") == "loan"


def test_infer_doc_type_unknown():
    text = "This is a generic document with no specific signals."
    assert _infer_doc_type(text, "document.pdf") == "unknown"


def test_ingest_documents_with_text_file(sample_pdf_path):
    result = ingest_documents(file_paths=[sample_pdf_path])
    assert len(result) == 1
    doc_id = list(result.keys())[0]
    assert result[doc_id]["provision_count"] > 0
    assert "provisions" in result[doc_id]


def test_infer_doc_type_ignores_nda_inside_other_words():
    """'standard' and 'calendar' contain 'nda' but do not make a lease an NDA."""
    text = "LEASE AGREEMENT. Landlord leases the premises for twelve calendar months at the standard rate."
    assert _infer_doc_type(text, "lease.pdf") == "lease"


def test_ingest_documents_reports_unreadable_file(temp_dir):
    from pathlib import Path

    broken = Path(temp_dir) / "broken.docx"
    broken.write_bytes(b"not really a docx")
    result = ingest_documents(file_paths=[str(broken)])
    (entry,) = result.values()
    assert "Could not read file" in entry["error"]


def test_analyze_provisions_enriches_metadata_and_records_skipped_docs():
    documents = {
        "doc-ok": {
            "filename": "nda_alpha.txt",
            "doc_type": "nda",
            "provisions": [
                {
                    "id": "p1",
                    "text": (
                        "Each Party shall indemnify and hold harmless the other "
                        "Party against all unlimited losses."
                    ),
                }
            ],
        },
        "doc-bad": {
            "filename": "corrupt.pdf",
            "error": "Could not read file",
        },
    }

    result = analyze_provisions(documents=documents)

    assert result["document_count"] == 1
    assert len(result["documents"]) == 1
    assert result["documents"][0]["document"] == "nda_alpha.txt"
    assert len(result["skipped_documents"]) == 1
    assert result["skipped_documents"][0]["document"] == "corrupt.pdf"

    assert len(result["risk_scores"]) == 1
    risk = result["risk_scores"][0]
    assert risk["document"] == "nda_alpha.txt"
    assert risk["provision_type"] == "indemnification"
    assert "indemnify" in risk["excerpt"]

    assert all(g["document"] == "nda_alpha.txt" for g in result["gaps"])

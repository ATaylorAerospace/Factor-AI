"""Tests for the Coordinator Agent."""


from factor.agents.coordinator import _infer_doc_type, ingest_documents


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

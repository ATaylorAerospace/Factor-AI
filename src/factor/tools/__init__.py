"""Factor agent tools — each decorated with @tool for Strands SDK."""

from factor.tools.parsing import parse_pdf, parse_docx
from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.rag import search_synthetic_knowledge
from factor.tools.classification import classify_domain
from factor.tools.citations import extract_citations
from factor.tools.export import export_excel, export_html, build_risk_report

__all__ = [
    "parse_pdf",
    "parse_docx",
    "chunk_provisions",
    "detect_provision_type",
    "score_risk",
    "find_gaps",
    "compare_across_documents",
    "search_synthetic_knowledge",
    "classify_domain",
    "extract_citations",
    "export_excel",
    "export_html",
    "build_risk_report",
]

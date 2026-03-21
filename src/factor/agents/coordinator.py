"""Coordinator Agent — orchestrates the Factor agent system."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from strands import Agent, tool
from strands.models.bedrock import BedrockModel

from factor.agents.prompts import COORDINATOR_PROMPT
from factor.config import settings
from factor.tools.parsing import parse_pdf, parse_docx
from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.rag import search_synthetic_knowledge
from factor.tools.classification import classify_domain
from factor.tools.export import build_risk_report, export_excel, export_html

logger = logging.getLogger(__name__)


@tool
def ingest_documents(file_paths: list[str]) -> dict:
    """Parse and chunk a batch of documents.

    Determines file type and routes to the appropriate parser,
    then chunks each document into provisions.

    Args:
        file_paths: List of file paths to ingest.

    Returns:
        Dictionary mapping document IDs to their parsed provisions.
    """
    results = {}

    for fpath in file_paths:
        doc_id = str(uuid.uuid4())
        path = Path(fpath)
        ext = path.suffix.lower()

        if ext == ".pdf":
            parsed = parse_pdf(file_path=fpath)
        elif ext in (".docx", ".doc"):
            parsed = parse_docx(file_path=fpath)
        else:
            parsed = {"text": path.read_text(errors="replace"), "filename": path.name}

        if parsed.get("error"):
            results[doc_id] = {"error": parsed["error"], "filename": path.name}
            continue

        text = parsed.get("text", "")
        doc_type = _infer_doc_type(text, path.name)
        provisions = chunk_provisions(text=text, doc_type=doc_type)

        results[doc_id] = {
            "filename": parsed.get("filename", path.name),
            "doc_type": doc_type,
            "page_count": parsed.get("pages", 0),
            "provisions": provisions,
            "provision_count": len(provisions),
        }

    logger.info("Ingested %d documents", len(results))
    return results


def _infer_doc_type(text: str, filename: str) -> str:
    """Infer document type from content and filename."""
    combined = (text[:2000] + " " + filename).lower()
    type_signals = {
        "nda": ["non-disclosure", "nda", "confidentiality agreement"],
        "lease": ["lease agreement", "tenant", "landlord", "premises"],
        "loan": ["loan agreement", "borrower", "lender", "principal amount"],
        "merger": ["merger", "acquisition", "purchase agreement", "target company"],
        "employment": ["employment agreement", "employee", "employer", "compensation"],
        "license": ["license agreement", "licensor", "licensee", "royalt"],
        "supply": ["supply agreement", "supplier", "purchase order"],
    }
    for doc_type, signals in type_signals.items():
        if any(s in combined for s in signals):
            return doc_type
    return "unknown"


@tool
def analyze_provisions(documents: dict) -> dict:
    """Run full analysis on ingested documents.

    Detects provision types, scores risks, finds gaps, and compares
    across documents.

    Args:
        documents: Dictionary from ingest_documents output.

    Returns:
        Complete analysis results.
    """
    all_risk_scores = []
    all_gaps = []
    provisions_by_doc = {}

    for doc_id, doc_data in documents.items():
        if doc_data.get("error"):
            continue

        provisions = doc_data.get("provisions", [])
        doc_type = doc_data.get("doc_type", "unknown")
        detected_types = []

        for prov in provisions:
            detection = detect_provision_type(provision_text=prov["text"])
            prov["provision_type"] = detection["provision_type"]
            prov["detection_confidence"] = detection["confidence"]
            detected_types.append(detection["provision_type"])

            risk = score_risk(provision=prov)
            risk["document_id"] = doc_id
            all_risk_scores.append(risk)

        gaps = find_gaps(detected_provisions=detected_types, doc_type=doc_type)
        for gap in gaps:
            gap["document_id"] = doc_id
        all_gaps.extend(gaps)

        provisions_by_doc[doc_id] = provisions

    comparison = compare_across_documents(provisions_by_doc=provisions_by_doc)

    return {
        "risk_scores": all_risk_scores,
        "gaps": all_gaps,
        "comparisons": comparison.get("comparisons", []),
        "document_count": len(documents),
    }


@tool
def search_knowledge(query: str, domain: str | None = None) -> list[dict]:
    """Search the synthetic knowledge base for reference content.

    WARNING: All results are from synthetic dataset.

    Args:
        query: Search query.
        domain: Optional legal domain filter.

    Returns:
        List of synthetic knowledge results.
    """
    return search_synthetic_knowledge(query=query, domain=domain)


@tool
def generate_report(analysis_results: dict, output_dir: str = "./reports") -> dict:
    """Generate the final due diligence report.

    Args:
        analysis_results: Results from analyze_provisions.
        output_dir: Directory for exported files.

    Returns:
        Report dictionary with export paths.
    """
    report = build_risk_report(analysis_results=analysis_results)

    session_id = str(uuid.uuid4())[:8]
    excel_path = f"{output_dir}/report_{session_id}.xlsx"
    html_path = f"{output_dir}/report_{session_id}.html"

    export_excel(report=report, output_path=excel_path)
    export_html(report=report, output_path=html_path)

    report["exports"] = {
        "excel": excel_path,
        "html": html_path,
    }

    return report


def create_coordinator_agent() -> Agent:
    """Create and return the Coordinator Agent.

    The Coordinator orchestrates the full due diligence pipeline:
    ingest → analyze → search knowledge → report.
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )

    agent = Agent(
        model=model,
        system_prompt=COORDINATOR_PROMPT,
        tools=[
            ingest_documents,
            analyze_provisions,
            search_knowledge,
            generate_report,
        ],
    )

    logger.info("Created Coordinator Agent with model=%s", settings.bedrock_model_id)
    return agent

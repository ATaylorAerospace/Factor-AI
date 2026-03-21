"""FastAPI application — API endpoints with SSE streaming."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from factor import DISCLAIMER, __version__
from factor.config import settings
from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.export import build_risk_report, export_excel, export_html
from factor.tools.classification import classify_domain
from factor.tools.citations import extract_citations
from factor.db.database import SessionStore

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Factor — Agentic AI Legal Due Diligence",
    version=__version__,
    description=(
        "Autonomous AI agents for batch contract analysis. "
        "Built with AWS Strands Agents SDK and Bedrock AgentCore. "
        f"\n\n{DISCLAIMER}"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store = SessionStore()


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/v1/analyze")
async def analyze_documents(files: list[UploadFile] = File(...)):
    """Upload documents and stream agentic analysis via SSE.

    Accepts a batch of PDF/DOCX files and returns a streaming response
    with analysis progress and results.
    """
    if len(files) > settings.factor_max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum batch size is {settings.factor_max_batch_size} files",
        )

    session_id = str(uuid.uuid4())
    upload_dir = Path(f"uploads/{session_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for f in files:
        if f.size and f.size > settings.max_upload_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} exceeds {settings.factor_max_upload_mb}MB limit",
            )

        file_path = upload_dir / (f.filename or f"document_{len(saved_paths)}")
        content = await f.read()
        file_path.write_bytes(content)
        saved_paths.append(str(file_path))

    session_store.create_session(session_id, [f.filename or "" for f in files])

    async def event_stream() -> AsyncGenerator[dict, None]:
        yield {"event": "session", "data": json.dumps({"session_id": session_id, "disclaimer": DISCLAIMER})}

        yield {"event": "status", "data": json.dumps({"stage": "ingestion", "message": "Parsing documents..."})}

        all_provisions = {}
        for fpath in saved_paths:
            text = Path(fpath).read_text(errors="replace")
            doc_id = str(uuid.uuid4())
            provisions = chunk_provisions(text=text, doc_type="unknown")
            all_provisions[doc_id] = provisions

            yield {"event": "progress", "data": json.dumps({
                "stage": "ingestion",
                "document": Path(fpath).name,
                "provisions_found": len(provisions),
            })}

        yield {"event": "status", "data": json.dumps({"stage": "analysis", "message": "Analyzing provisions..."})}

        all_risk_scores = []
        all_gaps = []
        provisions_by_doc = {}

        for doc_id, provisions in all_provisions.items():
            detected_types = []
            for prov in provisions:
                detection = detect_provision_type(provision_text=prov["text"])
                prov["provision_type"] = detection["provision_type"]
                detected_types.append(detection["provision_type"])

                risk = score_risk(provision=prov)
                risk["document_id"] = doc_id
                all_risk_scores.append(risk)

            gaps = find_gaps(detected_provisions=detected_types, doc_type="unknown")
            for gap in gaps:
                gap["document_id"] = doc_id
            all_gaps.extend(gaps)

            provisions_by_doc[doc_id] = provisions

        comparison = compare_across_documents(provisions_by_doc=provisions_by_doc)

        yield {"event": "status", "data": json.dumps({"stage": "reporting", "message": "Generating report..."})}

        analysis_results = {
            "risk_scores": all_risk_scores,
            "gaps": all_gaps,
            "comparisons": comparison.get("comparisons", []),
            "document_count": len(all_provisions),
        }

        report = build_risk_report(analysis_results=analysis_results)

        session_store.store_result(session_id, report)

        yield {"event": "report", "data": json.dumps(report)}
        yield {"event": "done", "data": json.dumps({"session_id": session_id, "disclaimer": DISCLAIMER})}

    return EventSourceResponse(event_stream())


@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session status and results."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["disclaimer"] = DISCLAIMER
    return session


@app.get("/api/v1/sessions/{session_id}/trace")
async def get_session_trace(session_id: str):
    """Get agent reasoning trace for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "trace": session.get("trace", []),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/v1/reports/{session_id}")
async def get_report(session_id: str):
    """Get structured report for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    report = session.get("result")
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    report["disclaimer"] = DISCLAIMER
    return report


@app.get("/api/v1/reports/{session_id}/export")
async def export_report(
    session_id: str,
    format: str = Query("excel", regex="^(excel|html)$"),
):
    """Export report in Excel or HTML format."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    report = session.get("result")
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    output_dir = Path(f"reports/{session_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "excel":
        path = str(output_dir / "report.xlsx")
        export_excel(report=report, output_path=path)
    else:
        path = str(output_dir / "report.html")
        export_html(report=report, output_path=path)

    return {"path": path, "format": format, "disclaimer": DISCLAIMER}


@app.get("/api/v1/knowledge/search")
async def search_knowledge(
    q: str = Query(..., min_length=1),
    domain: str | None = None,
    top_k: int = Query(5, ge=1, le=20),
):
    """Search the synthetic knowledge base."""
    from factor.tools.rag import search_synthetic_knowledge

    results = search_synthetic_knowledge(query=q, domain=domain, top_k=top_k)
    return {
        "query": q,
        "domain": domain,
        "results": results,
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/v1/knowledge/domains")
async def list_domains():
    """List all legal domains in the dataset."""
    from factor.knowledge.loader import ALL_DOMAINS, DD_DOMAINS

    return {
        "all_domains": ALL_DOMAINS,
        "due_diligence_domains": DD_DOMAINS,
        "disclaimer": DISCLAIMER,
    }

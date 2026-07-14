"""FastAPI application — API endpoints with SSE streaming."""

from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from factor import DISCLAIMER, __version__
from factor.config import settings
from factor.harness.guardrail import get_guardrail
from factor.harness.exceptions import CircuitBreakerTripped
from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.export import build_risk_report, export_excel, export_html
from factor.tools.parsing import parse_pdf, parse_docx
from factor.db.database import SessionStore

logger = logging.getLogger(__name__)

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

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
    allow_origins=settings.cors_origins,
    allow_credentials=not settings.is_production,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

session_store = SessionStore()


@app.on_event("startup")
async def configure_logging():
    """Configure logging from FACTOR_LOG_LEVEL setting."""
    log_level = getattr(logging, settings.factor_log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger.info("Logging configured: level=%s", settings.factor_log_level)

    if settings.phoenix_enabled:
        from factor.aws.observability import init_tracing
        init_tracing("factor")
        logger.info("Phoenix telemetry initialized")


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

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type '{ext}' for file '{f.filename}'. "
                    f"Allowed types: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
                ),
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

        safe_name = Path(f.filename).name if f.filename else ""
        if not safe_name or safe_name in (".", ".."):
            safe_name = f"document_{len(saved_paths)}"
        file_path = (upload_dir / safe_name).resolve()
        if not file_path.is_relative_to(upload_dir.resolve()):
            raise HTTPException(status_code=400, detail=f"Invalid filename: {f.filename}")
        content = await f.read()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} exceeds {settings.factor_max_upload_mb}MB limit",
            )
        file_path.write_bytes(content)
        saved_paths.append(str(file_path))

    session_store.create_session(session_id, [f.filename or "" for f in files])

    guardrail = get_guardrail()
    breaker = guardrail.register_session(session_id) if settings.guardrail_enabled else None

    async def event_stream() -> AsyncGenerator[dict, None]:
        try:
            yield {"event": "session", "data": json.dumps({"session_id": session_id, "disclaimer": DISCLAIMER})}

            if breaker:
                yield {"event": "guardrail", "data": json.dumps({
                    "stage": "initialized",
                    "budget_usd": settings.guardrail_session_budget_usd,
                    "max_steps": settings.guardrail_max_steps,
                })}

            yield {"event": "status", "data": json.dumps({"stage": "ingestion", "message": "Parsing documents..."})}

            all_provisions = {}
            for fpath in saved_paths:
                doc_id = str(uuid.uuid4())
                ext = Path(fpath).suffix.lower()
                if ext == ".pdf":
                    parsed = parse_pdf(file_path=fpath)
                    text = parsed.get("text", "")
                elif ext in (".docx", ".doc"):
                    parsed = parse_docx(file_path=fpath)
                    text = parsed.get("text", "")
                else:
                    text = Path(fpath).read_text(errors="replace")
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
                for prov_index, prov in enumerate(provisions):
                    detection = detect_provision_type(provision_text=prov["text"])
                    prov["provision_type"] = detection["provision_type"]
                    detected_types.append(detection["provision_type"])

                    risk = score_risk(provision=prov)
                    risk["document_id"] = doc_id
                    all_risk_scores.append(risk)

                    if breaker:
                        breaker.record_step(
                            action="score_risk",
                            meta={"doc_id": doc_id, "provision_index": prov_index},
                        )

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

            if breaker:
                yield {"event": "guardrail", "data": json.dumps({
                    "stage": "completed",
                    **breaker.status(),
                })}

            yield {"event": "report", "data": json.dumps(report)}
            yield {"event": "done", "data": json.dumps({"session_id": session_id, "disclaimer": DISCLAIMER})}

        except CircuitBreakerTripped as exc:
            logger.warning("Circuit breaker halted session %s: %s", session_id, exc)
            session_store.update_status(session_id, "halted")
            yield {"event": "guardrail_halt", "data": json.dumps({
                "halted": True,
                **exc.status,
                "message": str(exc),
                "disclaimer": DISCLAIMER,
            })}

        finally:
            if settings.guardrail_enabled:
                guardrail.remove_session(session_id)
            shutil.rmtree(upload_dir, ignore_errors=True)

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
    format: str = Query("excel", pattern="^(excel|html)$"),
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


@app.get("/api/v1/sessions/{session_id}/budget")
async def get_session_budget(session_id: str):
    """Get real-time budget and guardrail status for a session."""
    guardrail = get_guardrail()
    status = guardrail.session_status(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="No active guardrail for this session")
    status["disclaimer"] = DISCLAIMER
    return status


@app.get("/api/v1/guardrail/status")
async def guardrail_overview():
    """Get guardrail status across all active sessions."""
    guardrail = get_guardrail()
    return {
        "enabled": settings.guardrail_enabled,
        "phoenix_enabled": settings.phoenix_enabled,
        "phoenix_endpoint": settings.phoenix_otlp_endpoint,
        "default_budget_usd": settings.guardrail_session_budget_usd,
        "active_sessions": guardrail.all_sessions(),
        "disclaimer": DISCLAIMER,
    }


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

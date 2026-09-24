"""FastAPI application — API endpoints with SSE streaming."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import uuid
from collections import Counter
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from factor import DISCLAIMER, __version__
from factor.config import settings
from factor.harness.guardrail import get_guardrail
from factor.harness.exceptions import CircuitBreakerTripped
from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.doc_type import infer_doc_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.export import build_risk_report, export_excel, export_html
from factor.tools.parsing import parse_pdf, parse_docx
from factor.db.database import SessionStore

logger = logging.getLogger(__name__)

# Legacy binary .doc files are not accepted: python-docx can only read .docx.
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt"}
UPLOAD_CHUNK_BYTES = 1024 * 1024
EXCERPT_CHARS = 240
NO_TEXT_REASON = (
    "No extractable text — the file may be a scanned image. "
    "Run OCR on it and upload it again."
)

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
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

session_store = SessionStore(
    ttl_seconds=settings.factor_session_ttl_hours * 3600,
    max_sessions=settings.factor_max_sessions,
)


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


def _unique_labels(filenames: list[str]) -> list[str]:
    """Display names for a batch; repeated names get " (2)", " (3)", ..."""
    totals = Counter(filenames)
    seen: Counter[str] = Counter()
    labels = []
    for name in filenames:
        seen[name] += 1
        labels.append(f"{name} ({seen[name]})" if totals[name] > 1 and seen[name] > 1 else name)
    return labels


def _extract_text(path: Path) -> str:
    """Extract plain text from an uploaded file. Raises if the file can't be read."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        parsed = parse_pdf(file_path=str(path))
    elif ext == ".docx":
        parsed = parse_docx(file_path=str(path))
    else:
        return path.read_text(errors="replace")
    if parsed.get("error"):
        raise ValueError(parsed["error"])
    return parsed.get("text", "")


def _ingest_document(doc_id: str, path: Path, label: str) -> dict:
    """Parse and chunk one document. Runs in a worker thread."""
    text = _extract_text(path)
    if not text.strip():
        return {"document_id": doc_id, "document": label, "skipped": True, "reason": NO_TEXT_REASON}

    doc_type = infer_doc_type(text, label)
    provisions = chunk_provisions(text=text, doc_type=doc_type)
    return {
        "document_id": doc_id,
        "document": label,
        "doc_type": doc_type,
        "provisions": provisions,
        "skipped": False,
    }


def _analyze_document(doc: dict) -> tuple[list[dict], list[dict]]:
    """Detect, score, and gap-check one ingested document. Runs in a worker thread."""
    risks = []
    detected_types = []
    for prov in doc["provisions"]:
        detection = detect_provision_type(provision_text=prov["text"])
        prov["provision_type"] = detection["provision_type"]
        prov["detection_confidence"] = detection["confidence"]
        detected_types.append(detection["provision_type"])

        risk = score_risk(provision=prov)
        risk.update({
            "document_id": doc["document_id"],
            "document": doc["document"],
            "provision_type": prov["provision_type"],
            "excerpt": " ".join(prov["text"].split())[:EXCERPT_CHARS],
        })
        risks.append(risk)

    gaps = find_gaps(detected_provisions=detected_types, doc_type=doc["doc_type"])
    for gap in gaps:
        gap["document_id"] = doc["document_id"]
        gap["document"] = doc["document"]
    return risks, gaps


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data)}


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

    Accepts a batch of PDF/DOCX/TXT files and returns a streaming response
    with analysis progress and results. A file that can't be read is reported
    with a ``document_skipped`` event and the rest of the batch continues.
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

    original_names: list[str] = []
    saved_paths: list[Path] = []
    try:
        for index, f in enumerate(files):
            if f.size and f.size > settings.max_upload_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {f.filename} exceeds {settings.factor_max_upload_mb}MB limit",
                )

            safe_name = Path(f.filename).name if f.filename else ""
            if not safe_name or safe_name in (".", ".."):
                safe_name = f"document_{index}"
            # Index prefix keeps two uploads with the same name from overwriting each other.
            file_path = (upload_dir / f"{index:03d}_{safe_name}").resolve()
            if not file_path.is_relative_to(upload_dir.resolve()):
                raise HTTPException(status_code=400, detail=f"Invalid filename: {f.filename}")

            size = 0
            with file_path.open("wb") as out:
                while chunk := await f.read(UPLOAD_CHUNK_BYTES):
                    size += len(chunk)
                    if size > settings.max_upload_bytes:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File {f.filename} exceeds {settings.factor_max_upload_mb}MB limit",
                        )
                    out.write(chunk)

            original_names.append(safe_name)
            saved_paths.append(file_path)
    except BaseException:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise

    labels = _unique_labels(original_names)
    session_store.create_session(session_id, labels)

    guardrail = get_guardrail()
    # The breaker meters LLM token spend. This pipeline is deterministic (no model
    # calls), so clauses are not recorded as reasoning steps: doing so tripped the
    # step limit on ordinary batches of ~10 contracts.
    breaker = guardrail.register_session(session_id) if settings.guardrail_enabled else None

    async def event_stream() -> AsyncGenerator[dict, None]:
        session_store.update_status(session_id, "processing")
        try:
            yield _sse("session", {"session_id": session_id, "disclaimer": DISCLAIMER})

            if breaker:
                yield _sse("guardrail", {
                    "stage": "initialized",
                    "budget_usd": settings.guardrail_session_budget_usd,
                    "max_steps": settings.guardrail_max_steps,
                })

            yield _sse("status", {"stage": "ingestion", "message": "Parsing documents..."})

            documents: list[dict] = []
            skipped: list[dict] = []
            for path, label in zip(saved_paths, labels):
                doc_id = str(uuid.uuid4())
                try:
                    doc = await asyncio.to_thread(_ingest_document, doc_id, path, label)
                except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
                    logger.warning("Could not read %s in session %s: %s", label, session_id, exc)
                    doc = {
                        "document_id": doc_id,
                        "document": label,
                        "skipped": True,
                        "reason": f"Could not read this file ({type(exc).__name__}). "
                                  "It may be corrupt, password-protected, or not the format its extension says.",
                    }

                if doc["skipped"]:
                    entry = {k: doc[k] for k in ("document_id", "document", "reason")}
                    skipped.append(entry)
                    yield _sse("document_skipped", {"stage": "ingestion", **entry})
                    continue

                documents.append(doc)
                yield _sse("progress", {
                    "stage": "ingestion",
                    "document": label,
                    "doc_type": doc["doc_type"],
                    "provisions_found": len(doc["provisions"]),
                })

            yield _sse("status", {"stage": "analysis", "message": "Analyzing provisions..."})

            all_risk_scores: list[dict] = []
            all_gaps: list[dict] = []
            for doc in documents:
                risks, gaps = await asyncio.to_thread(_analyze_document, doc)
                all_risk_scores.extend(risks)
                all_gaps.extend(gaps)
                yield _sse("progress", {
                    "stage": "analysis",
                    "document": doc["document"],
                    "provisions_scored": len(risks),
                    "gaps_found": len(gaps),
                })

            comparison = await asyncio.to_thread(
                compare_across_documents,
                provisions_by_doc={d["document_id"]: d["provisions"] for d in documents},
                doc_labels={d["document_id"]: d["document"] for d in documents},
            )

            yield _sse("status", {"stage": "reporting", "message": "Generating report..."})

            analysis_results = {
                "risk_scores": all_risk_scores,
                "gaps": all_gaps,
                "comparisons": comparison.get("comparisons", []),
                "document_count": len(documents),
                "documents": [
                    {
                        "document_id": d["document_id"],
                        "document": d["document"],
                        "doc_type": d["doc_type"],
                        "provisions_found": len(d["provisions"]),
                    }
                    for d in documents
                ],
                "skipped_documents": skipped,
            }

            report = await asyncio.to_thread(build_risk_report, analysis_results=analysis_results)

            session_store.store_result(session_id, report)

            if breaker:
                yield _sse("guardrail", {"stage": "completed", **breaker.status()})

            yield _sse("report", report)
            yield _sse("done", {"session_id": session_id, "disclaimer": DISCLAIMER})

        except CircuitBreakerTripped as exc:
            logger.warning("Circuit breaker halted session %s: %s", session_id, exc)
            session_store.update_status(session_id, "halted", error=str(exc))
            yield _sse("guardrail_halt", {
                "halted": True,
                **exc.status,
                "message": str(exc),
                "disclaimer": DISCLAIMER,
            })

        except Exception as exc:  # report any failure to the client
            logger.exception("Analysis failed for session %s", session_id)
            session_store.update_status(session_id, "failed", error=str(exc))
            yield _sse("error", {
                "session_id": session_id,
                "message": "Analysis failed unexpectedly. Please try again.",
                "detail": f"{type(exc).__name__}: {exc}",
            })

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


@app.delete("/api/v1/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session, its report, and any exported files."""
    if not session_store.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}


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
def export_report(
    session_id: str,
    format: str = Query("excel", pattern="^(excel|html)$"),
):
    """Download the report as an Excel workbook or HTML file."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    report = session.get("result")
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    # Files live under reports/<session_id>/ and are removed with the session.
    output_dir = Path(f"reports/{session_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    download_name = f"factor-report-{session_id[:8]}"

    if format == "excel":
        path = output_dir / "report.xlsx"
        export_excel(report=report, output_path=str(path))
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{download_name}.xlsx",
        )

    path = output_dir / "report.html"
    export_html(report=report, output_path=str(path))
    return FileResponse(path, media_type="text/html", filename=f"{download_name}.html")


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
def search_knowledge(
    q: str = Query(..., min_length=1),
    domain: str | None = None,
    top_k: int = Query(5, ge=1, le=20),
):
    """Search the synthetic knowledge base.

    Declared as a plain ``def`` so FastAPI runs the embedding + vector search
    in its threadpool instead of blocking the event loop.
    """
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

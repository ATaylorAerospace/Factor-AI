#!/usr/bin/env python3
"""Benchmark Factor tools and analysis pipeline.

Measures execution time for document parsing, chunking, detection,
scoring, and gap analysis on sample documents.

Usage:
    python scripts/benchmark.py [--iterations 10]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from factor.tools.chunking import chunk_provisions
from factor.tools.detection import detect_provision_type
from factor.tools.scoring import score_risk
from factor.tools.gaps import find_gaps
from factor.tools.comparison import compare_across_documents
from factor.tools.classification import classify_domain
from factor.tools.citations import extract_citations
from factor.tools.export import build_risk_report


SAMPLE_TEXT = """
1. INDEMNIFICATION
Party A shall indemnify and hold harmless Party B from any losses.
Liability is capped at the aggregate amount of fees paid.

2. LIMITATION OF LIABILITY
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR CONSEQUENTIAL DAMAGES.
The aggregate liability shall not exceed $1,000,000.

3. CONFIDENTIALITY
All confidential information shall be kept strictly confidential
and not disclosed to any third party without prior written consent.

4. TERMINATION
Either party may terminate this agreement upon 30 days written notice.
A cure period of 15 days applies for material breaches.

5. GOVERNING LAW
This agreement shall be governed by the laws of the State of New York.

6. FORCE MAJEURE
Neither party shall be liable for failure to perform due to force majeure
events including pandemic, natural disasters, and acts of God.

7. REPRESENTATIONS AND WARRANTIES
Each party represents and warrants that it has the authority to enter
into this agreement and perform its obligations hereunder.

8. CHANGE OF CONTROL
In the event of a change of control, the non-affected party may
terminate this agreement upon written notice.
"""


def benchmark_tool(name: str, func, iterations: int, **kwargs) -> float:
    """Benchmark a single tool function."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(**kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)
    print(f"  {name:.<40} avg={avg*1000:.2f}ms  min={min_t*1000:.2f}ms  max={max_t*1000:.2f}ms")
    return avg


def main():
    parser = argparse.ArgumentParser(description="Benchmark Factor tools")
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()

    print(f"Factor Tool Benchmark (iterations={args.iterations})")
    print("=" * 70)

    # Chunking
    benchmark_tool("chunk_provisions", chunk_provisions, args.iterations, text=SAMPLE_TEXT, doc_type="nda")

    # Detection
    provisions = chunk_provisions(text=SAMPLE_TEXT, doc_type="nda")
    if provisions:
        benchmark_tool(
            "detect_provision_type",
            detect_provision_type,
            args.iterations,
            provision_text=provisions[0]["text"],
        )

    # Scoring
    if provisions:
        prov = provisions[0]
        prov["provision_type"] = "indemnification"
        benchmark_tool("score_risk", score_risk, args.iterations, provision=prov)

    # Gap analysis
    detected = ["indemnification", "confidentiality", "termination"]
    benchmark_tool("find_gaps", find_gaps, args.iterations, detected_provisions=detected, doc_type="nda")

    # Classification
    benchmark_tool("classify_domain", classify_domain, args.iterations, provision_text=SAMPLE_TEXT[:500])

    # Citations
    citation_text = "In Smith v. Jones, 123 F.3d 456, the court held that 42 USC § 1983 applies."
    benchmark_tool("extract_citations", extract_citations, args.iterations, text=citation_text)

    # Comparison
    provisions_by_doc = {
        "doc-1": [{"provision_type": "governing_law", "text": "governed by New York"}],
        "doc-2": [{"provision_type": "governing_law", "text": "governed by California"}],
    }
    benchmark_tool(
        "compare_across_documents",
        compare_across_documents,
        args.iterations,
        provisions_by_doc=provisions_by_doc,
    )

    # Report building
    results = {
        "risk_scores": [{"provision_id": "p1", "risk_level": "high", "score": 7.5, "factors": [], "explanation": ""}],
        "gaps": [{"missing_provision": "force_majeure", "severity": "medium", "recommendation": "Add clause"}],
        "comparisons": [],
        "document_count": 2,
    }
    benchmark_tool("build_risk_report", build_risk_report, args.iterations, analysis_results=results)

    print("=" * 70)
    print("Benchmark complete.")


if __name__ == "__main__":
    main()

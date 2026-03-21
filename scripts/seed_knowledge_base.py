#!/usr/bin/env python3
"""Seed the ChromaDB knowledge base with the Taylor658/synthetic-legal dataset.

WARNING: ALL content in this dataset is synthetically generated and NOT legally accurate.

Usage:
    python scripts/seed_knowledge_base.py [--max-rows 10000] [--domains Contract,Corporate]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from factor.config import settings
from factor.knowledge.loader import load_synthetic_dataset, DD_DOMAINS
from factor.knowledge.vectorstore import add_documents, reset_collection, get_vectorstore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Seed Factor knowledge base")
    parser.add_argument("--max-rows", type=int, default=10000, help="Max rows to load")
    parser.add_argument("--domains", type=str, default=None, help="Comma-separated domain filter")
    parser.add_argument("--reset", action="store_true", help="Reset collection before seeding")
    parser.add_argument("--persist-dir", type=str, default=None, help="ChromaDB persist directory")
    args = parser.parse_args()

    persist_dir = args.persist_dir or settings.factor_knowledge_path

    if args.reset:
        logger.info("Resetting existing collection...")
        reset_collection(persist_dir=persist_dir)

    domains = args.domains.split(",") if args.domains else DD_DOMAINS

    logger.info("Loading synthetic-legal dataset (max_rows=%d, domains=%s)", args.max_rows, domains)
    rows = load_synthetic_dataset(domains=domains, max_rows=args.max_rows)
    logger.info("Loaded %d rows", len(rows))

    if not rows:
        logger.warning("No rows loaded. Check dataset availability.")
        return

    documents = []
    metadatas = []
    ids = []

    for row in rows:
        text = f"Legal Problem:\n{row['legal_problem']}\n\nVerified Solution:\n{row['verified_solution']}"
        documents.append(text)
        metadatas.append({
            "legal_domain": row["legal_domain"],
            "verification_method": row["verification_method"],
            "row_id": str(row["id"]),
        })
        ids.append(f"synth-{row['id']}")

    logger.info("Adding %d documents to ChromaDB at %s", len(documents), persist_dir)
    count = add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        persist_dir=persist_dir,
    )

    collection = get_vectorstore(persist_dir=persist_dir)
    logger.info(
        "Seeding complete. Collection '%s' now has %d documents.",
        collection.name,
        collection.count(),
    )


if __name__ == "__main__":
    main()

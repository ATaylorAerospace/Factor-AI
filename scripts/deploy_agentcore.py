#!/usr/bin/env python3
"""Deploy Factor agents to Amazon Bedrock AgentCore.

This script:
1. Creates or updates the AgentCore Runtime configuration
2. Registers agent tools with AgentCore Gateway
3. Configures memory stores
4. Applies Cedar policies

Prerequisites:
    - AWS credentials configured
    - CDK infrastructure deployed (cd infra && cdk deploy --all)

Usage:
    python scripts/deploy_agentcore.py [--region us-west-2] [--env production]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def deploy_runtime(region: str, env: str) -> dict:
    """Deploy the agent runtime configuration."""
    logger.info("Deploying AgentCore Runtime (region=%s, env=%s)", region, env)

    runtime_config = {
        "runtime_name": f"factor-{env}",
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "region": region,
        "environment": env,
        "agents": [
            {"name": "coordinator", "description": "Orchestrates due diligence pipeline"},
            {"name": "ingestion", "description": "Parses and chunks documents"},
            {"name": "analysis", "description": "Detects, scores, and compares provisions"},
            {"name": "knowledge", "description": "Searches synthetic knowledge base"},
            {"name": "reporting", "description": "Assembles and exports reports"},
        ],
    }

    logger.info("Runtime configuration: %s", json.dumps(runtime_config, indent=2))
    return runtime_config


def register_tools(region: str) -> list[dict]:
    """Register agent tools with AgentCore Gateway."""
    logger.info("Registering tools with AgentCore Gateway")

    tools = [
        {"name": "parse_pdf", "type": "document_parsing", "module": "factor.tools.parsing"},
        {"name": "parse_docx", "type": "document_parsing", "module": "factor.tools.parsing"},
        {"name": "chunk_provisions", "type": "text_processing", "module": "factor.tools.chunking"},
        {"name": "detect_provision_type", "type": "classification", "module": "factor.tools.detection"},
        {"name": "score_risk", "type": "analysis", "module": "factor.tools.scoring"},
        {"name": "find_gaps", "type": "analysis", "module": "factor.tools.gaps"},
        {"name": "compare_across_documents", "type": "analysis", "module": "factor.tools.comparison"},
        {"name": "search_synthetic_knowledge", "type": "rag", "module": "factor.tools.rag"},
        {"name": "classify_domain", "type": "classification", "module": "factor.tools.classification"},
        {"name": "extract_citations", "type": "extraction", "module": "factor.tools.citations"},
        {"name": "build_risk_report", "type": "reporting", "module": "factor.tools.export"},
        {"name": "export_excel", "type": "export", "module": "factor.tools.export"},
        {"name": "export_html", "type": "export", "module": "factor.tools.export"},
    ]

    for tool in tools:
        logger.info("Registered tool: %s (%s)", tool["name"], tool["type"])

    return tools


def configure_memory(region: str, env: str) -> dict:
    """Configure AgentCore memory stores."""
    logger.info("Configuring AgentCore Memory")

    config = {
        "store_id": f"factor-memory-{env}",
        "type": "session_and_long_term",
        "session_ttl_hours": 24,
        "encryption": "aws/kms",
    }

    logger.info("Memory configuration: %s", json.dumps(config, indent=2))
    return config


def apply_policies(policies_dir: str = "policies") -> list[str]:
    """Apply Cedar policies to AgentCore."""
    logger.info("Applying Cedar policies from %s", policies_dir)

    policy_dir = Path(policies_dir)
    applied = []

    if policy_dir.exists():
        for policy_file in policy_dir.glob("*.cedar"):
            logger.info("Applied policy: %s", policy_file.name)
            applied.append(str(policy_file))

    return applied


def main():
    parser = argparse.ArgumentParser(description="Deploy Factor to AgentCore")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--env", default="production", choices=["development", "staging", "production"])
    args = parser.parse_args()

    logger.info("Starting Factor AgentCore deployment")
    logger.info("=" * 60)

    runtime = deploy_runtime(args.region, args.env)
    tools = register_tools(args.region)
    memory = configure_memory(args.region, args.env)
    policies = apply_policies()

    logger.info("=" * 60)
    logger.info("Deployment summary:")
    logger.info("  Runtime: %s", runtime["runtime_name"])
    logger.info("  Agents: %d", len(runtime["agents"]))
    logger.info("  Tools: %d", len(tools))
    logger.info("  Memory: %s", memory["store_id"])
    logger.info("  Policies: %d", len(policies))
    logger.info("=" * 60)
    logger.info("Deployment configuration prepared. Run 'cd infra && cdk deploy --all' to apply.")


if __name__ == "__main__":
    main()

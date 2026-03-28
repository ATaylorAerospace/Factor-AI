# Factor 

## Project Overview
Factor is an agentic AI legal due diligence platform built with AWS Strands Agents SDK and Amazon Bedrock AgentCore. It uses autonomous agents to batch-analyze legal documents for missing provisions, unusual terms, and risk flags.

## Key Architecture
- **Agent Framework:** Strands Agents SDK with `@tool` decorators
- **Foundation Model:** Amazon Bedrock (Anthropic Sonnet)
- **Production Runtime:** Bedrock AgentCore (Runtime, Memory, Gateway, Policy, Observability)
- **Knowledge Base:** ChromaDB + Taylor658/synthetic-legal dataset (ALL SYNTHETIC)
- **API:** FastAPI with SSE streaming
- **Frontend:** React 18 + TypeScript + Vite

## Important Constraints
1. **ALL dataset content is synthetic** — never present as real legal authority
2. **Not legal advice** — Factor is a research/productivity tool
3. **Agent architecture:** Use Strands SDK, not direct API calls

## Commands
```bash
# Tests
pytest tests/ -v --cov=src/factor

# API server
uvicorn src.factor.app:app --reload --port 8000

# Frontend
cd src/frontend && npm install && npm run dev

# Seed knowledge base
python scripts/seed_knowledge_base.py
```

## Code Layout
- `src/factor/agents/` — Strands Agent definitions (coordinator, ingestion, analysis, knowledge, reporting)
- `src/factor/tools/` — `@tool` decorated functions (parsing, chunking, detection, scoring, gaps, comparison, rag, classification, citations, export)
- `src/factor/knowledge/` — ChromaDB vector store and dataset loader
- `src/factor/aws/` — AWS service integrations (Bedrock, AgentCore, S3, Cognito)
- `src/factor/models/` — Pydantic data models
- `src/frontend/` — React dashboard
- `tests/` — pytest test suite
- `infra/` — AWS CDK stacks

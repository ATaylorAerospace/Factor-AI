# ⚖️ Factor AI - Agentic AI Legal Due Diligence Platform 🔍

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://typescriptlang.org)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20AgentCore%20%7C%20Strands-orange.svg)](https://aws.amazon.com/bedrock/)
[![Dataset](https://img.shields.io/badge/Dataset-Taylor658%2Fsynthetic--legal-yellow.svg)](https://huggingface.co/datasets/Taylor658/synthetic-legal)
[![Contact](https://img.shields.io/badge/Contact-Get%20In%20Touch-green.svg)](https://ataylor.getform.com/5w8wz)

**Autonomous AI agents that batch-analyze legal contracts for missing provisions, unusual terms, and risk flags - powered by AWS Strands Agents SDK and Amazon Bedrock AgentCore.**

> 🚧 **Status:** Core agents stable · Dashboard live · AgentCore deployment ready

---

## 🤔 The Problem

M&A and financing due diligence requires reviewing 10–100+ contracts to identify missing clauses, non-standard terms, and cross-document inconsistencies. Manual review is slow, expensive, and error-prone.

---

## 💡 The Solution

Factor AI deploys a system of **autonomous AI agents** that collaboratively analyze batches of legal documents:

- **Ingest** PDFs and DOCX files, extracting and chunking provisions
- **Detect** provision types using pattern matching and AI classification
- **Score** risk levels against configurable rubrics
- **Identify** missing critical clauses via gap analysis
- **Compare** provisions across documents for inconsistencies
- **Generate** structured risk reports with Excel and HTML export

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FACTOR AGENT SYSTEM                   │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │            Coordinator Agent                       │  │
│  │  Receives document batch, plans analysis strategy, │  │
│  │  delegates to specialist agents, assembles report  │  │
│  └──────────┬──────────┬──────────┬─────────────────┘  │
│             │          │          │                      │
│    ┌────────▼──┐ ┌─────▼─────┐ ┌─▼──────────┐         │
│    │ Ingestion │ │ Analysis  │ │ Knowledge  │         │
│    │   Agent   │ │   Agent   │ │   Agent    │         │
│    │ • Parse   │ │ • Detect  │ │ • RAG      │         │
│    │ • Chunk   │ │ • Score   │ │ • Classify │         │
│    │ • Extract │ │ • Gaps    │ │ • Citations│         │
│    └───────────┘ │ • Compare │ └────────────┘         │
│                  └───────────┘                          │
│    ┌─────────────┐                                      │
│    │  Reporting   │                                     │
│    │    Agent     │                                     │
│    │ • Reports   │                                     │
│    │ • Excel     │                                     │
│    │ • HTML      │                                     │
│    └─────────────┘                                      │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Bedrock AgentCore Runtime │ Memory │ Gateway      │  │
│  │  Policy │ Observability │ Identity                 │  │
│  │  Amazon Bedrock (Foundation Models)                │  │
│  │  S3 │ DynamoDB │ CloudWatch │ Cognito              │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent System

| Agent | Role | Tools | Status |
|-------|------|-------|--------|
| 🎯 **Coordinator** | Orchestrates pipeline, delegates tasks, assembles results | `ingest_documents`, `analyze_provisions`, `search_knowledge`, `generate_report` | ✅ Stable |
| 📄 **Ingestion** | Parses PDF/DOCX, chunks into provisions | `parse_pdf`, `parse_docx`, `chunk_provisions` | ✅ Stable |
| 🔍 **Analysis** | Detects types, scores risk, finds gaps, compares | `detect_provision_type`, `score_risk`, `find_gaps`, `compare_across_documents` | ✅ Stable |
| 📚 **Knowledge** | Searches synthetic KB, classifies domains, extracts citations | `search_synthetic_knowledge`, `classify_domain`, `extract_citations` | ✅ Stable |
| 📊 **Reporting** | Builds reports, exports Excel/HTML | `build_risk_report`, `export_excel`, `export_html` | ✅ Stable |

---

## ✨ Core Capabilities

- 🔍 **Provision Detection** - 14 provision types identified via anchor patterns
- 📊 **Risk Scoring** - Configurable rubrics with weighted signals (0–10 scale)
- ⚠️ **Gap Analysis** - Standard checklists for NDAs, leases, loans, mergers, employment, license, and supply agreements
- 🔄 **Cross-Document Comparison** - Inconsistency detection across governing law, liability caps, termination terms
- 📚 **RAG Knowledge Search** - Synthetic legal knowledge base (Taylor658/synthetic-legal)
- 📋 **Structured Reports** - Executive summary, risk assessment, gap analysis, comparison results
- 📥 **Export** - Excel (with disclaimer tab) and HTML (with disclaimers on every page)
- ⚡ **SSE Streaming** - Real-time analysis progress via Server-Sent Events
- 🛡️ **Session Isolation** - Cedar policies enforce per-user data access
- 🔒 **Upload Validation** - File type enforcement (PDF, DOCX, DOC, TXT) with size limits
- 🌐 **Production CORS** - Configurable origin restrictions for production deployments
- 🧹 **Automatic Cleanup** - Uploaded files are removed after analysis completes

---

## 📁 Repository Layout

```
factor/
├── src/factor/              # Python backend
│   ├── agents/              # Strands Agent definitions
│   ├── tools/               # @tool decorated functions
│   ├── knowledge/           # ChromaDB vector store + dataset loader
│   ├── models/              # Pydantic data models
│   ├── aws/                 # Bedrock, AgentCore, S3, Cognito
│   ├── reporting/           # HTML report templates
│   ├── db/                  # Session store (thread-safe)
│   ├── app.py               # FastAPI + SSE streaming
│   └── config.py            # pydantic-settings
├── src/frontend/            # React 18 + TypeScript + Vite
│   └── src/
│       ├── components/      # Upload, Analysis, Report, shared
│       ├── hooks/           # useUpload, useAnalysis, useAgentStream
│       ├── api/             # API client
│       └── types/           # TypeScript types
├── tests/                   # pytest test suite
├── scripts/                 # Seed KB, generate samples, deploy, benchmark
├── policies/                # Cedar policy files
├── data/                    # Provision definitions, risk rubric, samples
├── infra/                   # AWS CDK stacks
└── docker/                  # API + Frontend Dockerfiles, docker-compose
```

---

## 🏁 Getting Started

### Prerequisites

- ✅ Python 3.11+
- ✅ Node.js 20+
- ✅ AWS account with Bedrock access
- ✅ AWS CLI configured (`aws configure`)

### Installation

```bash
# Clone the repository
git clone https://github.com/ATaylorAerospace/Factor-AI.git
cd Factor-AI

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Seed the knowledge base
python scripts/seed_knowledge_base.py

# Start the API server
uvicorn src.factor.app:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev
```

### Run Tests

```bash
pytest tests/ -v --cov=src/factor
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🤖 **Agent Framework** | Strands Agents SDK | Model-driven agents with @tool |
| 🧠 **Foundation Model** | Amazon Bedrock (Anthropic Sonnet) | Reasoning + tool-use |
| ⚡ **Agent Runtime** | Bedrock AgentCore Runtime | Serverless execution |
| 💾 **Agent Memory** | Bedrock AgentCore Memory | Persistent context |
| 🔧 **Agent Gateway** | Bedrock AgentCore Gateway | MCP tool access |
| 🛡️ **Agent Policy** | Bedrock AgentCore Policy (Cedar) | Action boundaries |
| 📊 **Observability** | Bedrock AgentCore + OTEL | Tracing + dashboards |
| 🔐 **Identity** | Bedrock AgentCore Identity / Cognito | Authentication |
| 🔢 **Embeddings** | sentence-transformers | Vector embeddings |
| 📚 **Vector Store** | ChromaDB (local) / Bedrock KB (prod) | Dataset indexing |
| ☁️ **Storage** | Amazon S3 | Document storage |
| 🗄️ **Metadata** | Amazon DynamoDB | Session + results |
| 📄 **Doc Parsing** | PyMuPDF + python-docx + pdfplumber | Text extraction |
| 🖥️ **Frontend** | React 18 + TypeScript + Vite + Tailwind | Dashboard |
| 📋 **Export** | openpyxl + Jinja2 | Reports |
| 🏗️ **IaC** | AWS CDK (Python) | Infrastructure |
| 🔄 **CI/CD** | GitHub Actions | Quality + deploy |

---

## ⚠️ Synthetic Dataset Disclaimer

> **⚠️ CRITICAL: THIS IS A SYNTHETIC DATASET - ALL CONTENT IS ARTIFICIALLY GENERATED**
>
> Factor's knowledge base is powered by the **Taylor658/synthetic-legal** dataset on HuggingFace (140,000 rows, MIT License).
>
> **ALL text in this dataset is synthetically generated and IS NOT legally accurate.** All citations, statutes, case references, legal problems, verified solutions, and pairings are synthetic constructs created through template-based randomization. **No citations, statutes, or case references in this dataset are real.**
>
> This dataset exists for **research, experimentation, and model training only.**

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Upload documents (PDF, DOCX, DOC, TXT) + stream agentic analysis |
| `GET` | `/api/v1/sessions/{id}` | Session status + results |
| `GET` | `/api/v1/sessions/{id}/trace` | Agent reasoning trace |
| `GET` | `/api/v1/reports/{session_id}` | Structured report |
| `GET` | `/api/v1/reports/{session_id}/export` | Download Excel/HTML |
| `GET` | `/api/v1/knowledge/search` | Search synthetic KB |
| `GET` | `/api/v1/knowledge/domains` | List legal domains |
| `GET` | `/api/v1/health` | Health check |

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src/factor

# Run specific test modules
pytest tests/test_tools/ -v          # Tool tests
pytest tests/test_agents/ -v         # Agent tests
pytest tests/test_knowledge/ -v      # Knowledge base tests
```

Tests cover:
- ✅ Each `@tool` function independently with assertions
- ✅ Agent creation with mocked Bedrock responses
- ✅ Synthetic dataset loading and metadata
- ✅ ChromaDB vector store operations
- ✅ Provision detection, scoring, and gap analysis
- ✅ Cross-document comparison and inconsistency detection
- ✅ Domain classification across 13 legal domains
- ✅ Citation extraction (cases, statutes, regulations)
- ✅ Report building, Excel export, and HTML export
- ✅ All outputs label synthetic content

---

## 🚀 Deployment

### Docker

```bash
# Start both API and frontend services
docker compose -f docker/docker-compose.yml up --build
```

### AWS CDK (AgentCore)

```bash
# Deploy infrastructure
cd infra && cdk deploy --all

# Deploy agent configuration
python scripts/deploy_agentcore.py --env production
```

---

## 🙏 Contributing

Contributions are welcome! Please see the [issue templates](.github/ISSUE_TEMPLATE/) for bug reports and feature requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 👤 Author

**A Taylor** · 2026
[![Contact](https://img.shields.io/badge/Contact-Get%20In%20Touch-green.svg)](https://ataylor.getform.com/5w8wz)

---

## 📄 License

MIT © 2026 A Taylor
See [LICENSE](LICENSE) for details.

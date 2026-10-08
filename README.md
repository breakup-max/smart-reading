<p align="center">
  <h1 align="center">Smart Reading · 智阅</h1>
  <p align="center">
    <strong>Production-grade RAG system for PDF document intelligence</strong>
    <br/>
    Hybrid Search + MMR + Cross-Encoder Rerank · Multi-turn conversation · Web UI
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
  <img src="https://img.shields.io/badge/LangChain-1.4+-orange.svg" alt="LangChain"/>
  <img src="https://img.shields.io/badge/LLM-Qwen3--Max-8A2BE2.svg" alt="LLM"/>
</p>

---

## Overview

Smart Reading is a **full-stack RAG (Retrieval-Augmented Generation) application** designed for in-depth document Q&A. It ingests PDF documents, builds a searchable vector index, and answers user questions with **evidence-backed, citable responses** — not just generated text.

Unlike simple "chat-with-your-PDF" demos, this system implements a **three-stage retrieval pipeline** with hybrid search, diversity-aware MMR deduplication, Cross-Encoder LLM reranking, and multi-turn query rewriting. It ships with both a **Web UI** and a **CLI interface**, and is ready for Docker-based deployment.

### What Sets It Apart

| Aspect | Typical Demo | Smart Reading |
|--------|-------------|---------------|
| Retrieval | Single vector similarity | Dense + BM25 hybrid, MMR dedup |
| Reranking | None or TF-IDF | Cross-Encoder LLM with 0–10 scoring |
| Multi-turn | Stateless | Query rewriting with context-aware pronoun resolution |
| Evidence | Answer only | Structured evidence with page/source/score metadata |
| Deployment | `python app.py` | Docker Compose, health check, env-driven config |
| Interface | CLI only | Web UI + CLI dual mode |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ENTRY POINTS                                │
│                   Web UI (FastAPI)  │  CLI (run.py)                  │
└──────────────────┬──────────────────┴────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                                  │
│                                                                      │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────┐          │
│  │ Rewrite  │───▶│    Retrieve       │───▶│    Rerank     │──▶ Gen   │
│  │          │    │  Dense + BM25     │    │  Hybrid Score │          │
│  │ Context- │    │  MMR Dedup        │    │  LLM Judge    │          │
│  │ aware    │    │  Recall K=30      │    │  Top N=4      │          │
│  └──────────┘    └──────────────────┘    └───────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                   │                              │
                   ▼                              ▼
            ┌──────────┐                 ┌──────────────┐
            │ ChromaDB │                 │  Qwen3-Max   │
            │ (Vector) │                 │  (LLM Gen)   │
            └──────────┘                 └──────────────┘
```

### Pipeline Stages

1. **Query Rewrite** — Resolves pronouns, abbreviations, and implicit references across conversation turns using LLM-powered contextual rewriting
2. **Hybrid Retrieval** — Combines dense vector similarity (DashScope `text-embedding-v1`, 1536d) with BM25 keyword matching; applies MMR (Maximal Marginal Relevance) to ensure result diversity
3. **Cross-Encoder Reranking** — Two-phase: (a) hybrid score fusion of vector similarity + Jaccard text overlap with length/keyword heuristics, (b) LLM-based 0–10 relevance judgment on each candidate, retaining only Top-4
4. **Evidence-grounded Generation** — Constructs a structured prompt with numbered evidence blocks including source document and page metadata, then generates the final answer via Qwen3-Max

---

## Features

### Core Capabilities

- **PDF Ingestion** — PyMuPDF-based parsing with `RecursiveCharacterTextSplitter` (paragraph → sentence → token fallback strategy)
- **Three-Stage RAG** — Rewrite → Hybrid Retrieve + MMR → Cross-Encoder LLM Rerank → Generate
- **Multi-Turn Conversation** — Automatic chat history maintenance with context-aware query rewriting
- **Evidence Citation** — Every answer includes structured evidence metadata: content, source file, page number, vector score, hybrid score, and LLM relevance score
- **Configurable Pipeline** — All hyperparameters centralized in a `QaConfig` dataclass; retrieval depth (`recall_k`, `hybrid_top_m`, `top_k`) adjustable per query

### Interface

- **Web UI** — Single-page chat application with PDF upload, conversation history, and evidence expand/collapse
- **CLI** — Interactive terminal mode with file picker dialog and directory-level PDF scanning
- **REST API** — `POST /api/upload`, `POST /api/chat`, `GET /api/health` — ready for integration

### Engineering

- **Session Isolation** — Multiple concurrent PDF sessions via content-hash-based namespacing
- **Persistent Indexing** — ChromaDB backed by local filesystem; index once, query many times
- **Lazy Initialization** — Vector index built on first query, not at startup
- **Docker Support** — `Dockerfile` + `docker-compose.yml` with volume-mounted Chroma persistence
- **Hot Reload** — Uvicorn with `--reload` for development

---

## Quick Start

### Prerequisites

- Python ≥ 3.10
- [DashScope API Key](https://bailian.console.aliyun.com/) (Alibaba Cloud Model Studio)

### Installation

```bash
git clone https://github.com/breakup-max/smart-reading.git
cd smart-reading
pip install -r requirements.txt
```

### Configure API Key

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "sk-your-key"

# Linux / macOS
export DASHSCOPE_API_KEY="sk-your-key"
```

### Launch

**Web UI** (recommended):

```bash
# Windows
start.bat

# Linux / macOS
bash start.sh

# Or manually:
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**, upload a PDF, and start asking questions.

**CLI**:

```bash
python run.py "/path/to/document.pdf"
```

**Docker**:

```bash
cp .env.example .env        # Edit and set DASHSCOPE_API_KEY
docker compose up -d
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | `GET` | Health check; returns `{"status": "ok", "api_key_configured": true}` |
| `/api/upload` | `POST` | Upload PDF (`multipart/form-data`, field: `file`). Returns `file_hash` for subsequent chat. |
| `/api/chat` | `POST` | Send question (`application/json`, fields: `file_hash`, `question`). Returns answer with evidence. |

### Example

```bash
# Upload
curl -F "file=@paper.pdf" http://localhost:8000/api/upload
# → {"file_hash": "a1b2c3...", "message": "索引构建完成"}

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"file_hash": "a1b2c3...", "question": "这篇论文的核心贡献是什么？"}'
# → {"answer": "...", "evidence": [...], "rewritten": true}
```

---

## Configuration

All tunable parameters live in [`config/setting.py`](config/setting.py):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `llm_model` | `qwen3-max` | Qwen model variant for generation & reranking |
| `llm_temperature` | `0.2` | Generation temperature (lower = more deterministic) |
| `embedding_model` | `text-embedding-v1` | DashScope embedding model (1536-dim output) |
| `chunk_size` | `800` | Text chunk size in characters |
| `chunk_overlap` | `120` | Overlap between consecutive chunks |
| `context_max_chars` | `1400` | Max context length fed to the LLM |
| `chroma_root_dir` | `.chroma` | ChromaDB persistence directory |

Per-query retrieval parameters (passed to `RagPipeline.query()`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k` | `4` | Final documents after reranking |
| `recall_k` | `30` | Initial coarse retrieval pool |
| `hybrid_top_m` | `12` | Candidates retained after hybrid reranking |

---

## Project Structure

```
smart-reading/
├── run.py                     # CLI entry point + PDFQA core class
├── start.bat / start.sh       # One-click launch scripts
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Multi-service orchestration
├── .env.example               # Environment variable template
│
├── web/                       # Web application layer
│   ├── app.py                 # FastAPI app, session management
│   ├── schemas.py             # Pydantic request/response models
│   ├── routers/
│   │   ├── upload.py          # POST /api/upload
│   │   └── chat.py            # POST /api/chat
│   └── static/
│       ├── index.html         # Chat UI
│       ├── css/style.css
│       └── js/app.js
│
├── config/
│   └── setting.py             # QaConfig: centralized hyperparameters
│
├── indexing/                  # Offline index construction
│   ├── indexing_pipeline.py   # Orchestrator: ingest → vectorstore
│   ├── ingest.py              # PDF loading + recursive chunking
│   ├── vectorstore.py         # Embedding + ChromaDB storage
│   └── storage.py             # Namespace & persistence management
│
├── querying/                  # Online query pipeline
│   ├── rag_pipeline.py        # Orchestrator: rewrite → retrieve → rerank → generate
│   ├── rewrite.py             # Multi-turn query rewriting
│   ├── vector_retriever.py    # Dense vector recall with scores
│   ├── rerank.py              # Two-phase reranking (hybrid + LLM judge)
│   ├── query_prompt.py        # Prompt templates
│   └── answer.py              # LLM answer generation
│
├── test/                      # Test scripts & experiments
├── requirements.txt
└── .gitignore
```

---

## Technical Deep Dive

### Hybrid Retrieval

The system does **not** rely solely on vector similarity. Instead, it fuses two complementary signals:

- **Dense Vector** — Captures semantic meaning via 1536-dimensional DashScope embeddings
- **BM25 Keyword** — Captures exact term matching, critical for technical terms, abbreviations, and numerical references

The fusion happens in the reranking phase, not at retrieval time, which allows for more nuanced scoring.

### Hybrid Reranking Algorithm

Before LLM judging, candidates pass through a heuristic hybrid scorer:

```
hybrid_score = 0.3 × vector_score + 0.7 × jaccard_overlap_score

Adjustments:
  - len(text) < 80 chars   → × 0.8  (too short = less informative)
  - len(text) > 1600 chars  → × 0.9  (too long = diluted relevance)
  - keyword overlap found   → × 1.1  (reward exact term matches)
```

This balances semantic relevance with lexical precision before the expensive LLM reranking step.

### LLM Cross-Encoder Reranking

Each candidate chunk is individually scored by Qwen3-Max on a 0–10 scale using a structured prompt. The model evaluates **relevance to the query**, not just surface similarity. Only the top-N chunks proceed to answer generation, ensuring the LLM sees the most useful context.

### Evidence Traceability

Every answer is traceable to its source. The API returns:

```json
{
  "answer": "...",
  "evidence": [
    {
      "content": "原文片段...",
      "source": "paper.pdf",
      "page": 3,
      "vector_score": 0.87,
      "hybrid_score": 0.92,
      "llm_score": 9.0
    }
  ],
  "rewritten": true,
  "search_query": "这篇论文的核心贡献..."
}
```

This design makes the system suitable for scenarios requiring **auditability** — academic research, legal document review, compliance checking.

---

## Deployment

### Self-Hosted

```bash
# Set environment variable and start
export DASHSCOPE_API_KEY="sk-your-key"
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
cp .env.example .env   # Configure API key
docker compose up -d    # http://localhost:8000
```

### Cloud Platforms

The application follows the standard ASGI interface and can be deployed to any platform supporting Python web apps (Railway, Render, Hugging Face Spaces, etc.). The startup command is:

```
python -m uvicorn web.app:app --host 0.0.0.0 --port $PORT
```

Only one environment variable is required: `DASHSCOPE_API_KEY`.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `langchain` | RAG orchestration framework |
| `langchain-chroma` | ChromaDB vector store integration |
| `chromadb` | Vector database (local persistence) |
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `python-multipart` | File upload parsing |
| `numpy` | Numerical operations |

---

## Roadmap

- [ ] Streaming (SSE) response for real-time answer generation
- [ ] Multi-file conversation — chat across multiple PDFs simultaneously
- [ ] User authentication & session persistence
- [ ] Kubernetes deployment manifests
- [ ] LangSmith / LangFuse integration for observability
- [ ] Support for `.docx`, `.txt`, and web URL ingestion

---

## License

MIT — see [LICENSE](LICENSE) for details.
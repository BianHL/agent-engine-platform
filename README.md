<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">One-stop AI Agent building, management & orchestration platform.</h4>

<p align="center">
  <a href="docs/i18n/README.zh.md">🇨🇳 中文</a> •
  <a href="docs/i18n/README.ja.md">🇯🇵 日本語</a> •
  <a href="docs/i18n/README.ko.md">🇰🇷 한국어</a> •
  <a href="docs/i18n/README.fr.md">🇫🇷 Français</a> •
  <a href="docs/i18n/README.de.md">🇩🇪 Deutsch</a> •
  <a href="docs/i18n/README.es.md">🇪🇸 Español</a> •
  <a href="docs/i18n/README.pt.md">🇵🇹 Português</a> •
  <a href="docs/i18n/README.ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
  <a href="backend/requirements.txt">
    <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" alt="Python">
  </a>
  <a href="frontend/package.json">
    <img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg" alt="Node">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#engines">Engines</a> •
  <a href="#api">API</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#tech-stack">Tech Stack</a>
</p>

---

## Overview

Agent Engine Platform is a full-stack intelligent agent application engine that provides complete capabilities from Agent creation, knowledge base management, workflow orchestration, multi-agent collaboration to security auditing.

**Backend**: FastAPI + Python 3.11  
**Frontend**: Next.js 14 + React 18 + Ant Design  
**Infrastructure**: Docker Compose orchestration

---

## Features

- 🤖 **Agent Management** - Create, configure & publish intelligent agents with model selection, system prompts, tool binding & knowledge base association
- 🔀 **Multi-Model Routing** - Unified adapter for OpenAI / Anthropic / Ollama with load balancing, circuit breaker & cost tracking
- 📚 **Knowledge Engine** - Complete RAG pipeline with document parsing (PDF/Word/Excel/PPT), smart chunking, vector search (Milvus), full-text search (ES), graph search (Neo4j) & LightRAG dual-level retrieval
- ⚡ **Workflow Engine** - Visual DAG orchestration with LLM nodes, conditional branches, parallel execution, loops, HTTP calls, code sandbox, human approval & sub-workflows
- 🤝 **Multi-Agent Collaboration** - Crew mode (sequential/hierarchical/parallel/consensus) & Handoff routing protocol
- 🔧 **Tool Engine** - Built-in calculator, code executor, DB query, file ops, HTTP requests, web search with custom tool registration
- 🛡️ **Safety Engine** - Input/output security detection covering prompt injection, PII masking & sensitive info filtering
- 📊 **Eval Engine** - Ragas-style RAG quality evaluation (faithfulness/relevancy/precision/recall/tool accuracy)
- 🧠 **Memory System** - Short-term (Redis session history) + Long-term (vectorized storage + topic extraction + summary compression)
- 🔌 **MCP Service** - Expose platform capabilities via Model Context Protocol
- 👥 **Multi-Tenant** - Complete tenant isolation, RBAC permission system, department management & API token management
- 📝 **Audit & Monitoring** - Operation logs, API call auditing, model usage tracking, rate limiting

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- At least 8GB available memory (Milvus + Elasticsearch require more resources)

### 1. Clone & Configure

```bash
git clone <repository-url>
cd agent-engine-platform

# Copy environment variables and modify necessary configurations
cp .env.example .env
# Edit .env, at least set:
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (must change for production)
```

### 2. Start All Services

```bash
# Full startup (all infrastructure + application services)
docker compose --profile full up -d

# Or use external database (only start app + Neo4j)
docker compose --profile external-db up -d
```

### 3. Access

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js Admin UI |
| Backend API | http://localhost:8000 | FastAPI Service |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | Unified Entry |
| Neo4j Browser | http://localhost:7474 | Graph DB Console |

### 4. Local Development (Without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                │
│                   HTTP :80 / HTTPS :443                      │
└──────────┬──────────────────────────────┬───────────────────┘
           │                              │
    ┌──────▼──────┐               ┌───────▼───────┐
    │  Frontend   │               │   Backend     │
    │  Next.js 14 │               │   FastAPI     │
    │  :3000      │               │   :8000       │
    └─────────────┘               └───────┬───────┘
                                          │
                    ┌─────────────────────┬┴──────────────────┐
                    │                     │                    │
             ┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────┐
             │    MySQL    │    │     Redis       │   │   Celery    │
             │   Primary   │    │  Cache/Queue    │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│ Vector  │  │  Full-Text   │ │ Graph   │
└─────────┘  └─────────────┘ └─────────┘
```

### Data Flow

1. **User Request** → Nginx → Frontend (SSR/CSR) or Backend API
2. **Chat Request** → Backend → Safety Engine (Input) → Model Router → LLM → Safety Engine (Output) → SSE Stream
3. **RAG Request** → Knowledge Engine → Parse → Chunk → Embed → Store (Milvus/ES/Neo4j) → Retrieve → Rerank → Generate
4. **Async Tasks** → Backend → Celery Worker (Document processing, model training, scheduled cleanup)
5. **Workflow Execution** → Workflow Engine → DAG Scheduler → Node execution → Human approval → Output

---

## Engines

### Model Engine

Unified LLM adapter layer supporting multiple providers:

| Adapter | Models | Capabilities |
|---------|--------|--------------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama (local) | Chat / Streaming |

Core features: **ModelRouter** (multi-provider load balancing), **CircuitBreaker** (auto fault isolation), **CostTracker** (token usage & cost tracking), **Multimodal** (ASR/TTS/OCR/Vision adapters)

### Knowledge Engine

Complete RAG pipeline from documents to answers:

```
Upload → Parse (PDF/Word/Excel/PPT/TXT) → Smart Chunk → Embedding
    → Store (Milvus + ES + Neo4j) → Retrieve (Vector/Full-Text/Graph/LightRAG) → Rerank → Generate
```

**LightRAG Retrieval Modes:**

| Mode | Description | Use Case |
|------|-------------|----------|
| `naive` | Pure vector similarity | General QA |
| `local` | Entity-focused - extract names to search graph nodes | Precise fact queries |
| `global` | Topic-focused - extract broad concepts to search relationship edges | Macro analysis |
| `hybrid` | local + global weighted RRF fusion | Complex comprehensive queries |

### Workflow Engine

DAG workflow orchestration with node types:

| Node Type | Description |
|-----------|-------------|
| `llm` | LLM call node |
| `condition` | Conditional branch |
| `parallel` | Parallel execution |
| `loop` | Loop execution |
| `http` | HTTP request |
| `code` | Python code sandbox (resource isolated) |
| `human` | Human approval |
| `sub_workflow` | Sub-workflow invocation |

Features: Global timeout control, node-level execution trace, variable snapshots, detailed execution logs.

### Multi-Agent Engine

**Crew Mode**: Multi-agent team collaboration
- Sequential, Hierarchical, Parallel, Consensus

**Handoff Mode**: Structured handoff between agents
- Pydantic-based `HandoffMessage` protocol
- `HandoffTracker` for tracking handoff state & hop count

### Tool Engine

Built-in tools:

| Tool | Function |
|------|----------|
| `calculator` | Math expression calculation |
| `code_executor` | Python code sandbox execution |
| `db_query` | Database query (parameterized) |
| `file_ops` | File read/write operations |
| `http_request` | HTTP requests |
| `web_search` | Web search |

Supports dynamic custom tool registration via `ToolRegistry`.

### Safety Engine

Four-layer security protection:
1. **Prompt Injection Detection** - Regex matching + semantic analysis
2. **PII Masking** - Auto-detection & masking for IDs, phones, emails, bank cards
3. **Sensitive Info Filtering** - Configurable sensitivity levels (low/medium/high)
4. **Compliance Check** - Optional compliance policy toggle

### Memory Engine

- **ShortTermMemory** - Redis-based session history with TTL & max message limits
- **LongTermMemory** - Conversation summary compression + topic extraction + vectorized storage with cross-session retrieval

### Eval Engine

Ragas-style RAG quality evaluation with 5 core metrics:
- `faithfulness` - Answer fidelity to retrieved context
- `answer_relevancy` - Answer relevance to question
- `context_precision` - Retrieval result ranking quality
- `context_recall` - Retrieval coverage of necessary info
- `tool_call_accuracy` - Tool call correctness

---

## API

All API routes prefix: `/api/v1`

| Module | Route | Description |
|--------|-------|-------------|
| Auth | `/auth/*` | Login, register, token refresh |
| Agents | `/agents/*` | Agent CRUD, publish |
| Chat | `/chat/*` | Conversation (SSE streaming) |
| Conversations | `/conversations/*` | Session management |
| Knowledge | `/knowledge/*` | Knowledge base, document upload, retrieval |
| Models | `/models/*` | Model provider configuration |
| Workflows | `/workflows/*` | Workflow CRUD, execution |
| Tools | `/tools/*` | Tool management |
| Multi-Agent | `/multi-agent/*` | Multi-agent orchestration |
| Memory | `/memory/*` | Memory management |
| Evaluations | `/evaluations/*` | RAG evaluation |
| Triggers | `/triggers/*` | Cron / event / webhook triggers |
| Webhooks | `/webhooks/*` | Webhook endpoint management |
| Audit | `/audit/*` | Audit log query |
| Usage | `/usage/*` | Model usage statistics |
| Users | `/users/*` | User management |
| Roles | `/roles/*` | Role permission management |
| Tenants | `/tenants/*` | Tenant management |
| Tokens | `/tokens/*` | API token management |
| Feedbacks | `/feedbacks/*` | User feedback |
| Tasks | `/tasks/*` | Celery task status |

**Health Check**: `GET /health` — Returns database and Redis connection status.

---

## Configuration

All configurations are managed via environment variables. See `.env.example`.

### Production Required Settings

| Config | Description |
|--------|-------------|
| `DB_PASSWORD` | MySQL root password |
| `REDIS_PASSWORD` | Redis authentication password |
| `NEO4J_PASSWORD` | Neo4j authentication password |
| `SECRET_KEY` | JWT signing key (≥16 chars) |
| `ENCRYPTION_KEY` | Data encryption key (≥16 chars) |

### Key Tunable Parameters

| Config | Default | Description |
|--------|---------|-------------|
| `DB_POOL_SIZE` | 10 | Database connection pool size |
| `RATE_LIMIT_PER_MINUTE` | 60 | API rate limit |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery worker concurrency |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | Workflow global timeout (seconds) |
| `MAX_UPLOAD_SIZE_MB` | 50 | File upload size limit (MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | Input security detection toggle |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | Output security detection toggle |

---

## Deployment

### Docker Deployment (Recommended)

```bash
# 1. Configure environment variables
cp .env.example .env
vim .env  # Modify all <PRODUCTION> marked items

# 2. Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Start
docker compose --profile full up -d

# 4. View logs
docker compose logs -f backend
```

### Nginx HTTPS Configuration

Edit `nginx/nginx.conf`, uncomment HTTPS server block, place certificates in `nginx/ssl/`:

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### External Database Mode

If MySQL / Redis / Milvus / ES are provided by external services, configure connection URLs in `.env`, then:

```bash
docker compose --profile external-db up -d
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| Python 3.11 | Runtime |
| FastAPI | Web framework |
| SQLAlchemy 2.0 + aiomysql | Async ORM |
| Pydantic 2.0 | Data validation |
| Celery + Redis | Async task queue |
| Alembic | Database migrations |
| python-jose | JWT authentication |
| httpx | Async HTTP client |
| sse-starlette | SSE streaming response |
| pymilvus | Milvus vector DB client |
| neo4j | Neo4j graph DB driver |
| elasticsearch | ES client |
| minio | Object storage client |

### Frontend

| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework (App Router) |
| React 18 | UI library |
| TypeScript 5 | Type safety |
| Ant Design 5 | UI component library |
| Tailwind CSS 3 | Styling |
| Zustand | State management |
| Axios | HTTP client |
| ECharts | Data visualization |
| React Markdown | Markdown rendering |
| Jest + Testing Library | Testing |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker Compose | Service orchestration |
| MySQL 8.0 | Primary database |
| Redis 7 | Cache + message queue |
| Milvus 2.4 | Vector database |
| Neo4j 5 | Graph database |
| Elasticsearch 8.12 | Full-text search |
| Nginx | Reverse proxy + rate limiting |
| MinIO | Object storage (optional) |

---

## Project Structure

```
agent-engine-platform/
├── backend/                        # Python backend (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # RESTful API routes (20+ modules)
│   │   ├── core/                   # Core infrastructure
│   │   ├── engines/                # Core engine modules
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── tasks/                  # Celery async tasks
│   │   ├── mcp/                    # MCP server
│   │   └── main.py                 # FastAPI app entry
│   ├── tests/                      # Tests (unit / integration)
│   ├── alembic/                    # Database migrations
│   └── Dockerfile
├── frontend/                       # TypeScript frontend (Next.js 14)
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   ├── components/             # React components
│   │   ├── lib/                    # API client
│   │   ├── store/                  # Zustand stores
│   │   └── types/                  # TypeScript types
│   └── Dockerfile
├── nginx/                          # Nginx reverse proxy config
├── scripts/                        # Database init SQL
├── docs/                           # Documentation
├── docker-compose.yml              # All services orchestration
├── .env.example                    # Environment variables template
└── AGENTS.md                       # Automation agent rules
```

---

## Development & Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Database migrations
alembic upgrade head

# Generate migration
alembic revision --autogenerate -m "description"
```

### Frontend Development

```bash
cd frontend

npm install        # Install dependencies
npm run dev        # Start dev server (:3000)
npm run build      # Production build
npm test           # Run tests (Jest)
npm run lint       # ESLint check
```

### Code Standards

| Layer | Standard |
|-------|----------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-space indent |
| Naming | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| Commits | Conventional Commits (`feat(scope): description`) |

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **Repository**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

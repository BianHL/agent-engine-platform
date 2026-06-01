# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack AI Agent platform with a **FastAPI** backend (Python 3.11) and **Next.js 14** frontend. Orchestrated via Docker Compose with MySQL, Redis, Milvus, Neo4j, and Elasticsearch.

## Common Commands

### Backend (`cd backend`)

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server (auto-reload, port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run all tests
pytest

# Run unit tests only
pytest tests/unit -v

# Run integration tests only
pytest tests/integration -v

# Run a single test file
pytest tests/unit/test_safety_engine.py -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend (`cd frontend`)

```bash
npm install          # Install dependencies
npm run dev          # Dev server on :3000
npm run build        # Production build
npm run lint         # ESLint check
npm test             # Run Jest tests
npm test -- --watch  # Watch mode
```

### Docker Compose

```bash
# Full stack (all infra + app)
docker compose --profile full up -d

# External DB mode (app + Neo4j only)
docker compose --profile external-db up -d

# Rebuild after dependency changes
docker compose up -d --build backend frontend

# View logs
docker compose logs -f backend
```

## Architecture

### Backend (`backend/app/`)

- **`api/v1/`** — REST route handlers (28 route files). All routes prefixed with `/api/v1`. Key domains:
  - Core: `agents.py`, `auth.py`, `chat.py`, `conversations.py`, `knowledge.py`, `models.py`, `workflows.py`, `tools.py`
  - Multi-agent: `multi_agent.py`
  - Marketplace: `marketplace.py`, `plugins.py` (not yet wired)
  - Operations: `audit.py`, `usage.py`, `feedbacks.py`, `tasks.py`
  - Organization: `tenants.py`, `users.py`, `roles.py`, `tokens.py`
  - Advanced: `evaluations.py`, `model_compare.py`, `memory.py`, `variables.py`, `triggers.py`, `webhooks.py`, `data_import.py`
  - Draft: `agent_versions.py`, `compliance.py`, `workflow_debug.py` (exist but not wired into router)

- **`core/`** — Infrastructure layer (17 modules):
  - Auth/Security: `auth.py` (JWT + API token deps), `rbac.py`, `security.py` (encryption), `sm_crypto.py` (GM cryptography), `wecom_auth.py` (enterprise WeChat)
  - Data: `database.py` (async SQLAlchemy engine), `redis.py`
  - Middleware: `audit.py` (audit logging), `middleware.py` (request ID), `rate_limiter.py`, `ssrf.py`
  - Observability: `logging.py`, `metrics.py`, `metrics_middleware.py`, `telemetry.py` (OpenTelemetry), `alerting.py`
  - Integration: `webhook_dispatcher.py`, `wecom_notify.py`, `scheduler.py` (APScheduler)
  - Errors: `exceptions.py`

- **`engines/`** — Domain engines, each a self-contained module:
  - `model_engine/` — LLM provider adapters (OpenAI, Anthropic, Ollama, custom OpenAI), router, cost tracker, cache, monitor, presets. Also: embedding (OpenAI), rerank (Cohere), ASR (Whisper), OCR, TTS adapters
  - `knowledge_engine/` — RAG pipeline: document parsers (PDF/Word/Excel/PPT/Web/Text), chunking, reranking, vector/full-text/graph retrieval. Storage: Milvus, Elasticsearch, Neo4j
  - `workflow_engine/` — DAG execution with node types: llm, code, condition, parallel, loop, http, human, sub_workflow. Includes debug mode and debug store
  - `multi_agent/` — Crew modes (sequential/hierarchical/parallel/consensus), Handoff protocol, Plan-and-Execute agent pattern
  - `tool_engine/` — Built-in tools (calculator, code executor, DB query, file ops, HTTP request, text processor, web search) + `ToolRegistry` + `ToolExecutor` with sandboxing
  - `safety_engine/` — Prompt injection detection, PII detection, content filtering
  - `memory_engine/` — Short-term (Redis) + long-term (vector + summary) memory
  - `eval_engine/` — Ragas-style RAG quality metrics, dataset loading/exporting
  - `import_engine/` — Data import from competitor platforms (Dify, Coze) with base importer pattern
  - `plugin_engine/` — Plugin runtime sandbox (stub)

- **`models/`** — SQLAlchemy ORM models (13 files):
  - `base.py` — Declarative base, `generate_uuid`
  - `agent.py` — `AgentModel`, `AgentTagModel`, `AgentVersionModel`
  - `conversation.py` — `ConversationModel`, `MessageModel`, `ConversationVariableModel`, `MessageFeedbackModel`, `MessageAnnotationModel`
  - `knowledge.py` — `KnowledgeBaseModel`, `DocumentModel`, `DocumentSegmentModel`, `ChunkModel`
  - `workflow.py` — `WorkflowModel`, `WorkflowNodeModel`, `WorkflowEdgeModel`, `WorkflowExecutionModel`, `WorkflowVersionModel`
  - `user.py` — `UserModel`, `ApiTokenModel`, `UserRoleModel`, `UserSessionModel`
  - `tenant.py` — `TenantModel`, `DepartmentModel`, `TagModel`, `TagBindingModel`
  - `multi_agent.py` — `CrewModel`, `CrewExecutionModel`, `TaskModel`, `HandoffModel`
  - `marketplace.py` — `MarketplaceItem`, `MarketplaceReviewModel`, `MarketplaceRatingModel`, `MarketplaceCloneModel`, `MarketplaceChangeLogModel`
  - `audit.py` — `OperationLogModel`
  - `system.py` — 25+ system models (roles, permissions, webhooks, triggers, evaluations, tools, providers, configs, usage, etc.)
  - `extended.py` — `AgentVersionModel`, `ABTestModel`, `PluginModel`, `PluginInstallModel`, `PluginRatingModel`, `ComplianceReportModel`

- **`schemas/`** — Pydantic request/response schemas (17 files), mirrors model structure
- **`platform/`** — Business service layer (9 sub-services): agent, conversation, knowledge, marketplace, model, org, task, tenant, workflow
- **`tasks/`** — Celery async tasks: `document_tasks.py`, `marketplace_tasks.py`, `model_tasks.py`, `cleanup_tasks.py`
- **`mcp/`** — Model Context Protocol server: 16 tools, 8 resource templates, stdio transport, HMAC auth
- **`config.py`** — All settings via `pydantic-settings`, loaded from `.env`. Supports WeCom integration, GM crypto backend

### Frontend (`frontend/src/`)

- **`app/`** — Next.js App Router pages:
  - `(auth)/login/` — Login page (unauthenticated)
  - `(platform)/` — Main app (requires auth): ~40 page routes across dashboard, agents, knowledge, models, tools, workflows, conversations, audit, marketplace, evaluations, observability, multi-agent, plugins, compliance, and more
  - `layout.tsx` — Root layout with `ThemeProvider` and `ToastContainer`
  - `page.tsx` — Root redirect (authenticated → `/agents`, else → `/login`)

- **`components/`** — Reusable React components:
  - Root-level: `Sidebar.tsx`, `Header.tsx`, `ChatMessage.tsx`, `CommandPalette.tsx`, `ErrorBoundary.tsx`, `MarkdownRenderer.tsx`, `ThemeProvider.tsx`, `NotificationProvider.tsx`, `LanguageSwitcher.tsx`
  - `ui/` — 16+ design system primitives (Button, Card, Input, Modal, Table, Select, Toast, etc.) with barrel export
  - `workflow/` — Visual workflow editor: `WorkflowCanvas`, `NodeConfigPanel`, `NodePalette`, `Toolbar`, `BaseNode` (8 node types), custom edges
  - `evaluations/` — Eval config, comparison, metrics table, result chart, test question editor
  - `marketplace/` — Tool card, category filter, detail, install dialog, rating, white-box view
  - `observability/` — Alert rules, error analysis, metrics overview, performance charts, request traces, service map
  - `onboarding/` — Onboarding modal, provider, tooltip, progress indicator

- **`hooks/`** — Custom React hooks:
  - `useKeyboardShortcuts.ts` — Global/workflow/chat keyboard shortcuts
  - `usePerformance.ts` — Debounce, throttle, intersection observer, virtual list, deep memo, idle callback, localStorage, sessionStorage
  - `useResponsive.ts` — Responsive breakpoints, media queries, dark mode detection, reduced motion
  - `useTranslation.ts` — i18n hook

- **`lib/`** — Utility libraries:
  - `api.ts` — Axios-based API client with auth token injection, retry logic (exponential backoff), 401 redirect
  - `analytics.ts` — Analytics singleton with event queue, batch flushing, page view/action/performance tracking
  - `cache.ts` — Generic cache class (memory/localStorage/sessionStorage backends with TTL)
  - `errorHandler.ts` — Error class hierarchy (Network, Auth, Authorization, Validation, NotFound, RateLimit, Timeout) with retry and global setup
  - `i18n.ts` — Internationalization: locale detection, nested key resolution, parameter interpolation, plural forms (en-US, zh-CN, ja-JP)
  - `loadingManager.ts` — Zustand-based loading state manager with async operation hooks
  - `theme.ts` — Design token system ("Soft Editorial Warmth"): colors, typography, radius, spacing, motion. Light/dark themes with CSS variables (`--ae-*` prefix)
  - `validation.ts` — Zod-based validation schemas for agents, knowledge bases, workflows, models, tools, users

- **`store/`** — Zustand state stores:
  - `auth.ts` — User auth state, login/logout, token management
  - `chat.ts` — Chat messages, SSE streaming, abort controller
  - `i18n.ts` — Locale state, translation function
  - `workflow-store.ts` — Workflow nodes/edges, selection, execution status, viewport. Uses `zundo` for undo/redo

- **`types/`** — TypeScript type definitions:
  - `index.ts` — Core domain types (User, Agent, KnowledgeBase, Document, ChatMessage, Conversation, Workflow, WorkflowNode, WorkflowEdge, NodeType, etc.)
  - `marketplace.ts` — Marketplace types (MarketplaceItem, Rating, Review, Stats, ToolCategory, etc.)

- **`locales/`** — i18n translation files: `en-US.json`, `zh-CN.json`, `ja-JP.json`
- **`middleware.ts`** — Next.js auth route guard

### Key Patterns

- **Async everywhere**: Backend uses `async/await` with `aiomysql` and `httpx`.
- **Engine isolation**: Each engine in `engines/` is self-contained with its own internal logic; API routes call into engines, not directly into models.
- **Config from env**: All configuration flows through `app/config.py` Settings class. Never hardcode secrets.
- **SSE streaming**: Chat responses use `sse-starlette` for server-sent events.
- **Celery for async work**: Document processing, scheduled tasks, and long-running operations go through Celery workers.
- **Dual-layer theming**: Frontend uses CSS variables (`--ae-*` prefix) + Ant Design ThemeConfig, toggled via `data-theme` attribute.
- **Validation**: Frontend uses Zod schemas (`lib/validation.ts`); backend uses Pydantic models (`schemas/`).
- **Error hierarchy**: Frontend has typed error classes (`lib/errorHandler.ts`); backend has custom exceptions (`core/exceptions.py`).

## Testing

- **Backend**: pytest with `asyncio_mode = auto`. Mark tests with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.slow`. Test paths: `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/performance/`.
- **Frontend**: Jest 30 + `@testing-library/react`. Test behavior, not implementation. Tests in `__tests__/` directories alongside components.
- Tests mirror source layout.

## Conventions

- **Python**: PEP 8, type hints on public functions, `snake_case`/`PascalCase`/`UPPER_SNAKE_CASE`, 4-space indent.
- **TypeScript**: ESLint strict, `PascalCase` components, `camelCase` functions, 2-space indent.
- **Commits**: Conventional Commits — `feat(scope): description` (e.g., `feat(auth): add JWT refresh rotation`).

## Infrastructure Notes

- Docker Compose profiles: `full` (all self-hosted: MySQL + Redis + Milvus + ES + Neo4j) vs `external-db` (app + Neo4j only).
- Services: 11 total — mysql, redis, milvus-standalone, neo4j, elasticsearch, backend, celery-worker, celery-beat, frontend, nginx.
- Neo4j always starts regardless of profile.
- Milvus and ES require significant memory; ensure ≥8GB available for `full` profile.
- Nginx reverse proxy: rate limiting (API 10 req/s, Chat SSE 2 req/s), security headers, SSE proxy with 300s read timeout.
- Health check: `GET /health` returns database + Redis + Milvus + Neo4j + ES status.
- Prometheus metrics: `GET /metrics`.
- Database schema managed via `scripts/init.sql` (mounted into MySQL container); Alembic set up but no migrations committed yet.

## Related Documentation

- `README.md` — Comprehensive project docs (Chinese)
- `DESIGN.md` — Design system specification ("The Well-Typeset Workshop")
- `PRODUCT.md` — Product definition, brand personality, design principles
- `AGENTS.md` — Repository guidelines for AI agents / coding assistants

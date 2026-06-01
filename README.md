# Agent Engine Platform

> 智能体应用引擎平台 —— 一站式 AI Agent 构建、管理与运行平台

Agent Engine Platform 是一个全栈智能体应用引擎平台，提供从 Agent 创建、知识库管理、工作流编排、多 Agent 协作到安全审计的完整能力。后端基于 **FastAPI + Python 3.11**，前端基于 **Next.js 14 + React 18 + Ant Design**，通过 Docker Compose 编排所有基础设施服务。

---

## 目录

- [核心能力](#核心能力)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [引擎模块详解](#引擎模块详解)
- [API 概览](#api-概览)
- [前端页面](#前端页面)
- [基础设施](#基础设施)
- [安全机制](#安全机制)
- [配置说明](#配置说明)
- [开发与测试](#开发与测试)
- [部署指南](#部署指南)
- [技术栈汇总](#技术栈汇总)

---

## 核心能力

- **Agent 管理**：创建、配置、发布智能体，支持模型选择、系统提示词、工具绑定和知识库关联
- **多模型路由**：统一适配 OpenAI / Anthropic / Ollama 等多家 LLM 提供商，支持负载均衡、熔断降级与成本追踪
- **知识库引擎**：完整的 RAG 流水线，支持文档解析（PDF / Word / Excel / PPT / 文本）、智能分块、向量检索（Milvus）、全文检索（Elasticsearch）、图谱检索（Neo4j）以及 LightRAG 双级检索（local / global / hybrid）
- **工作流引擎**：可视化编排 DAG 工作流，支持 LLM 节点、条件分支、并行执行、循环、HTTP 调用、代码沙箱、人工审批与子工作流
- **多 Agent 协作**：支持 Crew 模式（顺序 / 层级 / 并行 / 共识）和 Handoff 路由协议
- **工具引擎**：内置计算器、代码执行器、数据库查询、文件操作、HTTP 请求、网页搜索等工具，支持自定义工具注册
- **安全引擎**：输入输出安全检测，覆盖 Prompt 注入防护、PII 脱敏、敏感信息过滤
- **评估引擎**：Ragas 风格的 RAG 质量评估（faithfulness / relevancy / precision / recall / tool accuracy）
- **记忆系统**：短期记忆（Redis 会话历史）+ 长期记忆（向量化存储 + 主题提取 + 摘要压缩）
- **MCP 服务**：通过 Model Context Protocol 对外暴露平台能力（create_agent / search_knowledge / run_workflow）
- **多租户**：完整的租户隔离、RBAC 权限体系、部门管理与 API Token 管理
- **审计与监控**：操作日志、API 调用审计、模型用量追踪、速率限制

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                       │
│                   HTTP :80 / HTTPS :443                       │
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
             │   主数据库   │    │  缓存/消息队列   │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│ 向量数据库│  │  全文搜索引擎 │ │ 图数据库 │
└─────────┘  └─────────────┘ └─────────┘
```

### 数据流概览

1. **用户请求** → Nginx → Frontend (SSR/CSR) 或 Backend API
2. **Chat 请求** → Backend → Safety Engine (输入检测) → Model Router → LLM Provider → Safety Engine (输出检测) → SSE 流式返回
3. **RAG 请求** → Knowledge Engine → 文档解析 → 分块 → Embedding → Milvus/ES/Neo4j 存储 → 检索 → Rerank → 生成
4. **异步任务** → Backend → Celery Worker (文档处理、模型训练、定时清理)
5. **工作流执行** → Workflow Engine → DAG 调度 → 节点依次/并行执行 → 人工审批 → 结果输出

---

## 项目结构

```
agent-engine-platform/
├── backend/                        # Python 后端 (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # RESTful API 路由 (20+ 模块)
│   │   │   ├── agents.py           # Agent CRUD
│   │   │   ├── auth.py             # 认证 (登录/注册/刷新 Token)
│   │   │   ├── chat.py             # 对话 (SSE 流式)
│   │   │   ├── conversations.py    # 会话管理
│   │   │   ├── knowledge.py        # 知识库与文档
│   │   │   ├── models.py           # 模型提供商管理
│   │   │   ├── workflows.py        # 工作流管理
│   │   │   ├── tools.py            # 工具管理
│   │   │   ├── multi_agent.py      # 多 Agent 编排
│   │   │   ├── evaluations.py      # RAG 评估
│   │   │   ├── audit.py            # 审计日志
│   │   │   ├── triggers.py         # 定时/事件触发器
│   │   │   ├── webhooks.py         # Webhook 管理
│   │   │   └── ...                 # tenants, users, roles, tokens, usage, memory, feedbacks, tasks
│   │   ├── core/                   # 核心基础设施
│   │   │   ├── auth.py             # JWT + API Token 认证依赖
│   │   │   ├── database.py         # SQLAlchemy 异步引擎 & Session
│   │   │   ├── redis.py            # Redis 连接管理
│   │   │   ├── security.py         # Token 编解码 & 加密
│   │   │   ├── middleware.py       # Request ID 中间件
│   │   │   ├── audit.py            # 审计日志中间件
│   │   │   ├── logging.py          # 结构化日志
│   │   │   ├── rate_limiter.py     # 速率限制
│   │   │   ├── rbac.py             # 角色权限控制
│   │   │   ├── scheduler.py        # Cron/事件/webhook 调度器
│   │   │   ├── ssrf.py             # SSRF 防护
│   │   │   ├── exceptions.py       # 统一异常定义
│   │   │   └── webhook_dispatcher.py # Webhook 分发
│   │   ├── engines/                # 核心引擎模块 (详见下方)
│   │   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── schemas/                # Pydantic 请求/响应 Schema
│   │   ├── platform/               # 业务服务层
│   │   ├── tasks/                  # Celery 异步任务
│   │   ├── mcp/                    # MCP (Model Context Protocol) 服务端
│   │   ├── utils/                  # 通用工具
│   │   ├── config.py               # 全局配置 (pydantic-settings)
│   │   └── main.py                 # FastAPI 应用入口
│   ├── tests/                      # 测试 (unit / integration)
│   ├── alembic/                    # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                       # TypeScript 前端 (Next.js 14)
│   ├── src/
│   │   ├── app/                    # App Router 页面
│   │   │   ├── (auth)/login/       # 登录页
│   │   │   ├── (platform)/         # 平台主界面 (需认证)
│   │   │   │   ├── dashboard/      # 仪表盘
│   │   │   │   ├── agents/         # Agent 管理 & 对话
│   │   │   │   ├── knowledge/      # 知识库管理
│   │   │   │   ├── models/         # 模型管理
│   │   │   │   ├── tools/          # 工具管理
│   │   │   │   ├── workflows/      # 工作流管理
│   │   │   │   ├── conversations/  # 会话历史
│   │   │   │   └── audit/          # 审计日志
│   │   │   └── layout.tsx          # 根布局 (Ant Design ConfigProvider)
│   │   ├── components/             # React 组件
│   │   ├── lib/api.ts              # API 客户端 (Axios)
│   │   ├── store/                  # Zustand 状态管理 (auth, chat)
│   │   ├── types/                  # TypeScript 类型定义
│   │   └── middleware.ts           # Next.js 中间件 (认证路由守卫)
│   ├── package.json
│   └── Dockerfile
├── nginx/                          # Nginx 反向代理配置
├── scripts/                        # 数据库初始化 SQL
├── docs/                           # 文档 (部署指南、审计报告)
├── docker-compose.yml              # 所有服务编排
├── .env.example                    # 环境变量模板
└── AGENTS.md                       # 自动化代理规则
```

---

## 快速开始

### 前置条件

- Docker & Docker Compose
- 至少 8GB 可用内存 (Milvus + Elasticsearch 需要较多资源)

### 1. 克隆并配置

```bash
git clone <repository-url>
cd agent-engine-platform

# 复制环境变量并修改必要配置
cp .env.example .env
# 编辑 .env，至少设置以下项：
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (生产环境必须修改)
```

### 2. 启动所有服务

```bash
# 完整启动 (所有基础设施 + 应用服务)
docker compose --profile full up -d

# 或使用外部数据库 (仅启动应用 + Neo4j)
docker compose --profile external-db up -d
```

### 3. 访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Next.js 管理界面 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | 统一入口 |
| Neo4j Browser | http://localhost:7474 | 图数据库控制台 |

### 4. 本地开发 (不使用 Docker)

**后端：**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

---

## 引擎模块详解

### Model Engine (模型引擎)

统一的 LLM 适配层，支持多家提供商：

| 适配器 | 支持模型 | 能力 |
|--------|---------|------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama 等本地模型 | Chat / Streaming |

核心特性：
- **ModelRouter**：多 Provider 负载均衡，支持 Round-Robin 和 Weighted 策略
- **CircuitBreaker**：熔断器模式，自动隔离故障 Provider
- **CostTracker**：Token 用量追踪与成本计算
- **多模态**：ASR (Whisper)、TTS、OCR、Vision 适配器

### Knowledge Engine (知识引擎)

完整的 RAG 流水线，从文档到回答：

```
文档上传 → 解析 (PDF/Word/Excel/PPT/TXT) → 智能分块 → Embedding
    → 向量存储 (Milvus) + 全文索引 (ES) + 图谱构建 (Neo4j)
    → 检索 (向量/全文/图谱/LightRAG) → Rerank → LLM 生成
```

**检索模式 (LightRAG)：**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `naive` | 纯向量相似度 | 通用问答 |
| `local` | 实体聚焦 — 提取具体名称搜索图谱节点 | 精确事实查询 |
| `global` | 主题聚焦 — 提取宽泛概念搜索关系边 | 宏观分析 |
| `hybrid` | local + global 加权 RRF 融合 | 复杂综合查询 |

**知识图谱构建**：LLM 自动提取实体和关系，支持 LLM Profiling（为实体/关系生成可搜索的 KV 属性），支持增量更新（set-union 合并）。

### Workflow Engine (工作流引擎)

DAG 工作流编排，支持以下节点类型：

| 节点类型 | 说明 |
|---------|------|
| `llm` | LLM 调用节点 |
| `condition` | 条件分支 |
| `parallel` | 并行执行 |
| `loop` | 循环执行 |
| `http` | HTTP 请求 |
| `code` | Python 代码沙箱 (资源隔离) |
| `human` | 人工审批 |
| `sub_workflow` | 子工作流调用 |

特性：全局超时控制、节点级执行追踪 (Trace)、变量快照、详细执行日志。

### Multi-Agent Engine (多 Agent 引擎)

**Crew 模式**：多 Agent 团队协作
- Sequential（顺序执行）
- Hierarchical（层级管理，Manager Agent 分配任务）
- Parallel（并行执行 + 结果合并）
- Consensus（共识决策，多 Agent 投票）

**Handoff 模式**：Agent 间结构化交接
- 基于 Pydantic 的 `HandoffMessage` 协议
- `HandoffTracker` 追踪交接状态与跳数

### Tool Engine (工具引擎)

内置工具集：

| 工具 | 功能 |
|------|------|
| `calculator` | 数学表达式计算 |
| `code_executor` | Python 代码沙箱执行 |
| `db_query` | 数据库查询 (参数化) |
| `file_ops` | 文件读写操作 |
| `http_request` | HTTP 请求 |
| `web_search` | 网页搜索 |

支持通过 `ToolRegistry` 动态注册自定义工具，`ToolExecutor` 统一执行并做权限和沙箱隔离。

### Safety Engine (安全引擎)

四层安全防护：
1. **Prompt 注入检测**：正则匹配 + 语义分析，覆盖常见注入模式
2. **PII 脱敏**：身份证、手机号、邮箱、银行卡等自动识别与脱敏（partial / full / hash）
3. **敏感信息过滤**：可配置敏感度等级（low / medium / high）
4. **合规检查**：可选的合规策略开关

### Memory Engine (记忆引擎)

- **ShortTermMemory**：基于 Redis 的会话历史，支持 TTL 和最大消息数限制
- **LongTermMemory**：对话摘要压缩 + 主题提取 + 向量化存储，支持跨会话检索

### Eval Engine (评估引擎)

Ragas 风格的 RAG 质量评估，5 个核心指标：
- `faithfulness`：回答是否忠于检索到的上下文
- `answer_relevancy`：回答与问题的相关性
- `context_precision`：检索结果的排序质量
- `context_recall`：检索是否覆盖所有必要信息
- `tool_call_accuracy`：工具调用的正确性

---

## API 概览

所有 API 路由前缀：`/api/v1`

| 模块 | 路由 | 说明 |
|------|------|------|
| Auth | `/auth/*` | 登录、注册、Token 刷新 |
| Agents | `/agents/*` | Agent CRUD、发布 |
| Chat | `/chat/*` | 对话 (SSE 流式) |
| Conversations | `/conversations/*` | 会话管理 |
| Knowledge | `/knowledge/*` | 知识库、文档上传、检索 |
| Models | `/models/*` | 模型提供商配置 |
| Workflows | `/workflows/*` | 工作流 CRUD、执行 |
| Tools | `/tools/*` | 工具管理 |
| Multi-Agent | `/multi-agent/*` | 多 Agent 编排 |
| Memory | `/memory/*` | 记忆管理 |
| Evaluations | `/evaluations/*` | RAG 评估 |
| Triggers | `/triggers/*` | Cron / 事件 / Webhook 触发器 |
| Webhooks | `/webhooks/*` | Webhook 端点管理 |
| Audit | `/audit/*` | 审计日志查询 |
| Usage | `/usage/*` | 模型用量统计 |
| Users | `/users/*` | 用户管理 |
| Roles | `/roles/*` | 角色权限管理 |
| Tenants | `/tenants/*` | 租户管理 |
| Tokens | `/tokens/*` | API Token 管理 |
| Feedbacks | `/feedbacks/*` | 用户反馈 |
| Tasks | `/tasks/*` | Celery 任务状态 |

**健康检查**：`GET /health` — 返回数据库和 Redis 连接状态。

---

## 前端页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 登录 | `/login` | JWT 认证，支持重定向 |
| 仪表盘 | `/dashboard` | 数据概览，ECharts 图表 |
| Agent 列表 | `/agents` | 创建、编辑、发布 Agent |
| Agent 详情 | `/agents/[id]` | 配置详情、工具/知识库绑定 |
| Agent 对话 | `/agents/[id]/chat` | SSE 流式对话界面 |
| 知识库 | `/knowledge` | 知识库管理、文档上传 |
| 知识库详情 | `/knowledge/[id]` | 文档列表、检索测试 |
| 模型管理 | `/models` | Provider 配置、模型启用/禁用 |
| 工具管理 | `/tools` | 工具列表、参数配置 |
| 工作流 | `/workflows` | 工作流列表、创建 |
| 工作流详情 | `/workflows/[id]` | DAG 编辑器、执行记录 |
| 会话历史 | `/conversations` | 历史会话列表与回顾 |
| 审计日志 | `/audit` | 操作记录查询 |

**技术栈**：Next.js 14 (App Router) + React 18 + Ant Design 5 + Tailwind CSS + Zustand + ECharts + React Markdown

---

## 基础设施

### Docker Compose 服务

| 服务 | 镜像 | Profile | 端口 | 说明 |
|------|------|---------|------|------|
| `mysql` | mysql:8.0 | `full` | 3306 | 主数据库 (InnoDB, utf8mb4) |
| `redis` | redis:7-alpine | `full` | 6379 | 缓存 + Celery Broker |
| `milvus-standalone` | milvusdb/milvus:v2.4 | `full` | 19530 | 向量数据库 |
| `elasticsearch` | elasticsearch:8.12.0 | `full` | 9200 | 全文搜索引擎 |
| `neo4j` | neo4j:5-community | 始终运行 | 7474, 7687 | 图数据库 |
| `backend` | 自建 (Python 3.11) | 始终运行 | 8000 | FastAPI 应用 |
| `celery-worker` | 同 backend | 始终运行 | - | Celery Worker (并发 4) |
| `celery-beat` | 同 backend | 始终运行 | - | Celery 定时任务 |
| `frontend` | 自建 (Node 20) | 始终运行 | 3000 | Next.js 应用 |
| `nginx` | nginx:alpine | 始终运行 | 80, 443 | 反向代理 + 限流 |

### Profile 模式

- **`full`**：所有基础设施自托管（MySQL + Redis + Milvus + ES + Neo4j + 应用服务）
- **`external-db`**：仅启动应用服务 + Neo4j，MySQL / Redis / Milvus / ES 由外部提供

---

## 安全机制

| 层面 | 实现 |
|------|------|
| **认证** | JWT Bearer Token + API Token 双通道，支持 Refresh Token |
| **授权** | RBAC 角色权限体系 (admin / manager / user)，租户隔离 |
| **传输安全** | HTTPS Redirect 中间件，可配置 TLS 证书 |
| **输入安全** | Prompt 注入检测、SQL 参数化、SSRF 防护 |
| **输出安全** | PII 脱敏、敏感信息过滤、合规检查 |
| **限流** | API 级速率限制 (60 req/min)、登录限制 (5 次/60s)、Nginx 层限流 |
| **审计** | 全操作审计日志 (who / when / what / before / after) |
| **CORS** | 可配置源、方法、头部白名单 |
| **代码沙箱** | 工作流代码节点资源隔离 (超时 + 内存限制 + 输出限制) |

---

## 配置说明

所有配置通过环境变量管理，参考 `.env.example`。

### 生产环境必须修改的配置

| 配置项 | 说明 |
|--------|------|
| `DB_PASSWORD` | MySQL root 密码 |
| `REDIS_PASSWORD` | Redis 认证密码 |
| `NEO4J_PASSWORD` | Neo4j 认证密码 |
| `SECRET_KEY` | JWT 签名密钥 (≥16 字符) |
| `ENCRYPTION_KEY` | 数据加密密钥 (≥16 字符) |

### 关键可调参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DB_POOL_SIZE` | 10 | 数据库连接池大小 |
| `RATE_LIMIT_PER_MINUTE` | 60 | API 速率限制 |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery Worker 并发数 |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | 工作流全局超时 (秒) |
| `MAX_UPLOAD_SIZE_MB` | 50 | 文件上传大小限制 (MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | 输入安全检测开关 |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | 输出安全检测开关 |

---

## 开发与测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 数据库迁移
alembic upgrade head

# 生成迁移
alembic revision --autogenerate -m "description"
```

### 前端开发

```bash
cd frontend

npm install        # 安装依赖
npm run dev        # 启动开发服务器 (:3000)
npm run build      # 生产构建
npm test           # 运行测试 (Jest)
npm run lint       # ESLint 检查
```

### 代码规范

| 层面 | 规范 |
|------|------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-space indent |
| 命名 | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| 提交 | Conventional Commits (`feat(scope): description`) |

---

## 部署指南

### Docker 部署 (推荐)

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 修改所有 <PRODUCTION> 标记项

# 2. 生成安全密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 启动
docker compose --profile full up -d

# 4. 查看日志
docker compose logs -f backend
```

### Nginx HTTPS 配置

编辑 `nginx/nginx.conf`，取消 HTTPS server block 注释，将证书放入 `nginx/ssl/` 目录：

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### 外部数据库模式

如果 MySQL / Redis / Milvus / ES 由外部服务提供，在 `.env` 中配置对应的连接 URL，然后：

```bash
docker compose --profile external-db up -d
```

---

## 技术栈汇总

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.11 | 运行时 |
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 + aiomysql | 异步 ORM |
| Pydantic 2.0 | 数据校验 |
| Celery + Redis | 异步任务队列 |
| Alembic | 数据库迁移 |
| python-jose | JWT 认证 |
| httpx | 异步 HTTP 客户端 |
| sse-starlette | SSE 流式响应 |
| pymilvus | Milvus 向量数据库客户端 |
| neo4j | Neo4j 图数据库驱动 |
| elasticsearch | ES 客户端 |
| minio | 对象存储客户端 |

### 前端

| 技术 | 用途 |
|------|------|
| Next.js 14 | React 框架 (App Router) |
| React 18 | UI 库 |
| TypeScript 5 | 类型安全 |
| Ant Design 5 | UI 组件库 |
| Tailwind CSS 3 | 样式 |
| Zustand | 状态管理 |
| Axios | HTTP 客户端 |
| ECharts | 数据可视化 |
| React Markdown | Markdown 渲染 |
| Jest + Testing Library | 测试 |

### 基础设施

| 技术 | 用途 |
|------|------|
| Docker Compose | 服务编排 |
| MySQL 8.0 | 主数据库 |
| Redis 7 | 缓存 + 消息队列 |
| Milvus 2.4 | 向量数据库 |
| Neo4j 5 | 图数据库 |
| Elasticsearch 8.12 | 全文搜索 |
| Nginx | 反向代理 + 限流 |
| MinIO | 对象存储 (可选) |

---

## License

Private / Proprietary

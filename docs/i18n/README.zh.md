<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">一站式 AI Agent 构建、管理与编排平台。</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.de.md">🇩🇪 Deutsch</a> •
  <a href="README.es.md">🇪🇸 Español</a> •
  <a href="README.pt.md">🇵🇹 Português</a> •
  <a href="README.ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <a href="../../LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
  <a href="../../backend/requirements.txt">
    <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" alt="Python">
  </a>
  <a href="../../frontend/package.json">
    <img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg" alt="Node">
  </a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#核心能力">核心能力</a> •
  <a href="#系统架构">系统架构</a> •
  <a href="#引擎模块">引擎模块</a> •
  <a href="#api-概览">API</a> •
  <a href="#配置说明">配置</a> •
  <a href="#部署指南">部署</a> •
  <a href="#技术栈">技术栈</a>
</p>

---

## 概述

Agent Engine Platform 是一个全栈智能体应用引擎平台，提供从 Agent 创建、知识库管理、工作流编排、多 Agent 协作到安全审计的完整能力。

**后端**：FastAPI + Python 3.11  
**前端**：Next.js 14 + React 18 + Ant Design  
**基础设施**：Docker Compose 编排

---

## 核心能力

- 🤖 **Agent 管理** - 创建、配置、发布智能体，支持模型选择、系统提示词、工具绑定和知识库关联
- 🔀 **多模型路由** - 统一适配 OpenAI / Anthropic / Ollama 等多家 LLM 提供商，支持负载均衡、熔断降级与成本追踪
- 📚 **知识引擎** - 完整的 RAG 流水线，支持文档解析（PDF/Word/Excel/PPT）、智能分块、向量检索（Milvus）、全文检索（ES）、图谱检索（Neo4j）以及 LightRAG 双级检索
- ⚡ **工作流引擎** - 可视化 DAG 编排，支持 LLM 节点、条件分支、并行执行、循环、HTTP 调用、代码沙箱、人工审批与子工作流
- 🤝 **多 Agent 协作** - Crew 模式（顺序/层级/并行/共识）与 Handoff 路由协议
- 🔧 **工具引擎** - 内置计算器、代码执行器、数据库查询、文件操作、HTTP 请求、网页搜索，支持自定义工具注册
- 🛡️ **安全引擎** - 输入输出安全检测，覆盖 Prompt 注入防护、PII 脱敏、敏感信息过滤
- 📊 **评估引擎** - Ragas 风格 RAG 质量评估（faithfulness/relevancy/precision/recall/tool accuracy）
- 🧠 **记忆系统** - 短期记忆（Redis 会话历史）+ 长期记忆（向量化存储 + 主题提取 + 摘要压缩）
- 🔌 **MCP 服务** - 通过 Model Context Protocol 对外暴露平台能力
- 👥 **多租户** - 完整的租户隔离、RBAC 权限体系、部门管理与 API Token 管理
- 📝 **审计与监控** - 操作日志、API 调用审计、模型用量追踪、速率限制

---

## 快速开始

### 前置条件

- Docker & Docker Compose
- 至少 8GB 可用内存（Milvus + Elasticsearch 需要较多资源）

### 1. 克隆并配置

```bash
git clone <repository-url>
cd agent-engine-platform

# 复制环境变量并修改必要配置
cp .env.example .env
# 编辑 .env，至少设置以下项：
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY（生产环境必须修改）
```

### 2. 启动所有服务

```bash
# 完整启动（所有基础设施 + 应用服务）
docker-compose --profile full up -d

# 或使用外部数据库（仅启动应用 + Neo4j）
docker-compose --profile external-db up -d
```

### 3. 访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Next.js 管理界面 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | 统一入口 |
| Neo4j Browser | http://localhost:7474 | 图数据库控制台 |

### 4. 本地开发（不使用 Docker）

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

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx（反向代理）                      │
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

### 数据流

1. **用户请求** → Nginx → Frontend（SSR/CSR）或 Backend API
2. **对话请求** → Backend → 安全引擎（输入检测）→ 模型路由 → LLM → 安全引擎（输出检测）→ SSE 流式返回
3. **RAG 请求** → 知识引擎 → 文档解析 → 分块 → Embedding → 存储（Milvus/ES/Neo4j）→ 检索 → Rerank → 生成
4. **异步任务** → Backend → Celery Worker（文档处理、模型训练、定时清理）
5. **工作流执行** → 工作流引擎 → DAG 调度 → 节点执行 → 人工审批 → 结果输出

---

## 引擎模块

### 模型引擎

统一的 LLM 适配层，支持多家提供商：

| 适配器 | 支持模型 | 能力 |
|--------|---------|------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama（本地模型） | Chat / Streaming |

核心特性：**ModelRouter**（多 Provider 负载均衡）、**CircuitBreaker**（熔断器模式）、**CostTracker**（Token 用量追踪与成本计算）、**多模态**（ASR/TTS/OCR/Vision 适配器）

### 知识引擎

完整的 RAG 流水线，从文档到回答：

```
文档上传 → 解析（PDF/Word/Excel/PPT/TXT）→ 智能分块 → Embedding
    → 存储（Milvus + ES + Neo4j）→ 检索（向量/全文/图谱/LightRAG）→ Rerank → 生成
```

**LightRAG 检索模式：**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `naive` | 纯向量相似度 | 通用问答 |
| `local` | 实体聚焦 — 提取具体名称搜索图谱节点 | 精确事实查询 |
| `global` | 主题聚焦 — 提取宽泛概念搜索关系边 | 宏观分析 |
| `hybrid` | local + global 加权 RRF 融合 | 复杂综合查询 |

### 工作流引擎

DAG 工作流编排，支持以下节点类型：

| 节点类型 | 说明 |
|---------|------|
| `llm` | LLM 调用节点 |
| `condition` | 条件分支 |
| `parallel` | 并行执行 |
| `loop` | 循环执行 |
| `http` | HTTP 请求 |
| `code` | Python 代码沙箱（资源隔离） |
| `human` | 人工审批 |
| `sub_workflow` | 子工作流调用 |

特性：全局超时控制、节点级执行追踪、变量快照、详细执行日志。

### 多 Agent 引擎

**Crew 模式**：多 Agent 团队协作
- Sequential（顺序执行）、Hierarchical（层级管理）、Parallel（并行执行）、Consensus（共识决策）

**Handoff 模式**：Agent 间结构化交接
- 基于 Pydantic 的 `HandoffMessage` 协议
- `HandoffTracker` 追踪交接状态与跳数

### 工具引擎

内置工具集：

| 工具 | 功能 |
|------|------|
| `calculator` | 数学表达式计算 |
| `code_executor` | Python 代码沙箱执行 |
| `db_query` | 数据库查询（参数化） |
| `file_ops` | 文件读写操作 |
| `http_request` | HTTP 请求 |
| `web_search` | 网页搜索 |

支持通过 `ToolRegistry` 动态注册自定义工具。

### 安全引擎

四层安全防护：
1. **Prompt 注入检测** - 正则匹配 + 语义分析
2. **PII 脱敏** - 身份证、手机号、邮箱、银行卡等自动识别与脱敏
3. **敏感信息过滤** - 可配置敏感度等级（low/medium/high）
4. **合规检查** - 可选的合规策略开关

### 记忆引擎

- **ShortTermMemory** - 基于 Redis 的会话历史，支持 TTL 和最大消息数限制
- **LongTermMemory** - 对话摘要压缩 + 主题提取 + 向量化存储，支持跨会话检索

### 评估引擎

Ragas 风格 RAG 质量评估，5 个核心指标：
- `faithfulness` - 回答是否忠于检索到的上下文
- `answer_relevancy` - 回答与问题的相关性
- `context_precision` - 检索结果的排序质量
- `context_recall` - 检索是否覆盖所有必要信息
- `tool_call_accuracy` - 工具调用的正确性

---

## API 概览

所有 API 路由前缀：`/api/v1`

| 模块 | 路由 | 说明 |
|------|------|------|
| Auth | `/auth/*` | 登录、注册、Token 刷新 |
| Agents | `/agents/*` | Agent CRUD、发布 |
| Chat | `/chat/*` | 对话（SSE 流式） |
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

## 配置说明

所有配置通过环境变量管理，参考 `.env.example`。

### 生产环境必须修改的配置

| 配置项 | 说明 |
|--------|------|
| `DB_PASSWORD` | MySQL root 密码 |
| `REDIS_PASSWORD` | Redis 认证密码 |
| `NEO4J_PASSWORD` | Neo4j 认证密码 |
| `SECRET_KEY` | JWT 签名密钥（≥16 字符） |
| `ENCRYPTION_KEY` | 数据加密密钥（≥16 字符） |

### 关键可调参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DB_POOL_SIZE` | 10 | 数据库连接池大小 |
| `RATE_LIMIT_PER_MINUTE` | 60 | API 速率限制 |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery Worker 并发数 |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | 工作流全局超时（秒） |
| `MAX_UPLOAD_SIZE_MB` | 50 | 文件上传大小限制（MB） |
| `SAFETY_INPUT_CHECK_ENABLED` | true | 输入安全检测开关 |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | 输出安全检测开关 |

---

## 部署指南

### Docker 部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 修改所有 <PRODUCTION> 标记项

# 2. 生成安全密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 启动
docker-compose --profile full up -d

# 4. 查看日志
docker-compose logs -f backend
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
docker-compose --profile external-db up -d
```

---

## 技术栈

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
| Next.js 14 | React 框架（App Router） |
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
| MinIO | 对象存储（可选） |

---

## 项目结构

```
agent-engine-platform/
├── backend/                        # Python 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/                 # RESTful API 路由（20+ 模块）
│   │   ├── core/                   # 核心基础设施
│   │   ├── engines/                # 核心引擎模块
│   │   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── schemas/                # Pydantic 请求/响应 Schema
│   │   ├── tasks/                  # Celery 异步任务
│   │   ├── mcp/                    # MCP 服务端
│   │   └── main.py                 # FastAPI 应用入口
│   ├── tests/                      # 测试（unit / integration）
│   ├── alembic/                    # 数据库迁移
│   └── Dockerfile
├── frontend/                       # TypeScript 前端（Next.js 14）
│   ├── src/
│   │   ├── app/                    # App Router 页面
│   │   ├── components/             # React 组件
│   │   ├── lib/                    # API 客户端
│   │   ├── store/                  # Zustand 状态管理
│   │   └── types/                  # TypeScript 类型定义
│   └── Dockerfile
├── nginx/                          # Nginx 反向代理配置
├── scripts/                        # 数据库初始化 SQL
├── docs/                           # 文档
├── docker-compose.yml              # 所有服务编排
├── .env.example                    # 环境变量模板
└── AGENTS.md                       # 自动化代理规则
```

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
npm run dev        # 启动开发服务器（:3000）
npm run build      # 生产构建
npm test           # 运行测试（Jest）
npm run lint       # ESLint 检查
```

### 代码规范

| 层面 | 规范 |
|------|------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-space indent |
| 命名 | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| 提交 | Conventional Commits（`feat(scope): description`） |

---

## License

本项目基于 Apache License 2.0 开源 - 详见 [LICENSE](../../LICENSE) 文件。

---

## 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 支持

- **文档**: [docs/](../../docs/)
- **问题反馈**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **仓库**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

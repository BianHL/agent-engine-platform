# Agent Engine Platform 深度审核报告

**日期**: 2026-05-27
**审核范围**: 框架层 + 能力层 + 业务层 + 竞品横向对比
**审核基线**: 137 项验收标准 (全部 VERIFIED)、602 测试通过

---

## 一、总体评估

平台是一个多租户 AI Agent 管理系统，后端 FastAPI + 前端 Next.js 14，Docker Compose 编排 9 个基础设施服务。代码结构清晰，验收标准覆盖完整。

**核心发现**:

| 严重级别 | 数量 | 关键领域 |
|----------|------|----------|
| CRITICAL | 14 | 安全沙箱逃逸、注入攻击、凭证管理、数据隔离 |
| HIGH | 36 | 架构缺陷、资源泄漏、生产就绪性不足 |
| MEDIUM | 12 | 代码质量、UI/UX、可维护性 |

---

## 二、框架层审核

### CRITICAL 级别

#### [FW-C01] 登录端点无限流 — 暴力破解风险
**文件**: `backend/app/api/v1/auth.py:21-37`
`/auth/login` 无任何速率限制。`rate_limit_dependency` 存在但从未应用到任何端点。
**修复**: 对登录端点施加 IP 级别速率限制（如 5次/分钟），加入账户锁定机制。

#### [FW-C02] SSRF 防护存在 DNS 重绑定 / TOCTOU 漏洞
**文件**: `backend/app/core/ssrf.py:27-58`
`is_safe_url()` 解析 DNS 并检查 IP，但实际 HTTP 请求在此之后发生。攻击者可在检查期间将 DNS 指向安全 IP，请求时切换为内网 IP。
**修复**: 使用自定义 DNS 解析器，检查时 pin 住 IP，后续请求直接连接该 IP。

#### [FW-C03] JWT sub 字段无类型验证 — 潜在类型混淆
**文件**: `backend/app/core/auth.py:33`
`payload.get("sub")` 未验证类型。`sub=0` 或 `sub={}` 时会静默回退到 API Token 路径。
**修复**: 添加 `isinstance(user_id, str) and user_id` 检查。

#### [FW-C04] bcrypt 异常导致用户枚举
**文件**: `backend/app/core/security.py:14-18`
`bcrypt.checkpw` 对畸形 hash 抛 `ValueError`，导致 500 vs 401 差异。攻击者可区分"用户存在"和"用户不存在"。
**修复**: 用 try/except 包裹 `verify_password`，捕获 `ValueError` 返回 `False`。

### HIGH 级别

#### [FW-H01] 审计日志完全不工作
**文件**: `backend/app/core/audit.py:90-91`
`request.state.user_id` 和 `request.state.tenant_id` 从未被设置。`get_current_user` 返回 dict 但不填充 `request.state`。所有审计日志 `user_id=None, tenant_id=None`，条件 `if tenant_id:` 永远不满足。
**修复**: 在 `get_current_user` 中设置 `request.state.user_id` 和 `request.state.tenant_id`。

#### [FW-H02] get_db 每次 commit — 隐式提交行为
**文件**: `backend/app/core/database.py:18-25`
每次请求都 commit（包括 GET）。`HTTPException` 被捕获为 Exception 导致 rollback，可能丢失已执行的写操作。
**修复**: 检查 `session.dirty`/`session.new` 再 commit；单独处理 `HTTPException`。

#### [FW-H03] Chat SSE 中 DB Session 生命周期问题
**文件**: `backend/app/api/v1/chat.py:188-192`
`get_db` 的 async generator 在 endpoint 返回 `EventSourceResponse` 后 commit/close session，但 `event_generator` 在此之后仍在运行。
**修复**: 在 generator 内部创建独立 session，或用 background task 处理 DB 写入。

#### [FW-H04] 加密密钥派生非标准 + 无密钥版本管理
**文件**: `backend/app/core/security.py:41-43`
SHA-256 哈希后取前 32 字节（实际是 no-op），每次调用创建新 Fernet 实例。密钥轮换无支持。
**修复**: 缓存派生密钥为模块级单例；实现密钥版本管理。

#### [FW-H05] Rate limiter 重复解码 JWT
**文件**: `backend/app/core/rate_limiter.py:83-92`
每次限流检查都重新解码 JWT，CPU 开销翻倍。且与 `auth.py` 的解码逻辑不同步。
**修复**: 从已认证的 `request.state` 获取 `tenant_id`。

#### [FW-H06] Redis 连接关闭未注册
**文件**: `backend/app/main.py:71-76`
`shutdown_tasks` 未调用 `close_redis()`，导致资源泄漏。
**修复**: 添加 `await close_redis()` 到 shutdown。

#### [FW-H07] DB 连接池硬编码 — 多 worker 连接爆炸
**文件**: `backend/app/core/database.py:4-9`
`pool_size=20, max_overflow=10` 硬编码。4 worker = 120 连接。无 `pool_recycle`/`pool_pre_ping`。
**修复**: 通过 Settings 配置化；添加 `pool_recycle=3600, pool_pre_ping=True`。

#### [FW-H08] Scheduler 单例线程安全问题
**文件**: `backend/app/core/scheduler.py:106-121`
`__new__` + `_initialized` flag 非线程安全。`_cron_triggers`/`_event_triggers` 无同步保护。

#### [FW-H09] Cron 时间计算 bug
**文件**: `backend/app/core/scheduler.py:70-95`
手动递增分钟，`day=dt.day + 1` 可产生非法日期（如 32 日）。
**修复**: 使用 `timedelta(minutes=1)`。

#### [FW-H10] 928 行单文件 ORM — 40+ 模型类
**文件**: `backend/app/models/base.py`
违反分离原则。应拆分为 `models/user.py`、`models/agent.py` 等。

#### [FW-H11] 关键列缺少唯一约束
`UserModel(tenant_id, username)`、`RoleModel(tenant_id, name)`、`RolePermissionModel(role_id, permission_id)` 等缺少 UniqueConstraint。并发创建可能产生重复数据。

#### [FW-H12] 所有 datetime 默认值剥离时区
`datetime.now(UTC).replace(tzinfo=None)` 创建 naive datetime。MySQL 非 UTC 时区时比较会出错。

#### [FW-H13] 文件上传内存耗尽
**文件**: `backend/app/api/v1/knowledge.py:112-115`
整个文件读入内存后才检查大小。100MB 文件 = 100MB 内存分配。
**修复**: 流式读取 + 分块大小检查。

#### [FW-H14] 无全局异常处理器
`core/exceptions.py` 定义的自定义异常（`ModelNotFoundError`、`RateLimitExceededError`）未注册到 FastAPI，触发时返回裸 500。

#### [FW-H15] API response_model 未强制执行
多数端点返回裸 dict，未使用 `response_model` 参数。OpenAPI 文档不完整，可能泄露额外字段。

#### [FW-H16] Triggers API 无权限检查
**文件**: `backend/app/api/v1/triggers.py:23-43`
所有 trigger 端点仅用 `get_current_user`，无 `require_permission`。任何认证用户可创建/修改触发器。

#### [FW-H17] update_user 角色无验证
**文件**: `backend/app/api/v1/users.py:145-146`
`update_user` 接受任意字符串作为 role，可设为不存在的角色绕过 RBAC。

#### [FW-H18] CORS 允许所有方法和头
**文件**: `backend/app/main.py:50-53`
`allow_methods=["*"], allow_headers=["*"]` 过于宽松。

#### [FW-H19] 健康检查每次创建新 Redis 连接
**文件**: `backend/app/main.py:95-100`
未复用共享 `get_redis()` 单例。

---

## 三、能力层审核（6 大引擎）

### Model Engine

#### [ME-C01] LLM Adapter 无重试 — 一次 429 即触发熔断
**文件**: `backend/app/engines/model_engine/llm/openai.py:15-35`
所有 adapter 直接 `raise_for_status()`，无 retry/backoff。一次 429 就增加 circuit breaker failure count。
**修复**: adapter 层加入 tenacity（仅对 429/500/502/503 重试）。

#### [ME-H01] 每次 chat 创建新 httpx.AsyncClient
**文件**: `openai.py:15, anthropic.py:23`
阻止连接池复用，高并发下大量 TCP 握手。
**修复**: `__init__` 创建长生命周期 client，shutdown hook 关闭。

#### [ME-H02] CostTracker 价格单位不明确
**文件**: `backend/app/engines/model_engine/cost_tracker.py:26`
除以 1000 假设 per-1K，但 GPT-4o 的 `input_price=2.5` 可能是 per-1M。计费差 1000 倍。

#### [ME-H03] ModelMonitor 内存指标无持久化、无多实例共享
进程重启丢失；多 worker 各自独立，无法聚合。

### Knowledge Engine

#### [KE-C01] Neo4j merge_node 中 key 参数未校验 — Cypher 注入
**文件**: `backend/app/engines/knowledge_engine/storage/graph/neo4j_store.py:59-60`
`merge_node` 将用户提供的 `key` 直接拼入 Cypher。`_validate_label` 只检查 label，不检查 key。
**修复**: 对所有动态标识符严格正则白名单校验 `^[A-Za-z_][A-Za-z0-9_]*$`。

#### [KE-C02] LLM 返回的实体 JSON 无校验直接入图
**文件**: `graph_builder.py:325-329`
LLM 返回的 `entities`/`relations` 无 Pydantic 验证，恶意构造的 type/name 可绕过白名单。
**修复**: 用 Pydantic 模型验证每个 entity/relation。

#### [KE-H01] Milvus delete 表达式注入
**文件**: `milvus_store.py:82-83`
`ids` 直接 f-string 拼接。需 sanitize 或使用参数化 API。

#### [KE-H02] Graph Retriever N+1 查询
**文件**: `graph_retriever.py:70-103`
每个 seed entity 串行 2 次 `get_neighbors`。5 seed 最坏 10+N 次图查询。
**修复**: 用一条 Cypher 路径查询替代。

#### [KE-H03] ES Store 无认证配置
**文件**: `es_store.py:6-11`
生产 ES 需认证和 TLS，当前只传 host。

### Memory Engine

#### [ME-C02] 长期记忆 LLM JSON 无限制执行
**文件**: `backend/app/engines/memory_engine/memory.py:93-118`
LLM 返回巨大数组或超长 content 会触发大量 embedding 调用和 vector 写入。
**修复**: 限制数组长度（≤10）和每条 content 长度。

#### [ME-H04] EpisodicMemory 无租户隔离
**文件**: `memory.py:215`
固定 collection_name `episodic_memory`，所有租户共享，无 user_id 过滤。
**修复**: 使用 `episodic_memory_{tenant_id}` 或 metadata filter。

#### [ME-H05] 长期记忆搜索应用层过滤 — top_k 被稀释
**文件**: `memory.py:127-141`
先检索 top_k，再按 user_id 过滤。多用户共享 collection 时实际结果远少于 top_k。

#### [ME-H06] add_message 每次触发 3 次 LLM 调用
**文件**: `memory.py:380-391`
最坏：extract_and_store + compress + maybe_summarize = 3 次 LLM。
**修复**: 后台异步 + debounce。

### Workflow Engine

#### [WF-C01] eval() 沙箱逃逸 — AST 白名单可绕过
**文件**: `backend/app/engines/workflow_engine/workflow.py:212-220`
白名单允许 `ast.Call` + `ast.Attribute`，可构造 `str.__class__.__base__.__subclasses__()` 逃逸。
**修复**: 使用 `simpleeval` 或从白名单移除 `ast.Attribute`，拒绝 `__` 开头属性名。

#### [WF-C02] 代码执行节点沙箱不充分
**文件**: `workflow.py:491-522`
临时文件 `/tmp` 全局可读；`proc.kill()` 不杀子进程树；无资源限制/网络隔离。
**修复**: 使用 Docker 容器或 nsjail 隔离；`os.killpg` 杀进程组。

#### [WF-H01] HTTP 节点只支持 GET/POST
PUT/PATCH/DELETE 都被当作 POST 发送。

#### [WF-H02] 并行节点空实现
**文件**: `workflow.py:441-451`
`run_task` 直接返回硬编码结果，无实际执行。

#### [WF-H03] 全局状态共享 — 多 worker 不共享 approval
**文件**: `workflow.py:18-20`
模块级 dict 在多 worker 下无法共享；且 `_approval_decisions` 从不清理。

### Safety Engine

#### [SE-H01] Prompt Injection 正则易绕过
**文件**: `safety.py:48-58`
9 条正则只覆盖最基础模式。同义词、编码、分散注入、语言混合均可绕过。LLM 检查仅 >200 字符触发。

#### [SE-H02] LLM moderation 解析失败默认 PASS
**文件**: `safety.py:165-177`
JSON 解析失败时 `safe=True`。攻击者诱导非 JSON 响应即可绕过安全检查。
**修复**: fail-closed 策略 — 解析失败默认 WARN 或 BLOCK。

#### [SE-H03] 输出检查复用输入检查逻辑
**文件**: `safety.py:127-128`
输出安全标准应比输入更严格（关注信息泄露、有害内容），而非完全相同。

### Tool Engine

#### [TE-C01] db_query SQL 注入防护不充分
**文件**: `builtin/db_query.py:38-60`
关键词黑名单可绕过（`LOAD DATA INFILE` 不在黑名单）；Unicode 空白字符绕过 word boundary；直接执行原始 SQL。
**修复**: 使用 SQL AST 解析器验证；限制可查询表；只读连接。

#### [TE-H01] OpenAPI schema parser 无 SSRF 防护
**文件**: `schema_parser.py:108-143`
`_create_api_handler` 直接使用解析的 URL 发请求，未调用 `is_safe_url`。

#### [TE-H02] ToolRegistry 单例 — 多 worker 不共享
动态注册的 custom tool 仅在接收请求的 worker 可见。

### 跨引擎架构

#### [ARCH-H01] 缺少统一错误传播机制
各引擎错误策略不同：直接 raise / return [] / except pass / 返回 dict。无统一 `EngineError` 基类。

#### [ARCH-H02] 缺少可观测性
无 OpenTelemetry 集成。RAG retrieve→rerank→generate 无 span 记录。LLM 调用无标准 latency/token 指标。

#### [ARCH-H03] 租户隔离不完整
EpisodicMemory 固定 collection；Neo4j 无租户隔离；Milvus 未强制 tenant_id 前缀。

#### [ARCH-H04] LLM 调用 model="" 硬编码空字符串
`rag_pipeline.py`、`memory.py`、`graph_builder.py` 等多处 `model=""`，依赖 adapter 默认值，可能导致不必要的成本。

---

## 四、业务层审核（前端 + 基础设施）

### CRITICAL 级别

#### [BL-C01] init.sql 硬编码 admin 密码
**文件**: `scripts/init.sql:674-676`
密码 `admin123` 明文写在注释中，无首次登录强制修改机制。

#### [BL-C02] 无 .gitignore 文件
`.env`、`node_modules/`、`.next/`、`*.rvf` 可能被提交。安全风险极高。

#### [BL-C03] Docker 容器全部以 root 运行
**文件**: `backend/Dockerfile`, `frontend/Dockerfile`
无 `USER` 指令。应用漏洞可获取容器内 root 权限。

#### [BL-C04] Elasticsearch 安全完全关闭
**文件**: `docker-compose.yml:77`
`xpack.security.enabled=false`，端口 9200 直接暴露。

#### [BL-C05] RabbitMQ 默认凭证
`.env.example` 建议 guest/guest，管理界面 15672 暴露。

#### [BL-C06] JWT 存储在 localStorage — XSS 窃取风险
**文件**: `frontend/src/lib/api.ts:140-144`
任何 XSS 漏洞都可窃取 token。

#### [BL-C07] Auth Cookie 缺少 HttpOnly 和 Secure 标志
**文件**: `frontend/src/store/auth.ts:7-8`
JavaScript 可读 cookie；HTTP 明文传输。

#### [BL-C08] 无 TLS/SSL 终止
**文件**: `nginx/nginx.conf:19`
仅监听 80 端口，所有流量（含密码/token）明文传输。

#### [BL-C09] 数据库端口全部暴露到宿主机
MySQL/Redis/Milvus/Neo4j/ES/MinIO/RabbitMQ 端口全部映射到宿主机。Redis 无密码。

### HIGH 级别

#### [BL-H01] 生产 compose 挂载源码目录
`docker-compose.yml:132-133` — `./backend:/app` bind mount，仅适用于开发。

#### [BL-H02] Redis 无认证
端口 6379 暴露，无 `requirepass`。

#### [BL-H03] MinIO 默认 access key
`MINIO_ACCESS_KEY=minioadmin` 硬编码。

#### [BL-H04] SSE 流式聊天绕过 axios 拦截器
**文件**: `frontend/src/store/chat.ts:55-59`
手动从 localStorage 取 token，401 不会触发自动登出。

#### [BL-H05] SSE JSON 解析空 catch
**文件**: `frontend/src/store/chat.ts:97`
`catch {}` 静默吞掉解析错误，聊天可能冻结无提示。

#### [BL-H06] 前端 Dockerfile 拷贝完整 node_modules
**文件**: `frontend/Dockerfile:14`
可用 `output: 'standalone'` 从 ~1GB 减至 ~150MB。

#### [BL-H07] Docker 服务无资源限制
ES/Milvus/Neo4j 可耗尽宿主机资源。

#### [BL-H08] API Key 可能泄露到前端
**文件**: `frontend/src/app/(platform)/models/page.tsx:166`
若后端 `GET /models/providers` 返回 `api_key` 字段，将暴露到前端 JS 状态。

### MEDIUM 级别

| 编号 | 问题 | 文件 |
|------|------|------|
| BL-M01 | Auth store 模块级副作用导致 SSR 崩溃 | `store/auth.ts:25-32` |
| BL-M02 | Chat 消息 ID 用 Date.now()，同毫秒冲突 | `store/chat.ts:38-39` |
| BL-M03 | 删除操作无确认弹窗 | `agents/page.tsx:31-38` |
| BL-M04 | 大量内联样式，Tailwind 已装但未用 | 全局 |
| BL-M05 | 无外键约束，孤立记录可累积 | `scripts/init.sql` |
| BL-M06 | 工作流编辑器使用原生 DOM 拖拽，无 React Flow | `workflows/[id]/page.tsx` |

---

## 五、竞品横向对比

### 对比平台
Dify、Coze Studio、FastGPT、Flowise、LangFlow、Bisheng、MaxKB

### 评分矩阵

| 维度 | AEP | 评级 | 关键差距 |
|------|-----|------|----------|
| 多 LLM 支持与路由 | 4 adapters + 轮询/权重/熔断 | **PARITY** | Dify 50+ providers |
| 插件/扩展架构 | 6 内置 + MCP server | **BEHIND** | Dify/Coze 50-100+ 工具 |
| API 设计 + SDK | REST v1, 23 端点组 | **BEHIND** | 无 SDK；Dify/Coze 多语言 SDK |
| 多租户 + RBAC | 4 角色 + 11 资源类型 | **PARITY** | 与 Bisheng/MaxKB 同级 |
| **RAG 管道** | 7 种检索模式含 LightRAG/Graph RAG | **AHEAD** | 最全面 |
| **记忆系统** | 4 层（短期/长期/工作/情景）+ 自动摘要 | **AHEAD** | 无竞品同级 |
| **安全引擎** | 注入+PII+敏感词+LLM 审核+SSRF+安全代码执行 | **AHEAD** | 最全面 |
| **评估引擎** | 5 项 Ragas 指标 | **AHEAD** | 少数竞品有内置评估 |
| 工作流引擎（后端） | 8 节点类型含并行/循环/人工审批 | **PARITY** | 后端能力足够 |
| 工作流引擎（前端） | 列表页，无拖拽画布 | **BEHIND** | **所有竞品都有可视化编辑器** |
| Agent 生命周期 | 基础 CRUD | **BEHIND** | 缺版本管理、发布/草稿分离、模板市场 |
| 知识库管理 | 5 解析器 + 4 分块策略 | **PARITY** | 缺网页爬虫、OCR 精度不如 Bisheng |
| 分析监控 | 基础指标 + 成本追踪 | **BEHIND** | 缺 OpenTelemetry、分布式追踪 |
| 部署灵活性 | Docker Compose 9 服务 | **PARITY** | 无 Helm Chart |

### 核心差距优先级

| 优先级 | 差距 | 影响 |
|--------|------|------|
| **P0** | 可视化工作流编辑器 | 市场准入门槛，所有竞品必备 |
| **P0** | 安全漏洞修复（14 个 CRITICAL） | 生产部署风险 |
| **P1** | 插件扩展至 20+ 工具 | Agent 能力边界 |
| **P1** | Python/TypeScript SDK | 开发者集成体验 |
| **P1** | OpenTelemetry 集成 | 生产可观测性 |
| **P2** | Graph RAG 可视化 UI | 独特卖点展示 |
| **P2** | 记忆管理 UI | 独特卖点展示 |
| **P2** | 安全策略配置 UI | 差异化展示 |
| **P2** | Helm Chart | 企业 K8s 部署 |

---

## 六、修复优先级路线图

### Phase 1 — 安全加固（1-2 周）

1. 创建 `.gitignore`
2. 移除 init.sql 硬编码密码，改为环境变量驱动
3. 添加 Nginx TLS 终止
4. 移除数据库端口宿主机映射
5. Dockerfile 添加非 root 用户
6. 启用 ES 安全认证
7. Redis 添加密码
8. 登录端点添加速率限制
9. JWT 迁移到 HttpOnly Cookie
10. 修复 eval() 沙箱逃逸（使用 simpleeval）
11. 修复审计日志（设置 request.state）
12. Safety Engine 改为 fail-closed
13. Neo4j merge_node key 参数校验
14. 代码执行节点沙箱加固

### Phase 2 — 架构修复（2-3 周）

1. 修复 SSE DB Session 生命周期
2. 统一错误传播（EngineError 基类）
3. LLM Adapter 添加重试 + 连接池复用
4. EpisodicMemory 租户隔离
5. CostTracker 价格单位明确化
6. get_db commit 策略优化
7. 添加全局异常处理器
8. API response_model 强制执行
9. Triggers API 权限检查
10. Docker 服务资源限制

### Phase 3 — 竞争力建设（4-8 周）

1. 可视化工作流编辑器（React Flow）
2. 插件扩展至 20+ 内置工具
3. Python/TypeScript SDK
4. OpenTelemetry 集成
5. Graph RAG 可视化 UI
6. 记忆管理 UI
7. Helm Chart
8. 监控 Dashboard

---

## 七、总结

**核心竞争力**: RAG（7 种检索模式含 LightRAG/Graph RAG）、记忆系统（4 层架构）、安全引擎（多层管道）是真正差异化优势，无竞品同级。

**最大短板**: 前端可视化工作流编辑器缺失是市场准入障碍；14 个 CRITICAL 安全漏洞阻碍生产部署。

**建议策略**: 先修复安全（Phase 1），再补架构（Phase 2），最后差异化竞争（Phase 3）。独特卖点（Graph RAG + 多层记忆 + 安全引擎）是立足之本，应优先投入 UI 化展示。

# Agent Engine Platform 产品手册

> **版本**: v3.0  
> **更新日期**: 2026-06-01  
> **适用环境**: 开发、测试、生产环境

---

## 目录

- [1. 产品概述](#1-产品概述)
- [2. 核心功能](#2-核心功能)
- [3. 架构设计](#3-架构设计)
- [4. 引擎详解](#4-引擎详解)
- [5. API参考](#5-api参考)
- [6. 部署指南](#6-部署指南)
- [7. 配置说明](#7-配置说明)
- [8. 开发指南](#8-开发指南)
- [9. 最佳实践](#9-最佳实践)
- [10. 故障排除](#10-故障排除)

---

## 1. 产品概述

### 1.1 产品简介

Agent Engine Platform 是一个企业级AI智能体（Agent）构建、编排和运维平台。它将智能体配置、知识库管理、可视化工作流编辑、模型路由、工具集成、市场分发和全栈可观测性统一到一个控制平面中。

**核心价值主张**：将智能体从"构想"到"生产部署"的时间降至最低，同时保持多租户组织的治理、可观测性和成本控制。

### 1.2 目标用户

#### 主要用户群体

| 用户角色 | 使用场景 | 核心需求 |
|---------|---------|---------|
| **ML工程师** | 配置智能体、调试工作流执行 | 快速迭代、详细日志、模型对比 |
| **解决方案架构师** | 设计多智能体协作方案 | 工作流编排、系统集成、性能优化 |
| **产品经理** | 审批市场提交、监控使用情况 | 可观测性仪表板、成本追踪、合规审计 |
| **租户管理员** | 管理用户权限、配置组织设置 | RBAC权限、多租户隔离、审计日志 |

#### 使用环境

- **设备**: 大型显示器（办公室环境）、平板电脑（事件响应）
- **会话时长**: 专注工作会话（配置、监控、调试）
- **技术熟练度**: 技术娴熟、时间敏感

### 1.3 产品目标

**成功标准**：
- 新智能体可以在不离开平台的情况下完成构思、构建、测试和部署到生产环境
- 运行时行为完全可观测、可审计、可追踪成本

**关键成果**：
1. 智能体创建时间从数天缩短到数小时
2. 工作流执行失败率降低50%
3. 模型调用成本可视化和优化
4. 多租户环境下的安全合规保障

### 1.4 设计原则

#### 核心设计哲学

1. **以身作则** (Practice what you preach)
   - Agent Engine帮助用户构建智能系统，其自身界面应在信息架构上体现智能

2. **展示而非告知** (Show, don't tell)
   - 数据和状态通过视觉层次和动画传达，而非解释性文字

3. **有纪律的密度** (Density with discipline)
   - 企业用户需要信息密度，但每个像素必须有其存在的价值

4. **柔和是一种特性** (Softness is a feature)
   - 低饱和度、温暖中性和充足空白减少长时间使用时的认知负荷

5. **熟悉是一种特性** (Familiarity is a feature)
   - 标准导航模式、可预测的表单布局和一致的组件词汇减少认知负荷

6. **工具融入任务** (The tool disappears into the task)
   - 用户在调试失败的工作流或比较模型输出时，不应思考界面

7. **颜色专用于信号** (Color is reserved for signal)
   - 温暖中性承载界面，颜色（橄榄绿、暖金）仅用于指示状态、操作或含义

### 1.5 品牌个性

**三个词**: 精准、温暖、持久

**语调**: 自信而不傲慢，技术性而不冰冷。每个界面元素都应感觉经过精心排版——有度量的间距、温暖的中性色、清晰的功能提示，没有装饰性的赘余。

**情感目标**: 用户应对复杂系统感到**安心**。产品应传达冷静的能力——低饱和度的温暖，表明"此工具为长时间工作而生，而非演示截图"。

### 1.6 技术栈

#### 后端技术

| 技术 | 用途 |
|------|------|
| Python 3.11 | 运行时环境 |
| FastAPI | Web框架 |
| SQLAlchemy 2.0 + aiomysql | 异步ORM |
| Pydantic 2.0 | 数据验证 |
| Celery + Redis | 异步任务队列 |
| Alembic | 数据库迁移 |
| python-jose | JWT认证 |
| httpx | 异步HTTP客户端 |
| sse-starlette | SSE流式响应 |
| pymilvus | Milvus向量数据库客户端 |
| neo4j | Neo4j图数据库驱动 |
| elasticsearch | ES客户端 |
| minio | 对象存储客户端 |

#### 前端技术

| 技术 | 用途 |
|------|------|
| Next.js 14 | React框架（App Router） |
| React 18 | UI库 |
| TypeScript 5 | 类型安全 |
| Ant Design 5 | UI组件库 |
| Tailwind CSS 3 | 样式 |
| Zustand | 状态管理 |
| Axios | HTTP客户端 |
| ECharts | 数据可视化 |
| React Markdown | Markdown渲染 |
| Jest + Testing Library | 测试 |

#### 基础设施

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

## 2. 核心功能

### 2.1 功能概览

Agent Engine Platform 提供以下核心功能模块：

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Engine Platform                     │
├─────────────────────────────────────────────────────────────┤
│  🤖 智能体管理  │  📚 知识引擎  │  ⚡ 工作流引擎  │  🔧 工具引擎  │
├─────────────────────────────────────────────────────────────┤
│  🔀 模型路由    │  🛡️ 安全引擎  │  🧠 记忆引擎    │  📊 评估引擎  │
├─────────────────────────────────────────────────────────────┤
│  🤝 多智能体    │  🔌 MCP服务   │  👥 多租户      │  📝 审计监控  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 智能体管理

#### 功能描述

智能体管理是平台的核心功能，允许用户创建、配置、测试和发布AI智能体。

#### 主要特性

- **智能体创建**: 可视化配置智能体参数
- **模型选择**: 支持多种LLM模型（OpenAI、Anthropic、Ollama等）
- **系统提示词**: 可编辑的系统提示词模板
- **工具绑定**: 为智能体分配可用工具
- **知识库关联**: 将智能体与知识库关联
- **版本管理**: 智能体配置的版本控制
- **发布流程**: 从草稿到发布的完整工作流

#### 配置参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 智能体名称 | "客服助手" |
| `description` | 智能体描述 | "处理客户咨询的AI助手" |
| `model_id` | 使用的模型ID | "gpt-4o" |
| `system_prompt` | 系统提示词 | "你是一个专业的客服代表..." |
| `tools` | 绑定的工具列表 | ["calculator", "web_search"] |
| `knowledge_bases` | 关联的知识库 | ["product_docs", "faq"] |
| `temperature` | 生成温度 | 0.7 |
| `max_tokens` | 最大token数 | 4096 |

#### 工作流程

```
创建智能体 → 配置参数 → 绑定工具/知识库 → 测试对话 → 发布到市场
     ↓           ↓            ↓              ↓           ↓
   基本信息    模型选择      能力扩展        验证效果     上线运营
```

### 2.3 知识引擎

#### 功能描述

知识引擎提供完整的RAG（检索增强生成）管道，从文档上传到智能问答。

#### 核心流程

```
上传文档 → 解析文档 → 智能分块 → 向量化 → 存储 → 检索 → 重排序 → 生成
```

#### 支持的文档格式

| 格式 | 解析器 | 特性 |
|------|--------|------|
| PDF | PyPDF2 | 支持扫描件OCR |
| Word | python-docx | 保留格式结构 |
| Excel | openpyxl | 表格数据提取 |
| PowerPoint | python-pptx | 幻灯片内容 |
| TXT | 内置 | 纯文本处理 |
| Markdown | 内置 | Markdown语法 |

#### 检索模式

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| `naive` | 纯向量相似度 | 通用问答 |
| `local` | 实体聚焦 - 提取名称搜索图节点 | 精确事实查询 |
| `global` | 主题聚焦 - 提取概念搜索关系边 | 宏观分析 |
| `hybrid` | local + global 加权RRF融合 | 复杂综合查询 |

#### 存储后端

- **Milvus**: 向量存储和相似度搜索
- **Elasticsearch**: 全文搜索和关键词匹配
- **Neo4j**: 图关系存储和实体检索

### 2.4 工作流引擎

#### 功能描述

工作流引擎提供DAG（有向无环图）编排能力，支持复杂的多步骤任务执行。

#### 节点类型

| 节点类型 | 描述 | 功能 |
|---------|------|------|
| `llm` | LLM调用节点 | 调用大语言模型 |
| `condition` | 条件分支 | 根据条件选择路径 |
| `parallel` | 并行执行 | 同时执行多个分支 |
| `loop` | 循环执行 | 重复执行直到条件满足 |
| `http` | HTTP请求 | 调用外部API |
| `code` | 代码沙箱 | 执行Python代码 |
| `human` | 人工审批 | 需要人工介入 |
| `sub_workflow` | 子工作流 | 调用其他工作流 |

#### 执行特性

- **全局超时控制**: 防止工作流无限运行
- **节点级执行追踪**: 每个节点的执行详情
- **变量快照**: 执行过程中的变量状态
- **详细执行日志**: 完整的执行历史记录
- **错误处理**: 节点失败时的重试和回退策略
- **人工审批**: 关键节点的人工确认机制

#### 工作流示例

```yaml
# 客户服务工作流示例
workflow:
  name: "客户服务处理"
  nodes:
    - id: "start"
      type: "start"
      next: "classify"

    - id: "classify"
      type: "llm"
      config:
        prompt: "对客户问题进行分类: {{input}}"
        model: "gpt-4o"
      next: "route"

    - id: "route"
      type: "condition"
      conditions:
        - if: "classification == 'technical'"
          next: "technical_support"
        - if: "classification == 'billing'"
          next: "billing_support"
        - else: "general_support"

    - id: "technical_support"
      type: "sub_workflow"
      workflow_id: "tech_support_flow"
      next: "end"

    - id: "billing_support"
      type: "human"
      config:
        approver_role: "billing_team"
      next: "end"

    - id: "general_support"
      type: "llm"
      config:
        prompt: "回答一般性问题: {{input}}"
      next: "end"

    - id: "end"
      type: "end"
```

### 2.5 多智能体协作

#### 协作模式

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| **Sequential** | 顺序执行 | 流水线处理 |
| **Hierarchical** | 层级协作 | 主从模式 |
| **Parallel** | 并行执行 | 独立任务并行 |
| **Consensus** | 共识决策 | 需要多方意见 |

#### Handoff协议

基于Pydantic的`HandoffMessage`协议，支持智能体之间的结构化交接：

```python
class HandoffMessage(BaseModel):
    source_agent: str
    target_agent: str
    context: Dict[str, Any]
    task_description: str
    priority: int
    metadata: Dict[str, Any]
```

#### 交接追踪

`HandoffTracker`追踪交接状态和跳数，防止无限循环：

```python
tracker = HandoffTracker(max_hops=10)
tracker.record_handoff(source="agent_a", target="agent_b")
if tracker.is_circular():
    raise CircularHandoffError()
```

### 2.6 工具引擎

#### 内置工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `calculator` | 数学表达式计算 | 数值计算 |
| `code_executor` | Python代码沙箱执行 | 代码执行 |
| `db_query` | 数据库查询（参数化） | 数据检索 |
| `file_ops` | 文件读写操作 | 文件处理 |
| `http_request` | HTTP请求 | API调用 |
| `web_search` | 网络搜索 | 信息检索 |

#### 自定义工具注册

通过`ToolRegistry`支持动态注册自定义工具：

```python
from app.engines.tool_engine import ToolRegistry

registry = ToolRegistry()

@registry.register(
    name="custom_tool",
    description="自定义工具描述",
    parameters={
        "param1": {"type": "string", "description": "参数1说明"},
        "param2": {"type": "integer", "description": "参数2说明"}
    }
)
async def custom_tool(param1: str, param2: int) -> str:
    # 工具实现
    return f"处理结果: {param1}, {param2}"
```

### 2.7 安全引擎

#### 四层安全防护

1. **提示词注入检测**
   - 正则表达式匹配
   - 语义分析
   - 已知攻击模式识别

2. **PII脱敏**
   - 身份证号自动检测和脱敏
   - 手机号脱敏
   - 邮箱地址脱敏
   - 银行卡号脱敏

3. **敏感信息过滤**
   - 可配置的敏感度级别（低/中/高）
   - 自定义敏感词库
   - 上下文相关的过滤规则

4. **合规检查**
   - 可选的合规策略开关
   - 行业特定的合规规则
   - 审计日志记录

#### 安全配置

```yaml
safety_engine:
  input_check:
    enabled: true
    prompt_injection_detection: true
    pii_masking: true
    sensitivity_level: "medium"
  output_check:
    enabled: true
    sensitive_info_filtering: true
    compliance_check: true
```

### 2.8 记忆引擎

#### 短期记忆

基于Redis的会话历史管理：

- **TTL控制**: 自动过期清理
- **消息限制**: 最大消息数量限制
- **会话隔离**: 每个会话独立存储

```python
short_term = ShortTermMemory(
    redis_url="redis://localhost:6379/0",
    ttl=3600,  # 1小时过期
    max_messages=100  # 最多100条消息
)
```

#### 长期记忆

向量化存储的长期记忆系统：

- **对话摘要压缩**: 自动压缩长对话
- **主题提取**: 提取对话主题
- **向量化存储**: 语义搜索能力
- **跨会话检索**: 历史对话检索

```python
long_term = LongTermMemory(
    vector_store=milvus_client,
    embedding_model="text-embedding-3-small"
)

# 存储记忆
await long_term.store(
    content="用户偏好设置...",
    metadata={"user_id": "user123", "topic": "preferences"}
)

# 检索记忆
memories = await long_term.retrieve(
    query="用户的偏好设置",
    top_k=5
)
```

### 2.9 评估引擎

#### Ragas风格评估指标

| 指标 | 描述 | 计算方式 |
|------|------|---------|
| `faithfulness` | 答案对检索上下文的忠实度 | 答案与上下文的一致性 |
| `answer_relevancy` | 答案对问题的相关性 | 答案与问题的语义相似度 |
| `context_precision` | 检索结果排序质量 | 相关文档的排名 |
| `context_recall` | 检索对必要信息的覆盖度 | 检索到的必要信息比例 |
| `tool_call_accuracy` | 工具调用正确性 | 工具调用的成功率 |

#### 评估流程

```python
from app.engines.eval_engine import EvalEngine

engine = EvalEngine()

# 运行评估
results = await engine.evaluate(
    questions=["问题1", "问题2"],
    answers=["答案1", "答案2"],
    contexts=[["上下文1"], ["上下文2"]],
    metrics=["faithfulness", "answer_relevancy"]
)

# 输出结果
print(f"Faithfulness: {results['faithfulness']:.2f}")
print(f"Answer Relevancy: {results['answer_relevancy']:.2f}")
```

### 2.10 模型路由

#### 多提供商支持

| 适配器 | 模型 | 能力 |
|--------|------|------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | 聊天/流式/函数调用 |
| `AnthropicAdapter` | Claude Sonnet/Opus/Haiku | 聊天/流式 |
| `OllamaAdapter` | Qwen2.5, Llama (本地) | 聊天/流式 |

#### 核心功能

- **ModelRouter**: 多提供商负载均衡
- **CircuitBreaker**: 自动故障隔离
- **CostTracker**: Token使用和成本追踪
- **Multimodal**: ASR/TTS/OCR/Vision适配器

#### 路由策略

```python
from app.engines.model_engine import ModelRouter

router = ModelRouter(
    providers=["openai", "anthropic", "ollama"],
    strategy="round_robin",  # 轮询策略
    fallback=True,  # 启用故障转移
    cost_tracking=True  # 启用成本追踪
)

# 调用模型
response = await router.chat(
    messages=[{"role": "user", "content": "你好"}],
    model="gpt-4o",
    stream=True
)
```

### 2.11 MCP服务

#### Model Context Protocol

通过MCP协议暴露平台能力：

```python
from app.mcp import MCPServer

server = MCPServer()

@server.tool("create_agent")
async def create_agent(name: str, model: str) -> dict:
    """创建新的AI智能体"""
    # 实现细节
    return {"agent_id": "new_agent_123"}

@server.tool("search_knowledge")
async def search_knowledge(query: str, top_k: int = 5) -> list:
    """搜索知识库"""
    # 实现细节
    return [{"content": "...", "score": 0.95}]
```

### 2.12 多租户

#### 租户隔离

- **数据隔离**: 每个租户的数据完全隔离
- **资源配额**: 可配置的资源使用限制
- **权限控制**: 基于角色的访问控制（RBAC）

#### RBAC权限系统

```yaml
roles:
  admin:
    permissions:
      - "agents:*"
      - "knowledge:*"
      - "workflows:*"
      - "users:*"
      - "tenants:*"

  developer:
    permissions:
      - "agents:read"
      - "agents:create"
      - "agents:update"
      - "knowledge:read"
      - "workflows:read"
      - "workflows:create"

  viewer:
    permissions:
      - "agents:read"
      - "knowledge:read"
      - "workflows:read"
```

### 2.13 审计与监控

#### 审计日志

记录所有关键操作：

- 用户登录/登出
- 智能体创建/修改/删除
- 知识库操作
- 工作流执行
- 模型调用
- 权限变更

#### 监控指标

- **系统指标**: CPU、内存、磁盘使用率
- **应用指标**: 请求量、响应时间、错误率
- **业务指标**: 智能体活跃数、对话量、模型调用量
- **成本指标**: Token使用量、API调用成本

---

## 3. 架构设计

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                      │
│                   HTTP :80 / HTTPS :443                      │
└──────────┬──────────────────────────────┬───────────────────┘
           │                              │
    ┌──────▼──────┐               ┌───────▼───────┐
    │   Frontend  │               │    Backend    │
    │  Next.js 14 │               │    FastAPI    │
    │   :3000     │               │    :8000      │
    └─────────────┘               └───────┬───────┘
                                          │
                    ┌─────────────────────┬┴──────────────────┐
                    │                     │                    │
             ┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────┐
             │    MySQL    │    │     Redis       │   │   Celery    │
             │   主数据库   │    │   缓存/队列     │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │Elasticsearch│ │  Neo4j  │
│  向量DB  │  │   全文搜索   │ │  图DB   │
└─────────┘  └─────────────┘ └─────────┘
```

### 3.2 数据流

#### 1. 用户请求流

```
用户请求 → Nginx → 前端（SSR/CSR）或 后端API
```

#### 2. 对话请求流

```
对话请求 → 后端 → 安全引擎（输入） → 模型路由 → LLM → 安全引擎（输出） → SSE流
```

#### 3. RAG请求流

```
RAG请求 → 知识引擎 → 解析 → 分块 → 向量化 → 存储（Milvus/ES/Neo4j） → 检索 → 重排序 → 生成
```

#### 4. 异步任务流

```
异步任务 → 后端 → Celery Worker（文档处理、模型训练、定时清理）
```

#### 5. 工作流执行流

```
工作流执行 → 工作流引擎 → DAG调度器 → 节点执行 → 人工审批 → 输出
```

### 3.3 组件职责

#### 前端（Next.js 14）

- **用户界面**: React组件渲染
- **状态管理**: Zustand全局状态
- **API调用**: Axios HTTP客户端
- **路由**: Next.js App Router
- **样式**: Tailwind CSS + Ant Design

#### 后端（FastAPI）

- **API服务**: RESTful API端点
- **业务逻辑**: 引擎协调和数据处理
- **认证授权**: JWT + RBAC
- **数据持久化**: SQLAlchemy ORM
- **异步处理**: Celery任务队列

#### 数据层

- **MySQL**: 主数据存储（用户、配置、元数据）
- **Redis**: 缓存、会话、消息队列
- **Milvus**: 向量存储（知识库嵌入）
- **Neo4j**: 图存储（实体关系）
- **Elasticsearch**: 全文搜索（文档索引）
- **MinIO**: 对象存储（文件上传）

### 3.4 扩展性设计

#### 水平扩展

```yaml
# Celery Worker扩展
docker-compose up -d --scale celery-worker=3

# 后端实例扩展（需要负载均衡器）
docker-compose up -d --scale backend=3
```

#### 垂直扩展

```yaml
# MySQL连接池调优
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis内存配置
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### 3.5 高可用设计

#### 数据库高可用

- **MySQL主从复制**: 读写分离
- **Redis Sentinel**: 自动故障转移
- **Milvus集群**: 多节点部署

#### 应用高可用

- **多实例部署**: 后端无状态设计
- **健康检查**: 自动重启失败实例
- **优雅关闭**: 处理中的请求完成后再关闭

---

## 4. 引擎详解

### 4.1 模型引擎

#### 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Model Engine                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Router    │  │   Circuit   │  │    Cost     │    │
│  │  负载均衡   │  │   Breaker   │  │   Tracker   │    │
│  │             │  │  故障隔离    │  │  成本追踪   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   OpenAI    │  │  Anthropic  │  │   Ollama    │    │
│  │  Adapter    │  │  Adapter    │  │  Adapter    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### 适配器实现

```python
class OpenAIAdapter:
    async def chat(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        stream: bool = False,
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        # OpenAI API调用实现
        pass

    async def embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        # 嵌入向量生成
        pass
```

#### 路由策略

```python
class ModelRouter:
    strategies = {
        "round_robin": self._round_robin,
        "least_cost": self._least_cost,
        "fastest": self._fastest,
        "random": self._random
    }

    async def chat(self, messages, **kwargs):
        provider = self.select_provider(strategy=self.strategy)
        try:
            return await provider.chat(messages, **kwargs)
        except Exception as e:
            if self.fallback:
                return await self.fallback_provider.chat(messages, **kwargs)
            raise
```

### 4.2 知识引擎

#### RAG管道

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Upload    │ →  │    Parse    │ →  │    Chunk    │
│   文档上传   │    │   文档解析   │    │   智能分块   │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
┌─────────────┐    ┌─────────────┐    ┌─────▼───────┐
│  Generate   │ ←  │   Rerank    │ ←  │   Embed     │
│   生成答案   │    │   重排序     │    │   向量化     │
└─────────────┘    └─────────────┘    └─────────────┘
       ↑                                     │
┌──────┴──────┐    ┌─────────────┐    ┌─────▼───────┐
│   Retrieve  │ ←  │    Store    │ ←  │   Store     │
│   检索结果   │    │  Milvus/ES  │    │   Neo4j     │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### 分块策略

```python
class SmartChunker:
    def chunk(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
        strategy: str = "semantic"
    ) -> List[Chunk]:
        """
        分块策略:
        - fixed: 固定大小分块
        - sentence: 按句子分块
        - paragraph: 按段落分块
        - semantic: 语义分块（推荐）
        """
        pass
```

#### LightRAG检索

```python
class LightRAGRetriever:
    async def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        检索模式:
        - naive: 纯向量相似度
        - local: 实体聚焦检索
        - global: 主题聚焦检索
        - hybrid: 混合检索（推荐）
        """
        pass
```

### 4.3 工作流引擎

#### DAG执行器

```python
class DAGExecutor:
    async def execute(
        self,
        workflow: Workflow,
        inputs: Dict[str, Any]
    ) -> ExecutionResult:
        # 拓扑排序
        sorted_nodes = self.topological_sort(workflow.nodes)

        # 执行节点
        context = ExecutionContext(inputs=inputs)
        for node in sorted_nodes:
            result = await self.execute_node(node, context)
            context.set_output(node.id, result)

            # 处理条件分支
            if node.type == "condition":
                next_node = self.evaluate_condition(node, context)
                # 跳转到下一个节点

        return context.get_final_output()
```

#### 节点执行器

```python
class NodeExecutor:
    executors = {
        "llm": self._execute_llm,
        "condition": self._execute_condition,
        "parallel": self._execute_parallel,
        "loop": self._execute_loop,
        "http": self._execute_http,
        "code": self._execute_code,
        "human": self._execute_human,
        "sub_workflow": self._execute_sub_workflow
    }

    async def execute_node(self, node, context):
        executor = self.executors[node.type]
        return await executor(node, context)
```

### 4.4 安全引擎

#### 检测管道

```
输入 → 提示词注入检测 → PII检测 → 敏感信息过滤 → 合规检查 → 输出
```

#### 检测规则

```python
class SafetyEngine:
    # 提示词注入检测规则
    injection_patterns = [
        r"ignore previous instructions",
        r"you are now",
        r"system prompt",
        r"jailbreak",
        # ... 更多模式
    ]

    # PII检测规则
    pii_patterns = {
        "phone": r"1[3-9]\d{9}",
        "id_card": r"\d{17}[\dXx]",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "bank_card": r"\d{16,19}"
    }

    async def check_input(self, text: str) -> SafetyResult:
        # 检测逻辑
        pass
```

### 4.5 记忆引擎

#### 短期记忆实现

```python
class ShortTermMemory:
    def __init__(self, redis_client, ttl=3600, max_messages=100):
        self.redis = redis_client
        self.ttl = ttl
        self.max_messages = max_messages

    async def add_message(self, session_id: str, message: Dict):
        key = f"session:{session_id}:messages"
        await self.redis.lpush(key, json.dumps(message))
        await self.redis.ltrim(key, 0, self.max_messages - 1)
        await self.redis.expire(key, self.ttl)

    async def get_messages(self, session_id: str) -> List[Dict]:
        key = f"session:{session_id}:messages"
        messages = await self.redis.lrange(key, 0, -1)
        return [json.loads(m) for m in messages]
```

#### 长期记忆实现

```python
class LongTermMemory:
    def __init__(self, vector_store, embedding_model):
        self.vector_store = vector_store
        self.embedding_model = embedding_model

    async def store(self, content: str, metadata: Dict):
        embedding = await self.embed(content)
        await self.vector_store.insert(
            collection="long_term_memory",
            vectors=[embedding],
            metadata=[metadata]
        )

    async def retrieve(self, query: str, top_k: int = 5):
        query_embedding = await self.embed(query)
        results = await self.vector_store.search(
            collection="long_term_memory",
            vector=query_embedding,
            top_k=top_k
        )
        return results
```

---

## 5. API参考

### 5.1 API概览

所有API路由前缀: `/api/v1`

#### 认证

所有需要认证的路由使用JWT Bearer令牌：

```http
Authorization: Bearer <access_token>
```

#### 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "错误描述",
  "detail": "详细错误信息"
}
```

### 5.2 API模块

| 模块 | 路由 | 描述 |
|------|------|------|
| Auth | `/auth/*` | 登录、注册、令牌刷新 |
| Agents | `/agents/*` | 智能体CRUD、发布 |
| Chat | `/chat/*` | 对话（SSE流式） |
| Conversations | `/conversations/*` | 会话管理 |
| Knowledge | `/knowledge/*` | 知识库、文档上传、检索 |
| Models | `/models/*` | 模型提供商配置 |
| Workflows | `/workflows/*` | 工作流CRUD、执行 |
| Tools | `/tools/*` | 工具管理 |
| Multi-Agent | `/multi-agent/*` | 多智能体编排 |
| Memory | `/memory/*` | 记忆管理 |
| Evaluations | `/evaluations/*` | RAG评估 |
| Triggers | `/triggers/*` | 定时/事件/Webhook触发器 |
| Webhooks | `/webhooks/*` | Webhook端点管理 |
| Audit | `/audit/*` | 审计日志查询 |
| Usage | `/usage/*` | 模型使用统计 |
| Users | `/users/*` | 用户管理 |
| Roles | `/roles/*` | 角色权限管理 |
| Tenants | `/tenants/*` | 租户管理 |
| Tokens | `/tokens/*` | API令牌管理 |
| Feedbacks | `/feedbacks/*` | 用户反馈 |
| Tasks | `/tasks/*` | Celery任务状态 |

### 5.3 核心API示例

#### 认证API

```http
# 登录
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

# 响应
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 智能体API

```http
# 创建智能体
POST /api/v1/agents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "客服助手",
  "description": "处理客户咨询的AI助手",
  "model_id": "gpt-4o",
  "system_prompt": "你是一个专业的客服代表...",
  "tools": ["calculator", "web_search"],
  "knowledge_bases": ["product_docs"]
}

# 获取智能体列表
GET /api/v1/agents?page=1&size=20
Authorization: Bearer <token>
```

#### 对话API

```http
# 发送对话（SSE流式）
POST /api/v1/chat/completions
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent_id": "agent_123",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "stream": true
}

# SSE响应格式
data: {"choices": [{"delta": {"content": "你"}}]}
data: {"choices": [{"delta": {"content": "好"}}]}
data: [DONE]
```

#### 知识库API

```http
# 上传文档
POST /api/v1/knowledge/{kb_id}/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <document.pdf>

# 检索知识库
POST /api/v1/knowledge/{kb_id}/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "产品功能介绍",
  "top_k": 5,
  "mode": "hybrid"
}
```

#### 工作流API

```http
# 创建工作流
POST /api/v1/workflows
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "客户服务流程",
  "description": "处理客户服务请求的工作流",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "next": "classify"
    },
    {
      "id": "classify",
      "type": "llm",
      "config": {
        "prompt": "对客户问题进行分类",
        "model": "gpt-4o"
      }
    }
  ]
}

# 执行工作流
POST /api/v1/workflows/{workflow_id}/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "inputs": {
    "customer_query": "我的订单在哪里？"
  }
}
```

### 5.4 健康检查

```http
GET /health

# 响应
{
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok",
    "milvus": "ok",
    "neo4j": "ok",
    "elasticsearch": "ok"
  }
}
```

---

## 6. 部署指南

### 6.1 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Docker | 24.0+ | 容器运行时 |
| Docker Compose | v2.20+ | `docker compose` (V2插件) |
| 系统内存 | 16 GB | Milvus + ES + Neo4j共需约8GB |
| 磁盘 | 40 GB | Docker镜像 + 数据卷 |
| CPU | 4核 | 推荐8核 |
| 操作系统 | Linux (Ubuntu 22.04+) / macOS | 内核5.x+ |

### 6.2 快速部署

#### 1. 克隆代码

```bash
git clone <repository-url>
cd agent-engine-platform
```

#### 2. 生成密钥

```bash
# JWT签名密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Fernet对称加密密钥
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 3. 配置环境变量

```bash
cp .env.example .env
vim .env  # 修改所有<PRODUCTION>标记项
```

#### 4. 启动服务

```bash
# 全部启动（所有基础设施 + 应用服务）
docker-compose --profile full up -d

# 或使用外部数据库（仅启动应用 + Neo4j）
docker-compose --profile external-db up -d
```

#### 5. 验证部署

```bash
# 查看容器状态
docker-compose ps

# 健康检查
curl http://localhost/health

# 验证登录
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 6.3 生产环境部署

#### 安全加固

```bash
# 1. 修改默认密码
# 2. 设置文件权限
chmod 600 .env

# 3. 配置HTTPS
# 编辑nginx/nginx.conf，启用HTTPS配置
# 将证书放入nginx/ssl/

# 4. 限制端口访问
# 修改docker-compose.yml，绑定127.0.0.1
```

#### 性能优化

```yaml
# MySQL优化
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis优化
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

# Elasticsearch优化
ES_HEAP_MIN=1g
ES_HEAP_MAX=1g
```

### 6.4 扩展部署

#### Celery Worker扩展

```bash
docker-compose up -d --scale celery-worker=3
```

#### 多实例部署

```bash
# 需要外部负载均衡器
docker-compose up -d --scale backend=3
```

### 6.5 备份与恢复

#### MySQL备份

```bash
# 备份
docker-compose exec mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction agent_engine > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复
docker-compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  agent_engine < backup_20260601.sql
```

#### Redis备份

```bash
# 触发RDB快照
docker-compose exec redis redis-cli BGSAVE
# 复制快照
docker-compose cp agent-engine-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

#### Milvus备份

```bash
# 备份volume
docker-compose stop milvus-standalone
docker run --rm \
  -v agent-engine-platform_milvus_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/milvus_backup_$(date +%Y%m%d).tar.gz -C /data .
docker-compose start milvus-standalone
```

---

## 7. 配置说明

### 7.1 环境变量

#### 通用配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENVIRONMENT` | development | 环境标识 (development/staging/production) |
| `LOG_LEVEL` | INFO | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `APP_PORT` | 8000 | 后端端口 |
| `FRONTEND_PORT` | 3000 | 前端端口 |

#### 数据库配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | 是 | - | MySQL连接串 |
| `DB_PASSWORD` | 是 | - | MySQL root密码 |
| `DB_POOL_SIZE` | 否 | 10 | 连接池大小 |
| `DB_MAX_OVERFLOW` | 否 | 20 | 最大溢出连接 |

#### Redis配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `REDIS_URL` | 否 | redis://redis:6379/0 | Redis连接串 |
| `REDIS_PASSWORD` | 是 | - | Redis密码 |

#### Celery配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CELERY_WORKER_CONCURRENCY` | 4 | Worker并发数 |
| `CELERY_TASK_SOFT_TIME_LIMIT` | 300 | 任务软超时（秒） |
| `CELERY_TASK_TIME_LIMIT` | 600 | 任务硬超时（秒） |

#### Milvus配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MILVUS_HOST` | milvus-standalone | Milvus主机 |
| `MILVUS_PORT` | 19530 | Milvus端口 |
| `MILVUS_COLLECTION_PREFIX` | aep_ | 集合前缀 |

#### Neo4j配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `NEO4J_URI` | 否 | bolt://neo4j:7687 | Neo4j连接URI |
| `NEO4J_PASSWORD` | 是 | - | Neo4j密码 |

#### Elasticsearch配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ES_HOSTS` | elasticsearch:9200 | ES地址 |
| `ES_INDEX_PREFIX` | aep_ | 索引前缀 |
| `ES_HEAP_MIN` | 512m | 最小堆内存 |
| `ES_HEAP_MAX` | 512m | 最大堆内存 |

#### JWT配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SECRET_KEY` | 是 | - | JWT签名密钥 |
| `ALGORITHM` | 否 | HS256 | JWT算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | 30 | 令牌有效期（分钟） |

#### 安全配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SAFETY_INPUT_CHECK_ENABLED` | true | 输入安全检测 |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | 输出安全检测 |

#### 工作流配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | 全局超时（秒） |
| `WORKFLOW_CODE_SANDBOX_TIMEOUT` | 30 | 代码节点超时（秒） |
| `WORKFLOW_CODE_MAX_OUTPUT` | 5000 | 代码节点最大输出字符数 |

### 7.2 配置文件

#### Nginx配置

位置: `nginx/nginx.conf`

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Docker Compose配置

位置: `docker-compose.yml`

支持两种profile：
- `full`: 所有服务自托管
- `external-db`: 仅应用 + Neo4j（外部基础设施）

---

## 8. 开发指南

### 8.1 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 运行测试
pytest
pytest tests/unit -v
pytest tests/integration -v

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "description"
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm test

# 代码检查
npm run lint
```

### 8.2 代码规范

#### Python规范

- **缩进**: 4个空格，无制表符
- **风格**: 遵循PEEP 8，使用类型提示
- **命名**: `snake_case`（函数/变量），`PascalCase`（类），`UPPER_SNAKE_CASE`（常量）
- **异步**: 优先使用`async/await`
- **导入**: 分组为标准库 → 第三方库 → 本地模块

#### TypeScript规范

- **缩进**: 2个空格
- **风格**: 遵循ESLint配置，使用TypeScript严格模式
- **命名**: `PascalCase`（组件/类型），`camelCase`（函数/变量），`UPPER_SNAKE_CASE`（常量）
- **状态**: 使用Zustand store管理共享状态
- **样式**: 使用CSS变量（`var(--ae-*)`）

### 8.3 测试指南

#### 后端测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

#### 前端测试

```bash
# 运行测试
npm test

# 运行测试并生成覆盖率
npm test -- --coverage

# 监视模式
npm test -- --watch
```

### 8.4 提交规范

遵循Conventional Commits：

```
<type>(<scope>): <short summary>
```

**类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `refactor`: 重构
- `docs`: 文档
- `test`: 测试
- `chore`: 构建/工具
- `perf`: 性能优化
- `ci`: CI/CD

**示例**:
```
feat(auth): add JWT refresh token rotation
fix(knowledge): resolve chunking issue with large documents
refactor(workflow): simplify node execution logic
```

---

## 9. 最佳实践

### 9.1 智能体设计

#### 系统提示词设计

```markdown
# 好的系统提示词示例
你是一个专业的客服代表，负责处理客户咨询。

## 角色定义
- 你是公司ProductX的官方客服代表
- 你的目标是帮助客户解决问题，提供优质服务
- 保持友好、专业、耐心的态度

## 能力范围
- 回答产品功能问题
- 处理订单查询
- 解决技术问题
- 收集客户反馈

## 限制
- 不处理退款（转交人工）
- 不提供法律建议
- 不透露内部信息

## 输出格式
- 使用清晰、简洁的语言
- 必要时使用列表或步骤
- 提供具体的操作指导
```

#### 工具选择

根据智能体的职责选择合适的工具：

| 场景 | 推荐工具 |
|------|---------|
| 数值计算 | `calculator` |
| 代码执行 | `code_executor` |
| 数据查询 | `db_query` |
| 文件处理 | `file_ops` |
| API调用 | `http_request` |
| 信息检索 | `web_search` |

### 9.2 知识库优化

#### 文档准备

1. **文档质量**: 确保文档内容准确、完整、最新
2. **格式规范**: 使用清晰的标题、段落、列表结构
3. **避免冗余**: 删除重复内容，保持唯一性
4. **适当分块**: 文档大小适中，便于处理

#### 分块策略选择

| 文档类型 | 推荐策略 | 分块大小 |
|---------|---------|---------|
| 技术文档 | semantic | 512 tokens |
| FAQ | fixed | 256 tokens |
| 长篇文章 | paragraph | 1024 tokens |
| 对话记录 | sentence | 128 tokens |

#### 检索模式选择

| 查询类型 | 推荐模式 | 原因 |
|---------|---------|------|
| 精确事实查询 | local | 实体聚焦，精确匹配 |
| 概念性问题 | global | 主题聚焦，全面覆盖 |
| 复杂综合查询 | hybrid | 结合两种模式的优势 |
| 简单问答 | naive | 快速、直接 |

### 9.3 工作流设计

#### 设计原则

1. **单一职责**: 每个节点只做一件事
2. **错误处理**: 为关键节点添加错误处理
3. **超时控制**: 设置合理的超时时间
4. **人工审批**: 关键决策点添加人工审批
5. **日志记录**: 记录关键节点的执行日志

#### 常见模式

```yaml
# 1. 错误处理模式
- id: "api_call"
  type: "http"
  config:
    url: "https://api.example.com/data"
    timeout: 30
  on_error:
    retry: 3
    fallback: "default_value"

# 2. 人工审批模式
- id: "approval"
  type: "human"
  config:
    approver_role: "manager"
    timeout: 3600
    on_timeout: "auto_approve"

# 3. 并行处理模式
- id: "parallel_tasks"
  type: "parallel"
  branches:
    - id: "task_1"
      type: "llm"
    - id: "task_2"
      type: "http"
    - id: "task_3"
      type: "code"
```

### 9.4 性能优化

#### 数据库优化

1. **索引优化**: 为常用查询字段添加索引
2. **连接池**: 合理配置连接池大小
3. **查询优化**: 避免N+1查询，使用批量操作
4. **缓存**: 使用Redis缓存热点数据

#### 模型调用优化

1. **批量处理**: 合并多个请求为批量调用
2. **缓存结果**: 缓存相同查询的结果
3. **流式响应**: 使用SSE流式响应减少延迟
4. **模型选择**: 根据任务复杂度选择合适的模型

#### 前端优化

1. **代码分割**: 使用Next.js动态导入
2. **图片优化**: 使用Next.js Image组件
3. **缓存策略**: 合理使用浏览器缓存
4. **懒加载**: 延迟加载非关键资源

### 9.5 安全最佳实践

#### 密钥管理

1. **环境变量**: 所有密钥通过环境变量配置
2. **密钥轮换**: 定期轮换密钥
3. **最小权限**: 只授予必要的权限
4. **加密存储**: 敏感数据加密存储

#### 输入验证

1. **参数验证**: 验证所有输入参数
2. **长度限制**: 设置合理的输入长度限制
3. **类型检查**: 验证输入数据类型
4. **特殊字符**: 过滤或转义特殊字符

#### 访问控制

1. **认证**: 所有API需要认证
2. **授权**: 基于角色的访问控制
3. **审计**: 记录所有敏感操作
4. **限流**: 防止API滥用

---

## 10. 故障排除

### 10.1 常见问题

#### Backend启动失败: "SECRET_KEY must be changed"

**原因**: `.env`中`SECRET_KEY`或`ENCRYPTION_KEY`仍为默认值。

**解决**:
```bash
# 生成新密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 更新.env
SECRET_KEY=<新生成的密钥>
ENCRYPTION_KEY=<新生成的密钥>

# 重启服务
docker-compose restart backend celery-worker celery-beat
```

#### Milvus健康检查超时

**原因**: Milvus首次启动需要90秒以上。

**解决**:
```bash
# 查看日志
docker-compose logs milvus-standalone --tail 50

# 健康检查
curl http://localhost:9091/healthz

# 如果持续失败，重置数据
docker-compose down
docker volume rm agent-engine-platform_milvus_data
docker-compose up -d milvus-standalone
```

#### MySQL连接被拒

**原因**: 密码错误或MySQL未就绪。

**解决**:
```bash
# 检查MySQL状态
docker-compose exec mysql mysqladmin ping -h localhost -uroot -p"${MYSQL_ROOT_PASSWORD}"

# 如果密码错误，重置
docker-compose down
docker volume rm agent-engine-platform_mysql_data
# 修改.env中的MYSQL_ROOT_PASSWORD和DATABASE_URL
docker-compose up -d
```

#### Celery Worker无法连接Redis

**原因**: Redis未就绪或密码错误。

**解决**:
```bash
# 检查Redis状态
docker-compose exec redis redis-cli -a "${REDIS_PASSWORD}" ping

# 查看Celery日志
docker-compose logs celery-worker --tail 20

# 确认REDIS_URL配置正确
```

#### Elasticsearch内存不足

**原因**: ES默认堆内存512m可能不足。

**解决**:
```yaml
# 编辑docker-compose.yml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

#### 前端白屏 / API 502

**原因**: Nginx配置错误或后端未就绪。

**解决**:
```bash
# 检查Nginx配置
docker-compose exec nginx nginx -t

# 检查后端状态
docker-compose ps backend
curl http://localhost:8000/health

# 查看Nginx日志
docker-compose logs nginx --tail 50
```

### 10.2 性能问题

#### 响应延迟高

**可能原因**:
1. 数据库查询慢
2. 模型调用延迟
3. 网络延迟

**排查步骤**:
```bash
# 1. 检查数据库慢查询
docker-compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SHOW PROCESSLIST;"

# 2. 检查Redis延迟
docker-compose exec redis redis-cli --latency

# 3. 检查后端日志
docker-compose logs backend --tail 100

# 4. 检查系统资源
docker stats --no-stream
```

#### 内存使用过高

**可能原因**:
1. 连接池过大
2. 缓存未清理
3. 内存泄漏

**解决**:
```bash
# 1. 调整连接池
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# 2. 清理Redis缓存
docker-compose exec redis redis-cli FLUSHDB

# 3. 重启服务
docker-compose restart
```

### 10.3 数据问题

#### 知识库检索无结果

**可能原因**:
1. 文档未正确索引
2. 向量化失败
3. 检索配置错误

**排查步骤**:
```bash
# 1. 检查文档状态
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/knowledge/{kb_id}/documents

# 2. 检查Milvus集合
docker-compose exec milvus-standalone curl \
  http://localhost:9091/collections

# 3. 测试检索
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试查询", "top_k": 5}' \
  http://localhost:8000/api/v1/knowledge/{kb_id}/search
```

#### 工作流执行失败

**可能原因**:
1. 节点配置错误
2. 依赖服务不可用
3. 超时

**排查步骤**:
```bash
# 1. 查看工作流执行日志
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/workflows/{workflow_id}/executions

# 2. 检查节点执行详情
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/workflows/{workflow_id}/executions/{execution_id}

# 3. 验证依赖服务
curl http://localhost:8000/health
```

### 10.4 日志查看

#### 应用日志

```bash
# 后端日志
docker-compose logs -f backend --tail 100

# Celery日志
docker-compose logs -f celery-worker --tail 100

# 前端日志
docker-compose logs -f frontend --tail 100
```

#### 系统日志

```bash
# Nginx日志
docker-compose logs -f nginx --tail 100

# MySQL日志
docker-compose logs -f mysql --tail 100

# Redis日志
docker-compose logs -f redis --tail 100
```

### 10.5 联系支持

如果以上方法无法解决问题：

1. **查看文档**: [docs/](docs/)
2. **提交Issue**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
3. **查看源码**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| Agent | AI智能体，能够自主执行任务的AI系统 |
| RAG | 检索增强生成，结合检索和生成的技术 |
| LLM | 大语言模型，如GPT-4、Claude等 |
| DAG | 有向无环图，工作流的执行结构 |
| SSE | 服务器发送事件，用于流式响应 |
| RBAC | 基于角色的访问控制 |
| PII | 个人身份信息 |
| MCP | 模型上下文协议 |

### B. 参考资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Next.js文档](https://nextjs.org/docs)
- [Milvus文档](https://milvus.io/docs)
- [Neo4j文档](https://neo4j.com/docs/)
- [Elasticsearch文档](https://www.elastic.co/guide/)

### C. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.0 | 2026-06-01 | 初始版本 |

---

**文档维护**: 本文档由Agent Engine Platform团队维护，如有问题或建议，请提交Issue。

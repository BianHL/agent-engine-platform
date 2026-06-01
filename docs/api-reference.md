# Agent Engine Platform API 参考手册

> **版本**: v3.0  
> **更新日期**: 2026-06-01  
> **Base URL**: `/api/v1`

---

## 目录

- [1. 认证](#1-认证)
- [2. 智能体管理](#2-智能体管理)
- [3. 对话管理](#3-对话管理)
- [4. 知识库管理](#4-知识库管理)
- [5. 工作流管理](#5-工作流管理)
- [6. 模型管理](#6-模型管理)
- [7. 工具管理](#7-工具管理)
- [8. 用户管理](#8-用户管理)
- [9. 租户管理](#9-租户管理)
- [10. 审计日志](#10-审计日志)
- [11. 系统管理](#11-系统管理)

---

## 1. 认证

### 1.1 用户登录

**POST** `/auth/login`

用户登录并获取访问令牌。

#### 请求体

```json
{
  "username": "string",  // 用户名
  "password": "string"   // 密码
}
```

#### 响应

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 错误响应

```json
{
  "code": 401,
  "message": "用户名或密码错误"
}
```

#### 示例

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 1.2 刷新令牌

**POST** `/auth/refresh`

使用刷新令牌获取新的访问令牌。

#### 请求体

```json
{
  "refresh_token": "string"  // 刷新令牌
}
```

#### 响应

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 1.3 用户注册

**POST** `/auth/register`

注册新用户。

#### 请求体

```json
{
  "username": "string",      // 用户名（3-50字符）
  "password": "string",      // 密码（至少8位）
  "email": "string",         // 邮箱
  "full_name": "string",     // 全名
  "tenant_id": "string"      // 租户ID（可选）
}
```

#### 响应

```json
{
  "id": "user_123",
  "username": "newuser",
  "email": "newuser@example.com",
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 1.4 用户登出

**POST** `/auth/logout`

使当前令牌失效。

#### 请求头

```
Authorization: Bearer <access_token>
```

#### 响应

```json
{
  "message": "登出成功"
}
```

---

## 2. 智能体管理

### 2.1 创建智能体

**POST** `/agents`

创建新的AI智能体。

#### 请求头

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "string",                    // 智能体名称（必填）
  "description": "string",             // 描述
  "model_id": "string",                // 模型ID（必填）
  "system_prompt": "string",           // 系统提示词
  "tools": ["string"],                 // 工具列表
  "knowledge_bases": ["string"],       // 知识库ID列表
  "temperature": 0.7,                  // 生成温度（0-2）
  "max_tokens": 4096,                  // 最大token数
  "top_p": 1.0,                        // Top-p采样
  "frequency_penalty": 0.0,            // 频率惩罚
  "presence_penalty": 0.0,             // 存在惩罚
  "metadata": {}                       // 元数据
}
```

#### 响应

```json
{
  "id": "agent_123",
  "name": "客服助手",
  "description": "处理客户咨询的AI助手",
  "model_id": "gpt-4o",
  "status": "draft",
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T10:00:00Z"
}
```

### 2.2 获取智能体列表

**GET** `/agents`

获取智能体列表，支持分页和筛选。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `status` | string | - | 状态筛选 (draft/published/archived) |
| `search` | string | - | 搜索关键词 |
| `sort_by` | string | created_at | 排序字段 |
| `sort_order` | string | desc | 排序方式 (asc/desc) |

#### 响应

```json
{
  "items": [
    {
      "id": "agent_123",
      "name": "客服助手",
      "description": "处理客户咨询的AI助手",
      "model_id": "gpt-4o",
      "status": "published",
      "created_at": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### 2.3 获取智能体详情

**GET** `/agents/{agent_id}`

获取指定智能体的详细信息。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string | 智能体ID |

#### 响应

```json
{
  "id": "agent_123",
  "name": "客服助手",
  "description": "处理客户咨询的AI助手",
  "model_id": "gpt-4o",
  "system_prompt": "你是一个专业的客服代表...",
  "tools": ["calculator", "web_search"],
  "knowledge_bases": ["kb_456"],
  "temperature": 0.7,
  "max_tokens": 4096,
  "status": "published",
  "version": 3,
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T12:00:00Z",
  "metadata": {
    "category": "customer_service",
    "language": "zh-CN"
  }
}
```

### 2.4 更新智能体

**PUT** `/agents/{agent_id}`

更新智能体配置。

#### 请求体

```json
{
  "name": "string",
  "description": "string",
  "system_prompt": "string",
  "tools": ["string"],
  "knowledge_bases": ["string"],
  "temperature": 0.7,
  "max_tokens": 4096,
  "metadata": {}
}
```

#### 响应

```json
{
  "id": "agent_123",
  "name": "更新后的名称",
  "updated_at": "2026-06-01T13:00:00Z"
}
```

### 2.5 删除智能体

**DELETE** `/agents/{agent_id}`

删除指定智能体。

#### 响应

```json
{
  "message": "智能体已删除"
}
```

### 2.6 发布智能体

**POST** `/agents/{agent_id}/publish`

将智能体从草稿状态发布为可用状态。

#### 响应

```json
{
  "id": "agent_123",
  "status": "published",
  "published_at": "2026-06-01T14:00:00Z"
}
```

### 2.7 归档智能体

**POST** `/agents/{agent_id}/archive`

归档智能体，使其不可用。

#### 响应

```json
{
  "id": "agent_123",
  "status": "archived",
  "archived_at": "2026-06-01T15:00:00Z"
}
```

### 2.8 获取智能体版本历史

**GET** `/agents/{agent_id}/versions`

获取智能体的版本历史。

#### 响应

```json
{
  "versions": [
    {
      "version": 3,
      "created_at": "2026-06-01T12:00:00Z",
      "created_by": "user_123",
      "changes": "更新了系统提示词"
    },
    {
      "version": 2,
      "created_at": "2026-06-01T10:00:00Z",
      "created_by": "user_123",
      "changes": "添加了web_search工具"
    }
  ]
}
```

---

## 3. 对话管理

### 3.1 发送对话（同步）

**POST** `/chat/completions`

发送对话消息并获取响应。

#### 请求头

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 请求体

```json
{
  "agent_id": "string",               // 智能体ID（必填）
  "messages": [                       // 消息列表（必填）
    {
      "role": "user",                 // 角色 (user/assistant/system)
      "content": "string"             // 内容
    }
  ],
  "stream": false,                    // 是否流式响应
  "temperature": 0.7,                 // 覆盖智能体的温度设置
  "max_tokens": 4096,                 // 覆盖智能体的max_tokens
  "conversation_id": "string"         // 会话ID（可选，用于继续对话）
}
```

#### 响应

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1685670000,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么可以帮助你的吗？"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  },
  "conversation_id": "conv_789"
}
```

### 3.2 发送对话（流式）

**POST** `/chat/completions`

发送对话消息并获取流式响应（SSE）。

#### 请求体

```json
{
  "agent_id": "string",
  "messages": [...],
  "stream": true
}
```

#### 响应（SSE流）

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### 3.3 获取会话列表

**GET** `/conversations`

获取用户的会话列表。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `agent_id` | string | - | 智能体ID筛选 |

#### 响应

```json
{
  "items": [
    {
      "id": "conv_789",
      "agent_id": "agent_123",
      "title": "客服咨询",
      "last_message": "感谢您的帮助！",
      "message_count": 12,
      "created_at": "2026-06-01T10:00:00Z",
      "updated_at": "2026-06-01T10:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "size": 20
}
```

### 3.4 获取会话详情

**GET** `/conversations/{conversation_id}`

获取指定会话的详细信息和消息历史。

#### 响应

```json
{
  "id": "conv_789",
  "agent_id": "agent_123",
  "title": "客服咨询",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "你好，我想咨询一下产品功能",
      "created_at": "2026-06-01T10:00:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "你好！很高兴为您服务。请问你想了解哪些产品功能？",
      "created_at": "2026-06-01T10:00:05Z"
    }
  ],
  "metadata": {
    "total_tokens": 1500,
    "total_cost": 0.05
  },
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T10:30:00Z"
}
```

### 3.5 删除会话

**DELETE** `/conversations/{conversation_id}`

删除指定会话。

#### 响应

```json
{
  "message": "会话已删除"
}
```

### 3.6 会话反馈

**POST** `/conversations/{conversation_id}/feedback`

为会话提交反馈。

#### 请求体

```json
{
  "rating": 5,                    // 评分（1-5）
  "comment": "string",            // 评论
  "helpful": true                 // 是否有帮助
}
```

#### 响应

```json
{
  "message": "反馈已提交"
}
```

---

## 4. 知识库管理

### 4.1 创建知识库

**POST** `/knowledge`

创建新的知识库。

#### 请求体

```json
{
  "name": "string",                // 知识库名称（必填）
  "description": "string",         // 描述
  "embedding_model": "string",     // 嵌入模型（默认text-embedding-3-small）
  "chunk_size": 512,               // 分块大小
  "chunk_overlap": 50,             // 分块重叠
  "chunk_strategy": "semantic",    // 分块策略 (fixed/sentence/paragraph/semantic)
  "metadata": {}                   // 元数据
}
```

#### 响应

```json
{
  "id": "kb_456",
  "name": "产品文档",
  "description": "产品功能和使用说明",
  "document_count": 0,
  "status": "ready",
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 4.2 获取知识库列表

**GET** `/knowledge`

获取知识库列表。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `search` | string | - | 搜索关键词 |

#### 响应

```json
{
  "items": [
    {
      "id": "kb_456",
      "name": "产品文档",
      "description": "产品功能和使用说明",
      "document_count": 25,
      "status": "ready",
      "created_at": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20
}
```

### 4.3 上传文档

**POST** `/knowledge/{kb_id}/documents`

上传文档到知识库。

#### 请求头

```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 请求体

```
file: <document.pdf>                // 文件（必填）
metadata: {"category": "string"}   // 元数据（可选）
```

#### 响应

```json
{
  "id": "doc_789",
  "knowledge_base_id": "kb_456",
  "filename": "product_manual.pdf",
  "status": "processing",
  "file_size": 1024000,
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 4.4 获取文档列表

**GET** `/knowledge/{kb_id}/documents`

获取知识库中的文档列表。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `status` | string | - | 状态筛选 (processing/ready/failed) |

#### 响应

```json
{
  "items": [
    {
      "id": "doc_789",
      "filename": "product_manual.pdf",
      "status": "ready",
      "chunk_count": 150,
      "file_size": 1024000,
      "processed_at": "2026-06-01T10:05:00Z",
      "created_at": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "size": 20
}
```

### 4.5 删除文档

**DELETE** `/knowledge/{kb_id}/documents/{doc_id}`

删除指定文档。

#### 响应

```json
{
  "message": "文档已删除"
}
```

### 4.6 知识库检索

**POST** `/knowledge/{kb_id}/search`

在知识库中检索相关内容。

#### 请求体

```json
{
  "query": "string",                // 查询内容（必填）
  "top_k": 5,                       // 返回结果数量
  "mode": "hybrid",                 // 检索模式 (naive/local/global/hybrid)
  "filters": {                      // 过滤条件
    "metadata.category": "string"
  },
  "rerank": true                    // 是否重排序
}
```

#### 响应

```json
{
  "results": [
    {
      "content": "产品功能介绍...",
      "score": 0.95,
      "metadata": {
        "document_id": "doc_789",
        "chunk_index": 10,
        "source": "product_manual.pdf"
      }
    }
  ],
  "query_embedding_time": 50,
  "search_time": 100,
  "total_results": 150
}
```

### 4.7 知识库统计

**GET** `/knowledge/{kb_id}/stats`

获取知识库的统计信息。

#### 响应

```json
{
  "document_count": 25,
  "chunk_count": 1500,
  "total_size": 51200000,
  "status_distribution": {
    "ready": 20,
    "processing": 3,
    "failed": 2
  },
  "last_updated": "2026-06-01T10:00:00Z"
}
```

---

## 5. 工作流管理

### 5.1 创建工作流

**POST** `/workflows`

创建新的工作流。

#### 请求体

```json
{
  "name": "string",                    // 工作流名称（必填）
  "description": "string",             // 描述
  "nodes": [                           // 节点列表（必填）
    {
      "id": "string",                  // 节点ID
      "type": "string",                // 节点类型 (llm/condition/parallel/loop/http/code/human/sub_workflow)
      "name": "string",                // 节点名称
      "config": {},                    // 节点配置
      "next": "string",                // 下一个节点ID
      "on_error": "string"             // 错误处理节点ID
    }
  ],
  "edges": [                           // 边列表（可选，用于可视化）
    {
      "source": "string",
      "target": "string",
      "label": "string"
    }
  ],
  "variables": {                       // 变量定义
    "input_var": {
      "type": "string",
      "description": "输入变量",
      "required": true
    }
  },
  "timeout": 300,                      // 全局超时（秒）
  "metadata": {}                       // 元数据
}
```

#### 响应

```json
{
  "id": "wf_123",
  "name": "客户服务流程",
  "status": "draft",
  "version": 1,
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 5.2 获取工作流列表

**GET** `/workflows`

获取工作流列表。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `status` | string | - | 状态筛选 |
| `search` | string | - | 搜索关键词 |

#### 响应

```json
{
  "items": [
    {
      "id": "wf_123",
      "name": "客户服务流程",
      "description": "处理客户服务请求的工作流",
      "status": "published",
      "version": 3,
      "node_count": 8,
      "created_at": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "size": 20
}
```

### 5.3 获取工作流详情

**GET** `/workflows/{workflow_id}`

获取工作流的详细信息。

#### 响应

```json
{
  "id": "wf_123",
  "name": "客户服务流程",
  "description": "处理客户服务请求的工作流",
  "nodes": [...],
  "edges": [...],
  "variables": {...},
  "status": "published",
  "version": 3,
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T12:00:00Z"
}
```

### 5.4 更新工作流

**PUT** `/workflows/{workflow_id}`

更新工作流配置。

#### 请求体

```json
{
  "name": "string",
  "description": "string",
  "nodes": [...],
  "edges": [...],
  "variables": {...},
  "timeout": 300
}
```

#### 响应

```json
{
  "id": "wf_123",
  "name": "更新后的名称",
  "version": 4,
  "updated_at": "2026-06-01T13:00:00Z"
}
```

### 5.5 执行工作流

**POST** `/workflows/{workflow_id}/execute`

执行工作流。

#### 请求体

```json
{
  "inputs": {                          // 输入变量
    "customer_query": "我的订单在哪里？"
  },
  "async": false,                      // 是否异步执行
  "callback_url": "string"             // 回调URL（异步执行时）
}
```

#### 响应（同步）

```json
{
  "execution_id": "exec_456",
  "workflow_id": "wf_123",
  "status": "completed",
  "outputs": {
    "result": "您的订单已发货，预计明天到达。"
  },
  "execution_time": 5.2,
  "node_executions": [
    {
      "node_id": "classify",
      "status": "completed",
      "duration": 1.2,
      "output": {"classification": "order_tracking"}
    }
  ],
  "created_at": "2026-06-01T10:00:00Z",
  "completed_at": "2026-06-01T10:00:05Z"
}
```

#### 响应（异步）

```json
{
  "execution_id": "exec_456",
  "workflow_id": "wf_123",
  "status": "running",
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 5.6 获取执行历史

**GET** `/workflows/{workflow_id}/executions`

获取工作流的执行历史。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `status` | string | - | 状态筛选 (running/completed/failed) |

#### 响应

```json
{
  "items": [
    {
      "execution_id": "exec_456",
      "status": "completed",
      "execution_time": 5.2,
      "created_at": "2026-06-01T10:00:00Z",
      "completed_at": "2026-06-01T10:00:05Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

### 5.7 获取执行详情

**GET** `/workflows/{workflow_id}/executions/{execution_id}`

获取工作流执行的详细信息。

#### 响应

```json
{
  "execution_id": "exec_456",
  "workflow_id": "wf_123",
  "status": "completed",
  "inputs": {"customer_query": "我的订单在哪里？"},
  "outputs": {"result": "您的订单已发货，预计明天到达。"},
  "node_executions": [...],
  "execution_time": 5.2,
  "created_at": "2026-06-01T10:00:00Z",
  "completed_at": "2026-06-01T10:00:05Z"
}
```

### 5.8 取消执行

**POST** `/workflows/{workflow_id}/executions/{execution_id}/cancel`

取消正在运行的工作流执行。

#### 响应

```json
{
  "message": "执行已取消"
}
```

---

## 6. 模型管理

### 6.1 获取模型提供商列表

**GET** `/models/providers`

获取可用的模型提供商列表。

#### 响应

```json
{
  "providers": [
    {
      "id": "provider-openai",
      "name": "OpenAI",
      "status": "active",
      "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
      "configured": true
    },
    {
      "id": "provider-anthropic",
      "name": "Anthropic",
      "status": "active",
      "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
      "configured": true
    },
    {
      "id": "provider-ollama",
      "name": "Ollama",
      "status": "active",
      "models": ["qwen2.5", "llama3"],
      "configured": false
    }
  ]
}
```

### 6.2 更新提供商配置

**PATCH** `/models/providers/{provider_id}`

更新模型提供商的配置。

#### 请求体

```json
{
  "api_key": "string",           // API密钥
  "api_base": "string",          // API基础URL（可选）
  "organization": "string",      // 组织ID（可选）
  "enabled": true                // 是否启用
}
```

#### 响应

```json
{
  "id": "provider-openai",
  "name": "OpenAI",
  "status": "active",
  "configured": true,
  "updated_at": "2026-06-01T10:00:00Z"
}
```

### 6.3 获取模型列表

**GET** `/models`

获取可用的模型列表。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `provider` | string | 提供商筛选 |
| `capability` | string | 能力筛选 (chat/embedding/vision) |

#### 响应

```json
{
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "openai",
      "capabilities": ["chat", "vision", "function_calling"],
      "context_window": 128000,
      "pricing": {
        "input": 0.005,
        "output": 0.015
      }
    }
  ]
}
```

### 6.4 模型对比

**POST** `/models/compare`

对比多个模型的响应。

#### 请求体

```json
{
  "models": ["gpt-4o", "claude-3-opus"],
  "messages": [
    {"role": "user", "content": "解释量子计算"}
  ],
  "metrics": ["latency", "token_usage", "quality"]
}
```

#### 响应

```json
{
  "comparisons": [
    {
      "model": "gpt-4o",
      "response": "量子计算是...",
      "latency": 1.2,
      "token_usage": 150,
      "quality_score": 0.92
    },
    {
      "model": "claude-3-opus",
      "response": "量子计算是一种...",
      "latency": 1.5,
      "token_usage": 180,
      "quality_score": 0.95
    }
  ]
}
```

### 6.5 使用统计

**GET** `/usage`

获取模型使用统计。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `start_date` | string | - | 开始日期 (YYYY-MM-DD) |
| `end_date` | string | - | 结束日期 |
| `model` | string | - | 模型筛选 |
| `group_by` | string | day | 分组方式 (day/week/month) |

#### 响应

```json
{
  "summary": {
    "total_requests": 10000,
    "total_tokens": 5000000,
    "total_cost": 150.50
  },
  "timeline": [
    {
      "date": "2026-06-01",
      "requests": 500,
      "tokens": 250000,
      "cost": 7.50
    }
  ],
  "by_model": [
    {
      "model": "gpt-4o",
      "requests": 8000,
      "tokens": 4000000,
      "cost": 120.00
    }
  ]
}
```

---

## 7. 工具管理

### 7.1 获取工具列表

**GET** `/tools`

获取可用工具列表。

#### 响应

```json
{
  "tools": [
    {
      "name": "calculator",
      "description": "数学表达式计算",
      "parameters": {
        "expression": {
          "type": "string",
          "description": "数学表达式"
        }
      },
      "builtin": true
    },
    {
      "name": "web_search",
      "description": "网络搜索",
      "parameters": {
        "query": {
          "type": "string",
          "description": "搜索查询"
        },
        "num_results": {
          "type": "integer",
          "description": "结果数量",
          "default": 5
        }
      },
      "builtin": true
    }
  ]
}
```

### 7.2 注册自定义工具

**POST** `/tools`

注册自定义工具。

#### 请求体

```json
{
  "name": "string",                    // 工具名称（必填）
  "description": "string",             // 描述（必填）
  "parameters": {                      // 参数定义（必填）
    "param1": {
      "type": "string",
      "description": "参数说明",
      "required": true
    }
  },
  "endpoint": "string",                // HTTP端点
  "method": "POST",                    // HTTP方法
  "headers": {},                       // 请求头
  "timeout": 30                        // 超时（秒）
}
```

#### 响应

```json
{
  "name": "custom_tool",
  "description": "自定义工具",
  "status": "active",
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 7.3 测试工具

**POST** `/tools/{tool_name}/test`

测试工具调用。

#### 请求体

```json
{
  "parameters": {
    "param1": "value1"
  }
}
```

#### 响应

```json
{
  "success": true,
  "result": "工具执行结果",
  "execution_time": 0.5
}
```

### 7.4 删除工具

**DELETE** `/tools/{tool_name}`

删除自定义工具。

#### 响应

```json
{
  "message": "工具已删除"
}
```

---

## 8. 用户管理

### 8.1 获取用户列表

**GET** `/users`

获取用户列表（需要管理员权限）。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `role` | string | - | 角色筛选 |
| `tenant_id` | string | - | 租户筛选 |

#### 响应

```json
{
  "items": [
    {
      "id": "user_123",
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "管理员",
      "role": "admin",
      "status": "active",
      "last_login": "2026-06-01T10:00:00Z",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20
}
```

### 8.2 获取用户详情

**GET** `/users/{user_id}`

获取用户详细信息。

#### 响应

```json
{
  "id": "user_123",
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "管理员",
  "role": "admin",
  "tenant_id": "tenant_001",
  "status": "active",
  "last_login": "2026-06-01T10:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "metadata": {
    "department": "技术部"
  }
}
```

### 8.3 更新用户

**PUT** `/users/{user_id}`

更新用户信息。

#### 请求体

```json
{
  "email": "string",
  "full_name": "string",
  "role": "string",
  "status": "string",
  "password": "string"
}
```

#### 响应

```json
{
  "id": "user_123",
  "username": "admin",
  "email": "newemail@example.com",
  "updated_at": "2026-06-01T10:00:00Z"
}
```

### 8.4 删除用户

**DELETE** `/users/{user_id}`

删除用户。

#### 响应

```json
{
  "message": "用户已删除"
}
```

---

## 9. 租户管理

### 9.1 创建租户

**POST** `/tenants`

创建新租户。

#### 请求体

```json
{
  "name": "string",                    // 租户名称（必填）
  "description": "string",             // 描述
  "quota": {                           // 资源配额
    "max_users": 100,
    "max_agents": 50,
    "max_storage_gb": 100
  },
  "settings": {}                       // 租户设置
}
```

#### 响应

```json
{
  "id": "tenant_001",
  "name": "示例租户",
  "status": "active",
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 9.2 获取租户列表

**GET** `/tenants`

获取租户列表。

#### 响应

```json
{
  "items": [
    {
      "id": "tenant_001",
      "name": "示例租户",
      "user_count": 25,
      "agent_count": 10,
      "status": "active",
      "created_at": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 20
}
```

### 9.3 更新租户

**PUT** `/tenants/{tenant_id}`

更新租户信息。

#### 请求体

```json
{
  "name": "string",
  "description": "string",
  "quota": {},
  "settings": {}
}
```

#### 响应

```json
{
  "id": "tenant_001",
  "name": "更新后的名称",
  "updated_at": "2026-06-01T10:00:00Z"
}
```

### 9.4 删除租户

**DELETE** `/tenants/{tenant_id}`

删除租户。

#### 响应

```json
{
  "message": "租户已删除"
}
```

---

## 10. 审计日志

### 10.1 获取审计日志

**GET** `/audit`

获取审计日志。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `size` | integer | 20 | 每页数量 |
| `action` | string | - | 操作类型筛选 |
| `user_id` | string | - | 用户ID筛选 |
| `resource_type` | string | - | 资源类型筛选 |
| `start_date` | string | - | 开始日期 |
| `end_date` | string | - | 结束日期 |

#### 响应

```json
{
  "items": [
    {
      "id": "audit_001",
      "action": "user.login",
      "user_id": "user_123",
      "username": "admin",
      "resource_type": "auth",
      "resource_id": null,
      "details": {
        "ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
      },
      "timestamp": "2026-06-01T10:00:00Z"
    }
  ],
  "total": 1000,
  "page": 1,
  "size": 20
}
```

### 10.2 审计日志统计

**GET** `/audit/stats`

获取审计日志统计。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `start_date` | string | - | 开始日期 |
| `end_date` | string | - | 结束日期 |
| `group_by` | string | day | 分组方式 (day/week/month) |

#### 响应

```json
{
  "summary": {
    "total_events": 5000,
    "unique_users": 25,
    "top_actions": [
      {"action": "user.login", "count": 1000},
      {"action": "agent.create", "count": 500}
    ]
  },
  "timeline": [
    {
      "date": "2026-06-01",
      "events": 250,
      "users": 15
    }
  ]
}
```

---

## 11. 系统管理

### 11.1 健康检查

**GET** `/health`

检查系统健康状态。

#### 响应

```json
{
  "status": "ok",
  "timestamp": "2026-06-01T10:00:00Z",
  "components": {
    "database": {
      "status": "ok",
      "latency": 5
    },
    "redis": {
      "status": "ok",
      "latency": 2
    },
    "milvus": {
      "status": "ok",
      "latency": 10
    },
    "neo4j": {
      "status": "ok",
      "latency": 8
    },
    "elasticsearch": {
      "status": "ok",
      "latency": 15
    }
  }
}
```

### 11.2 系统信息

**GET** `/system/info`

获取系统信息。

#### 响应

```json
{
  "version": "3.0.0",
  "environment": "production",
  "uptime": 86400,
  "python_version": "3.11.0",
  "database_version": "8.0.30",
  "redis_version": "7.0.0",
  "milvus_version": "2.4.0",
  "neo4j_version": "5.0.0",
  "elasticsearch_version": "8.12.0"
}
```

### 11.3 任务状态

**GET** `/tasks`

获取Celery任务状态。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `status` | string | - | 状态筛选 (pending/running/completed/failed) |
| `task_type` | string | - | 任务类型筛选 |

#### 响应

```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "task_type": "document_processing",
      "status": "completed",
      "progress": 100,
      "result": {...},
      "created_at": "2026-06-01T10:00:00Z",
      "completed_at": "2026-06-01T10:05:00Z"
    }
  ],
  "summary": {
    "pending": 5,
    "running": 2,
    "completed": 100,
    "failed": 3
  }
}
```

### 11.4 Webhook管理

#### 创建Webhook

**POST** `/webhooks`

```json
{
  "name": "string",
  "url": "string",
  "events": ["agent.created", "workflow.completed"],
  "secret": "string",
  "active": true
}
```

#### 获取Webhook列表

**GET** `/webhooks`

#### 删除Webhook

**DELETE** `/webhooks/{webhook_id}`

#### 测试Webhook

**POST** `/webhooks/{webhook_id}/test`

---

## 错误码参考

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 请求体验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 速率限制

- 默认限制: 60次/分钟
- 登录限制: 5次/分钟
- 可通过环境变量配置: `RATE_LIMIT_PER_MINUTE`

---

**文档维护**: 本文档由Agent Engine Platform团队维护，如有问题或建议，请提交Issue。

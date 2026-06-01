# OpenCode 借镜分析：基于代码验证

> 日期: 2026-06-01
> 方法: 逐项对照后端代码，验证 opencode-analysis.md 中的每条差距

---

## 代码验证结果

### 1. Agent 模型字段

| 字段 | OpenCode | 当前代码 (`models/agent.py`) | 差距? |
|------|----------|--------------------------|-------|
| `mode` (primary/subagent/all) | ✅ | ❌ 无 | **有** |
| `steps` (最大迭代步数) | ✅ | ❌ 无 | **有** |
| `permission` (独立权限规则) | ✅ | ❌ 无 | **有** |
| `hidden` (子Agent可见性) | ✅ | ❌ 无 | **有** |
| `temperature/model_config` | ✅ | ✅ `model_config` JSON | 无 |
| `tools` | ✅ | ✅ `tools` JSON list | 无 |

**结论**: 4 个字段缺失属实。但 **项目定位不同** — 当前平台是 SaaS 多租户平台，不是终端工具。`mode`/`hidden` 主要为 CLI Agent 设计；`steps` 限制对 SaaS 有价值。

---

### 2. 权限系统 (Permission)

| 维度 | OpenCode | 当前代码 (`core/rbac.py`) | 差距? |
|------|----------|----------------------|-------|
| API 端点 RBAC | ❌ (无) | ✅ 细粒度 resource:action | 平台领先 |
| Agent 工具调用权限 | ✅ Ruleset 引擎 | ❌ ToolExecutor 只检查工具名 | **有** |
| 文件操作 glob 规则 | ✅ `*.ts` 匹配 | ❌ 无 | N/A（平台无文件系统） |
| 用户交互确认 (ask) | ✅ once/always/reject | ❌ 无 | 见下文判定 |

**结论**: OpenCode 的 Permission 是 **终端Agent专用**（文件读写、命令执行需用户确认）。当前平台是后端服务，**无本地文件系统操作**，glob 规则和用户确认机制 **不适用**。但"Agent 工具调用权限白名单"概念可移植。

---

### 3. Provider 模型元数据

| 字段 | OpenCode | 当前代码 (`models/system.py`) | 差距? |
|------|----------|--------------------------|-------|
| 模型能力标记 | `attachment/reasoning/tool_call` | ✅ `supports_function_calling`/`supports_vision` | **部分有** |
| 成本模型 | `cost.input/output/cache_*` | ✅ `input_price_per_k`/`output_price_per_k` | **部分有** |
| 缓存成本 | `cache_read/cache_write` | ❌ 无 | **有** |
| 模态声明 | `modalities.input/output` | ❌ 无 | **有** |
| 上下文窗口 | `limit.context` | ✅ `max_context_tokens` | 无 |

**结论**: 基础字段已有。缺 缓存成本 和 模态声明。`UsageLogModel` 有 `cached_tokens` 字段，说明架构预留了缓存追踪但定价缺失。

---

### 4. Skill 系统

| 维度 | OpenCode | 当前平台 | 判定 |
|------|----------|---------|------|
| SKILL.md 自动发现 | ✅ glob `**/*.SKILL.md` | ❌ 无 | 见下文 |
| 工具是代码级注册 | ❌ | ✅ `ToolRegistry` | 平台方式合理 |

**结论**: OpenCode 的 Skill 是为**开发者自定义 Claude Code 行为**设计。当前平台的 Tool 系统服务于**终端用户的 Agent 配置**。场景完全不同。

---

### 5. 会话 Compaction

| 维度 | OpenCode | 当前代码 | 差距? |
|------|----------|---------|-------|
| 消息压缩 | ✅ LLM 摘要 | ✅ `SummarizationPipeline._summarize_messages()` | **已实现!** |
| 工作记忆压缩 | — | ✅ `WorkingMemory.compress()` | **已实现!** |
| 阈值触发 | — | ✅ `threshold=20` 自动压缩 | **已实现!** |

**结论**: opencode-analysis.md 标注"无上下文压缩"是 **错误的**。当前平台的 `MemoryEngine` 已实现三层记忆 + LLM 自动压缩 + 降级摘要。**无需借用。**

---

### 6. SSE 流式保护

| 维度 | OpenCode | 当前代码 | 差距? |
|------|----------|---------|-------|
| SSE 超时保护 | ✅ `wrapSSE()` | ❌ 无 heartbeat/超时 | **有** |
| Nginx 代理超时 | — | ✅ 300s read timeout | 部分覆盖 |

**结论**: SSE 超时保护缺失属实。应用层应增加 heartbeat，不能仅依赖 Nginx。

---

### 7. 其他

| 维度 | 状态 |
|------|------|
| Tool AbortSignal | ❌ `ToolExecutor` 无 abort 参数 |
| 子会话 Fork | ❌ `ConversationModel` 无 `parent_id` |
| Agent 调试面板 | ❌ Agent 对话无 trace 可视化 |
| 消息引用知识块 | ❌ 回复无引用标记 |

---

## 借镜建议判定

### ✅ 值得借镜（与平台定位契合）

| # | 功能 | 理由 | 改造思路 | 工作量 |
|---|------|------|---------|--------|
| 1 | **Agent 步数限制** `max_steps` | 防止 Agent 无限循环消耗 token，多租户平台必须 | `AgentModel` 加 `max_steps: int` 字段，`ToolExecutor.execute_for_agent()` 加步数计数器 | 1天 |
| 2 | **SSE 超时 + Heartbeat** | 长对话断连用户体验差 | `chat_stream` 加周期性 `{"event":"ping"}` + 超时 abort | 1天 |
| 3 | **模型缓存成本** | `UsageLogModel` 已有 `cached_tokens`，缺定价字段 | `ModelConfigModel` 加 `cache_read_price`/`cache_write_price` Float | 0.5天 |
| 4 | **Agent 工具权限白名单** | 当前 `execute_for_agent()` 只检查工具名是否在列表内，加 `allow`/`deny` 规则更灵活 | `tools` JSON 从 `["tool_name"]` 扩展为 `[{"name": "...", "permission": "allow|deny|ask"}]` | 1天 |
| 5 | **Tool AbortSignal** | 用户关闭对话时应能中止进行中的工具调用 | `execute()` 加 `abort_event: Event` 参数，传给 `asyncio.wait_for` 的取消逻辑 | 0.5天 |

### ⚠️ 改造后可借镜（需要适配）

| # | 功能 | 原始设计 | 适配理由 | 适配思路 |
|---|------|---------|---------|---------|
| 6 | **Agent Mode** (primary/subagent) | CLI Agent 调度模式 | 平台的多 Agent 系统是 Crew/Handoff，不是 CLI 调度 | 不直接移植。可借鉴"主 Agent 能调用子 Agent"概念，映射到现有 Crew 系统 |
| 7 | **模型模态声明** | `modalities.input/output` 数组 | 平台即将支持多模态，需声明模型能力 | `ModelConfigModel` 加 `supported_input_types`/`supported_output_types` JSON 数组 |
| 8 | **消息引用知识块** | 回复标注知识块来源 | RAG 场景核心需求 | `MessageModel` 加 `source_chunks` JSON，存储引用的知识块 ID 和文本片段 |

### ❌ 不应借镜（与平台定位冲突）

| # | 功能 | 不借理由 |
|---|------|---------|
| 9 | **Permission glob 规则** | 平台无本地文件系统，glob 匹配无意义 |
| 10 | **Permission ask（用户确认）** | 终端交互式确认。平台是 API 服务，无终端交互 |
| 11 | **Skill (SKILL.md 发现)** | 为开发者自定义 CLI Agent 行为设计。平台 Tool 是给终端用户配置的 |
| 12 | **Agent hidden 标识** | CLI @补全可见性控制。平台 Agent 通过 RBAC 控制可见性 |
| 13 | **Agent 颜色标识** | TUI 视觉辅助。平台有独立 UI 设计系统 |
| 14 | **动态 Agent 生成（meta-prompt）** | 概念有趣但实现成本高，且平台用户通过 UI 配置 Agent，不需要 prompt 生成配置 |

---

## 修正分析文档中的错误

opencode-analysis.md 中部分判断与代码不符：

| 原文判断 | 实际代码 | 修正 |
|----------|---------|------|
| "无上下文压缩，长对话直接截断" | `SummarizationPipeline` + `WorkingMemory.compress()` + 降级摘要 | **已有三层压缩** |
| "Tool 执行前无权限检查" | `execute_for_agent()` 有工具名白名单检查 | 部分有，缺细粒度规则 |
| "ModelConfig 只有 model_name/display_name" | 有 `supports_function_calling`/`supports_vision`/`input_price_per_k`/`max_context_tokens` 等 | 基础字段较全 |

---

## 实施优先级

### P0（1-2天，立即可做）

1. **Agent max_steps** — 防 token 消耗失控
2. **SSE Heartbeat** — 改善对话体验
3. **Tool AbortSignal** — 用户取消支持

### P1（2-3天，近期规划）

4. **模型缓存成本字段** — 补齐成本追踪
5. **Agent 工具权限规则** — 从白名单升级到规则引擎
6. **消息引用知识块** — RAG 体验提升

### P2（3-5天，中期）

7. **模型模态声明** — 多模态支持前置
8. **子会话 Fork** — 对话分支探索

---

## 总结

OpenCode 的核心架构价值在于 **声明式配置 + 权限分层**，但其设计假设是 **终端编码工具**（本地文件、用户交互确认、CLI 调度）。

当前 Agent Engine Platform 定位是 **SaaS 多租户平台**，核心差距不在 OpenCode 借镜，而在：
1. **交互层**（Agent 调试面板、消息引用）
2. **成本控制**（步数限制、缓存定价）
3. **可靠性**（SSE 超时、Tool abort）

值得借镜的是 **5 个具体功能点**，不是架构哲学。总计约 **5天工作量**，与 Dify 对齐无关，纯粹提升平台质量。

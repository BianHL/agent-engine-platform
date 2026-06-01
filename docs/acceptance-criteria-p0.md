# P0 开发验收标准

> 制定日期: 2026-05-29 | 基于前端/后端优化计划

---

## 一、前端验收标准

### AC-1: Workflow 可视化 DAG 编辑器

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 1.1 | 安装 react-flow + zundo + elkjs 依赖 | `cat frontend/package.json \| grep -E "reactflow|zundo|elkjs"` 有输出 |
| 1.2 | 创建 WorkflowCanvas 组件（React Flow 画布） | 文件存在 `frontend/src/app/(platform)/workflows/[id]/edit/page.tsx` |
| 1.3 | 实现 8 种节点类型组件 | `frontend/src/components/workflow/nodes/` 下有 LLMNode/CodeNode/ConditionNode/ParallelNode/LoopNode/HTTPNode/HumanNode/SubWorkflowNode.tsx |
| 1.4 | 实现 NodePalette 拖拽面板 | 文件存在且可拖拽节点到画布 |
| 1.5 | 实现 NodeConfigPanel 配置面板 | 点击节点弹出配置表单 |
| 1.6 | 实现 Toolbar（保存/撤销/重做/运行） | 文件存在 `frontend/src/components/workflow/Toolbar/` |
| 1.7 | 实现 workflow-store（Zustand + zundo） | 文件存在 `frontend/src/store/workflow-store.ts`，含 nodes/edges/history |
| 1.8 | 与后端 API 对接（保存/加载工作流） | 调用 `api.ts` 中已有 workflow API |
| 1.9 | 所有新增文件无 TypeScript 编译错误 | `cd frontend && npx tsc --noEmit` 通过 |

### AC-2: 7 个缺失页面

| # | 页面 | 路径 | 验收项 |
|---|------|------|--------|
| 2.1 | 多 Agent 编排 | `/multi-agent` | 页面存在，含 Crew 创建/编辑/执行 UI |
| 2.2 | 评估管理 | `/evaluations` | 页面存在，含评估数据集/运行/结果展示 |
| 2.3 | 触发器管理 | `/triggers` | 页面存在，含 Cron/事件触发器 CRUD |
| 2.4 | Webhook 管理 | `/webhooks` | 页面存在，含 Webhook 端点 CRUD + 测试 |
| 2.5 | 租户管理 | `/tenants` | 页面存在，含租户列表/详情/配额设置 |
| 2.6 | 角色权限 | `/roles` | 页面存在，含角色列表/权限矩阵编辑 |
| 2.7 | 用户管理 | `/users` | 页面存在，含用户列表/创建/编辑/角色分配 |

**通用验收**: 每个页面调用对应后端 API，有 Table/Form/Modal 基础交互，无 TS 编译错误。

### AC-3: Agent 对话页重写

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 3.1 | SSE 流式对话渲染 | ChatMessage 组件支持流式文本追加 |
| 3.2 | Markdown 渲染 + 代码高亮 | 代码块有语法高亮 + 复制按钮 |
| 3.3 | 停止生成按钮 | 流式过程中显示 Stop 按钮 |
| 3.4 | 对话历史加载 | 滚动加载历史消息 |
| 3.5 | 文件 > 150 行 | `agents/[id]/chat/page.tsx` 超过 150 行 |

### AC-4: Sidebar 更新

| # | 验收项 |
|---|--------|
| 4.1 | 新增 7 个菜单项（multi-agent/evaluations/triggers/webhooks/tenants/roles/users） |
| 4.2 | 菜单项权限过滤（admin 看全部，user 看部分） |

---

## 二、后端验收标准

### AC-5: ORM 模型层重构

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 5.1 | 创建 `backend/app/models/` 目录 | 目录存在 |
| 5.2 | 按领域拆分模型文件 | 有 tenant.py/user.py/agent.py/knowledge.py/workflow.py/conversation.py/audit.py/system.py |
| 5.3 | `__init__.py` 统一导出所有模型 | `from app.models import *` 可用 |
| 5.4 | 原 base.py 仅保留 Base 类 | `backend/app/models/base.py` < 50 行 |
| 5.5 | 所有现有 import 不受影响 | `grep -r "from app.models.base" backend/` 所有引用仍可用 |
| 5.6 | 后端测试全部通过 | `cd backend && python -m pytest` 通过 |

### AC-6: Schema 层重构

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 6.1 | 创建 `backend/app/schemas/` 目录按领域拆分 | 有 agent.py/knowledge.py/workflow.py 等文件 |
| 6.2 | `__init__.py` 统一导出 | 所有现有 import 仍可用 |
| 6.3 | 原 api.py 仅保留 common schema | `backend/app/schemas/api.py` < 100 行 |
| 6.4 | 测试通过 | `pytest` 通过 |

### AC-7: JWT Token 撤销机制

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 7.1 | 实现 Redis-based Token 黑名单 | `backend/app/core/auth.py` 含 `revoke_token`/`is_token_revoked` 函数 |
| 7.2 | 登出 API 将 Token 加入黑名单 | `POST /api/v1/auth/logout` 端点存在 |
| 7.3 | 每次请求检查黑名单 | `_authenticate_token` 在 JWT 验证后检查黑名单 |
| 7.4 | 单元测试覆盖 | `test_auth.py` 含黑名单测试用例 |

### AC-8: MCP 工具扩展

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 8.1 | MCP 工具从 5 个扩展到 10+ | `backend/app/mcp/server.py` TOOL_DEFINITIONS 列表长度 >= 10 |
| 8.2 | 新增工具: update_agent/delete_agent/list_knowledge_bases/evaluate_rag/get_audit_logs/list_workflows | 对应工具定义存在 |

---

## 三、整体验收标准

| # | 验收项 | 验证方式 |
|---|--------|---------|
| G1 | 前端 TypeScript 编译通过 | `cd frontend && npx tsc --noEmit` 无错误 |
| G2 | 后端测试通过 | `cd backend && python -m pytest` 全部通过 |
| G3 | 新增文件总数 > 30 | `find frontend/src -name "*.tsx" -o -name "*.ts" \| wc -l` > 50 |
| G4 | 无 import 断链 | 所有新文件可被现有代码正确引用 |
| G5 | Sidebar 包含全部菜单项 | Sidebar.tsx menuItems.length >= 15 |

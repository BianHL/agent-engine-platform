# Dify/Coze 前端架构深度研究报告

> 研究日期：2026-05-29  
> 研究目标：为 Agent Engine Platform 前端优化提供可借鉴的技术方案

## 1. Dify 前端架构分析

### 1.1 核心技术栈

- **框架**: Next.js + TypeScript
- **工作流引擎**: React Flow (@xyflow/react)
- **状态管理**: Zustand + zundo (撤销/重做)
- **构建工具**: Vinext (开发体验增强) + Vite
- **包管理**: pnpm workspace
- **UI组件库**: @langgenius/dify-ui (自研组件库)
- **测试**: Vitest + React Testing Library
- **其他**: Immer (不可变数据)、ahooks (React hooks 工具库)

### 1.2 Workflow 编辑器实现

#### 核心依赖
```typescript
import ReactFlow, {
  Background,
  ReactFlowProvider,
  SelectionMode,
  useEdgesState,
  useNodes,
  useNodesState,
  useOnViewportChange,
  useReactFlow,
  useStoreApi,
} from 'reactflow'
```

#### 架构特点

**Provider 层级结构**
```
ReactFlowProvider
├── WorkflowHistoryProvider (撤销/重做状态)
├── DatasetsDetailProvider (数据集详情)
└── WorkflowContextProvider (工作流上下文)
```

**状态管理分层**
Dify 使用了高度模块化的 Zustand stores:
- `useWorkflowStore`: 工作流元数据、脏标志、拖拽状态
- `useCanvasStore`: 视口、网格设置、小地图、只读模式
- `usePanelStore`: 活动面板、面板栈、运行面板、设置面板
- `useEdgeStore`: 边状态 (与 React Flow 内部状态分离)
- `useInteractionStore`: 指针/平移模式、临时平移
- `useSelectionStore`: 选中的节点/边 ID
- `useRunStore`: 执行状态、每个节点的状态、进度

**节点系统**
- 统一的 `BaseNode` 包装器提供通用 UI (手柄、头部、交互)
- 30+ 节点类型: LLM, HTTP, Code, Knowledge Retrieval, IF/ELSE, Loop, Iteration, Variable Aggregator
- Hook 注入模式: UI 与执行逻辑解耦

### 1.3 关键技术特性

#### 撤销/重做系统
使用 zundo (Zustand 时间旅行):
```typescript
const { saveStateToHistory, undo, redo } = useWorkflowHistory()
```

**限制**:
- Node Panel 中的 InputChange 事件不触发状态变更
- UI 元素调整大小不触发状态变更
- 需要手动处理批量操作 (如 "organize blocks")

#### 草稿同步
```typescript
// 防抖同步
const handleSyncWorkflowDraft = useCallback(() => {
  // 同步逻辑
}, [])

// 页面关闭时的安全同步
const syncWorkflowDraftWhenPageClose = useCallback(() => {
  // sendBeacon 备份
}, [])
```

#### 性能优化
- `setAutoFreeze(false)` - 禁用 Immer 的自动冻结以提升性能
- 使用 `produce` (Immer) 进行不可变更新
- 节点组件使用 `memo` 包装
- 细粒度 store 订阅避免不必要的重渲染

### 1.4 UI/UX 设计模式

#### Z-Index 合约
- 新组件默认 `z-1002`
- Toast 系统 `z-1003` 确保通知始终可见

#### 工作流画布特性
- 对齐辅助线 (水平和垂直)
- 节点分组和嵌套支持
- 小地图导航
- 节点动画效果

#### 调试和预览面板
- 实时执行跟踪
- 变量检查器
- SSE 事件流支持
- 人工输入表单处理

### 1.5 代码组织结构

```
web/app/components/workflow/
├── index.tsx                 # 主工作流组件
├── context/                 # Context providers
├── hooks/                   # 自定义 hooks
│   ├── use-nodes-interactions.ts
│   ├── use-edges-interactions.ts
│   ├── use-nodes-sync-draft.ts
│   ├── use-panel-interactions.ts
│   └── use-workflow-history.ts
├── nodes/                   # 节点组件
│   ├── _base/              # BaseNode 组件
│   ├── llm/
│   ├── http/
│   ├── code/
│   └── ...
├── panel/                   # 配置面板
│   ├── debug-and-preview/
│   └── node-config/
└── utils/                   # 工具函数
    ├── workflow.ts
    ├── workflow-init.ts
    └── elk-layout.ts
```

## 2. Coze Studio 前端架构分析

### 2.1 核心技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Rsbuild (基于 Rspack)
- **包管理**: Rush.js + pnpm
- **状态管理**: Zustand
- **路由**: React Router v6
- **UI组件**: @coze-arch/coze-design (基于 Semi Design)
- **样式**: Tailwind CSS
- **国际化**: @coze-arch/i18n
- **工作流引擎**: FlowGram (自研, 非 React Flow)

### 2.2 Monorepo 架构

Coze 使用 135+ 前端包的分层依赖系统:

```
frontend/
├── apps/
│   └── coze-studio/         # 主应用 (Level 4)
├── packages/
│   ├── arch/                # 核心基础设施 (Level 1)
│   ├── common/              # 共享组件和工具 (Level 2)
│   ├── agent-ide/           # AI Agent 开发环境 (Level 3)
│   ├── workflow/            # 工作流引擎 (Level 3)
│   ├── studio/              # Studio 核心功能 (Level 3)
│   └── components/          # UI 组件库
└── config/                  # 配置文件
```

### 2.3 工作流引擎 (FlowGram)

与 Dify 不同，Coze 使用自研的 FlowGram 引擎:

**特点**:
- 基于 Fabric.js 的 Canvas 渲染引擎
- 自研的节点系统 (非 React Flow)
- 专门为 AI Agent 工作流优化
- 支持复杂的节点类型和连接逻辑

**架构**:
```
packages/workflow/
├── fabric-canvas/           # Canvas 渲染引擎
├── nodes/                   # 节点组件库
├── sdk/                     # Workflow SDK
└── playground/              # 调试运行时环境
```

### 2.4 架构模式

**适配器模式**: 广泛使用 `-adapter` 后缀包实现层间解耦

**Base/Core 模式**: 共享功能使用 `-base` 或 `-core` 后缀

**依赖管理**: 使用 workspace 引用 (`workspace:*`) 管理内部依赖

### 2.5 关键设计决策

1. **自研 vs 开源**: 选择自研 FlowGram 而非 React Flow，可能是为了更好的控制和优化
2. **Rsbuild vs Vite**: 使用 Rsbuild 获得更快的构建速度
3. **Rush.js**: 管理大规模 monorepo 的标准选择

## 3. React Flow 最佳实践

### 3.1 核心配置模式

```typescript
// 必要的 CSS 导入
import '@xyflow/react/dist/style.css'

// Provider 包裹
<ReactFlowProvider>
  <Workflow nodes={nodes} edges={edges} />
</ReactFlowProvider>

// 节点/边类型定义 (在组件外或使用 useMemo)
const nodeTypes = {
  custom: CustomNode,
}
```

### 3.2 性能优化关键点

**1. 节点组件优化**
```typescript
// 使用 memo 包裹自定义节点
const CustomNode = memo(({ data }) => {
  return <div>{data.label}</div>
})

// 保持节点"哑" - 不包含业务逻辑
```

**2. 回调记忆化**
```typescript
const onConnect = useCallback(
  (params) => setEdges((eds) => addEdge(params, eds)),
  [setEdges]
)
```

**3. Store 访问优化**
```typescript
// 避免直接使用 useStore
// 使用 React Flow 提供的 hooks
const { getNodes, setNodes } = useStoreApi()
```

### 3.3 状态管理策略

**将图表视为系统状态，而非 UI 状态**

```typescript
// 不推荐: 本地状态
const [nodes, setNodes] = useNodesState(initialNodes)

// 推荐: 全局状态管理
const workflowStore = useWorkflowStore()
```

**撤销/重做实现选项**:
- 基于快照 (简单但内存占用大)
- 基于命令 (复杂但更精确)

### 3.4 连接验证

```typescript
const isValidConnection = (connection) => {
  if (connection.source === connection.target) return false
  const source = nodes.find((n) => n.id === connection.source)
  if (source?.type === "text") return false
  return true
}
```

### 3.5 自动布局方案

| 算法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| d3-hierarchy | 轻量 (136KB) | 不支持动态尺寸 | 简单线性流程 |
| dagre.js | 动态间距、简洁 | 固定节点定位 | 中等复杂度 |
| elk.js | 功能最全 | 重量 (7.8MB) | 复杂分支流程 |

### 3.6 大图性能优化

**视口虚拟化**: 仅渲染可见节点

**边类型选择**: 大图使用简单边类型

**更新防抖**: 对快速交互进行防抖

## 4. AI Agent 平台上手引导设计

### 4.1 "前五分钟"设计原则

#### 核心发现 (来自 Zylos Research)

**1. 展示而非告知**
- 不要依赖文档
- 在提示界面展示示例模板
- 提供预定义的可实现任务

**2. 渐进式自主权**
```
观察并建议 → 提出并等待批准 → 执行并通知 → 完全自主
```
- 关键指标: 建议接受率 >85% 时可提升自主权
- 一次失败且无回滚机制 = 用户永久流失

**3. 使等待状态富有成效**
- 不要只显示进度条
- 在索引/设置期间生成有价值的内容
- Devin 的例子: 代码库索引期间生成 DeepWiki 文档

**4. 模板选择的"雇佣"心智模型**
- 将 AI 视为雇佣员工
- 适当的期望 (需要时间、需要上下文)
- 而非期望即时魔法

### 4.2 Dify vs Coze 上手体验对比

| 维度 | Dify | Coze |
|------|------|------|
| 学习曲线 | 较陡峭，适合开发者 | 平缓，适合非技术人员 |
| 首次交互 | 需理解节点概念 | 拖拽即可用 |
| 模板数量 | 较少 | 丰富 |
| 引导流程 | 技术导向 | 任务导向 |
| 即时价值感 | 需配置后体现 | 立即可用 |

### 4.3 可借鉴的引导模式

**Lindy 的模板选择法**
1. 选择 AI 员工类型 (客服、HR、销售)
2. 通过表单向导配置
3. "雇佣"心智模型建立合理期望

**Devin 的渐进式方法**
1. 代码库索引 + 设置 (必需，等待期间生成文档)
2. 会话开始: 选择仓库 + Agent 类型
3. Ask Mode 优先: 仅生成计划
4. 批准计划 → 切换到 Agent Mode 执行
5. 任务示例指导首次任务选择
6. 会话后: Session Insights

**Gamma 的即时价值**
- 几秒内生成演示文稿草稿
- 消除空白页面瘫痪

### 4.4 关键指标和陷阱

**关键指标**:
- 进度条提升完成率 22%
- 72% 用户在步骤过多时放弃 (保持在 3-5 步)
- 预估时间 upfront 设置

**避免陷阱**:
- 不要在首个屏幕要求过多设置
- 不要只显示进度条
- 不要让空白页面让用户冻结
- 不要缺少回滚机制

## 5. 可借鉴的具体方案

### 5.1 技术架构选择

#### 推荐: React Flow + Zustand
- React Flow: 成熟、文档完善、社区活跃
- Zustand: 轻量、与 React Flow 配合良好
- zundo: 开箱即用的撤销/重做

#### 状态管理分层
```
/workflow-store/        # 工作流核心状态
/canvas-store/          # 画布 UI 状态
/panel-store/           # 面板状态
/execution-store/        # 执行状态
/selection-store/        # 选择状态
```

### 5.2 节点系统设计

```typescript
// 统一的节点接口
interface BaseNodeData {
  id: string
  type: NodeType
  title: string
  config: NodeConfig
  status?: NodeStatus
}

// BaseNode 包装器
<BaseNode>
  <NodeHeader />
  <NodeHandles />
  <NodeContent />
  <NodeStatus />
</BaseNode>
```

### 5.3 草稿持久化方案

```typescript
// 防抖自动保存
const debouncedSave = useDebounce(() => {
  saveWorkflowDraft(nodes, edges, viewport)
}, 2000)

// 页面关闭时的安全备份
useBeforeUnload(() => {
  navigator.sendBeacon('/api/workflows/draft', JSON.stringify({
    nodes, edges, viewport
  }))
})
```

### 5.4 上手引导流程

**阶段一: 快速价值 (30 秒)**
1. 欢迎屏幕 + 3 个模板选择
2. 即时预览 (零配置)

**阶段二: 个性化设置 (2-3 分钟)**
1. 简单表单向导 (最多 5 步)
2. 估计时间显示
3. 后台并行初始化

**阶段三: 深度探索 (按需)**
1. 交互式教程
2. 示例工作流画廊
3. 文档和社区链接

### 5.5 性能优化清单

- [ ] 节点组件使用 `memo`
- [ ] 回调使用 `useCallback`
- [ ] 复杂计算使用 `useMemo`
- [ ] Store 细粒度订阅
- [ ] 大图使用虚拟化
- [ ] 布局计算防抖
- [ ] 禁用 Immer 自动冻结 (`setAutoFreeze(false)`)

### 5.6 UI/UX 建议清单

**视觉设计**
- [ ] 清晰的节点类型视觉区分
- [ ] 连接线状态颜色编码
- [ ] 执行状态实时反馈
- [ ] 辅助线和对齐提示

**交互设计**
- [ ] 右键菜单操作
- [ ] 键盘快捷键支持
- [ ] 撤销/重做按钮
- [ ] 小地图导航
- [ ] 搜索和过滤功能

**错误处理**
- [ ] 节点级错误显示
- [ ] 连接验证反馈
- [ ] 优雅的错误消息

## 6. 推荐技术栈

基于研究结果，为 Agent Engine Platform 推荐以下技术栈:

### 核心框架
- **前端**: Next.js 14+ (App Router) + TypeScript
- **工作流**: React Flow v12+
- **状态管理**: Zustand + zundo
- **构建**: Turbopack (Next.js 集成) 或 Rsbuild

### 辅助库
- **样式**: Tailwind CSS + shadcn/ui
- **表单**: React Hook Form + Zod
- **数据获取**: SWR 或 TanStack Query
- **动画**: Framer Motion
- **国际化**: next-intl

### 工具链
- **包管理**: pnpm workspace
- **测试**: Vitest + Playwright
- **代码质量**: ESLint + Prettier
- **类型检查**: TypeScript strict mode

## 7. 参考资料

- Dify GitHub: https://github.com/langgenius/dify
- Dify 前端架构: https://deepwiki.com/langgenius/dify/10-web-frontend-architecture
- Coze Studio GitHub: https://github.com/coze-dev/coze-studio
- React Flow 文档: https://reactflow.dev
- AI Agent 上手引导研究: https://zylos.ai/research/2026-03-29-ai-agent-onboarding-ux-first-five-minutes

---

**研究完成时间**: 2026-05-29  
**研究团队**: Frontend Researcher Agent  
**下一步行动**: 基于本研究结果制定前端优化实施计划

# 前端长期优化计划

> 制定日期：2026-05-29  
> 制定者：Frontend Researcher Agent  
> 依据：产品评估报告 + 竞品研究

---

## 计划概览

基于产品评估报告（前端评分 3.5/10）和竞品研究，制定以下三阶段优化计划：

| 阶段 | 时间周期 | 核心目标 | 工作量 |
|------|---------|---------|--------|
| **P0** | 0-3月 | 产品生死线：补齐致命短板 | 3FE + 1BE + 1PM |
| **P1** | 3-6月 | 建立竞争壁垒 | 2FE + 1BE |
| **P2** | 6-12月 | 扩大领先优势 | 1.5FE + 持续 |

**总投入估算**: 6.5 前端人月 + 1 后端人月 + 1 产品经理人月

---

## P0 阶段 (0-3月) — 产品生死线

### 方案 1：Workflow 可视化 DAG 编辑器

**优先级**: P0 | **状态**: 🔴 完全缺失 | **影响**: 用户直接流失

#### 1.1 页面结构

```
/workflows/create                # 新建工作流
/workflows/[id]/edit             # 编辑工作流
/workflows/[id]/edit/debug       # 调试模式
```

#### 1.2 组件拆分

```
app/
├── workflows/
│   ├── [id]/
│   │   └── edit/
│   │       ├── page.tsx                 # 主页面
│   │       ├── components/
│   │       │   ├── WorkflowCanvas/      # React Flow 画布
│   │       │   │   ├── index.tsx
│   │       │   │   ├── nodes/           # 节点类型
│   │       │   │   │   ├── BaseNode.tsx
│   │       │   │   │   ├── LLMNode.tsx
│   │       │   │   │   ├── CodeNode.tsx
│   │       │   │   │   ├── ConditionNode.tsx
│   │       │   │   │   ├── ParallelNode.tsx
│   │       │   │   │   ├── LoopNode.tsx
│   │       │   │   │   ├── HTTPNode.tsx
│   │       │   │   │   └── HumanNode.tsx
│   │       │   │   ├── edges/           # 边类型
│   │       │   │   │   ├── CustomEdge.tsx
│   │       │   │   │   └── AnimatedEdge.tsx
│   │       │   │   └── minimap/
│   │       │   ├── NodeConfigPanel/     # 节点配置面板
│   │       │   │   ├── index.tsx
│   │       │   │   ├── LLMConfig.tsx
│   │       │   │   ├── CodeConfig.tsx
│   │       │   │   └── HTTPConfig.tsx
│   │       │   ├── Toolbar/             # 工具栏
│   │       │   │   ├── index.tsx
│   │       │   │   ├── UndoRedo.tsx
│   │       │   │   ├── RunButton.tsx
│   │       │   │   └── SaveButton.tsx
│   │       │   ├── NodePalette/         # 节点拖拽面板
│   │       │   │   ├── index.tsx
│   │       │   │   └── NodeCategory.tsx
│   │       │   ├── VariablePicker/     # 变量选择器
│   │       │   │   └── DebugPanel/      # 调试面板
│   │       │   └── minimap/
│   │       ├── stores/                  # Zustand stores
│   │       │   ├── workflow-store.ts
│   │       │   ├── canvas-store.ts
│   │       │   ├── panel-store.ts
│   │       │   ├── execution-store.ts
│   │       │   └── selection-store.ts
│   │       ├── hooks/
│   │       │   ├── use-nodes-sync.ts
│   │       │   ├── use-workflow-history.ts
│   │       │   └── use-node-validation.ts
│   │       └── utils/
│   │           ├── elk-layout.ts
│   │           └── workflow-validator.ts
```

#### 1.3 交互流程

```
用户进入编辑器
  │
  ├─→ 首次创建？
  │    └─→ 显示空状态 + 3个模板选择
  │
  ├─→ 加载已存在工作流
  │    └─→ 解析后端 graph JSON → React Flow nodes/edges
  │
  ├─→ 拖拽添加节点
  │    └─→ 从 NodePalette 拖拽 → 画布生成节点 → 自动保存草稿
  │
  ├─→ 配置节点
  │    └─→ 点击节点 → NodeConfigPanel 打开 → 配置表单 → 验证 → 保存
  │
  ├─→ 连接节点
  │    └─→ 拖拽 handle → 显示连接线 → 释放 → 验证连接 → 创建边
  │
  ├─→ 运行调试
  │    └─→ 点击运行 → 切换到调试模式 → 实时显示节点状态 → SSE 推送进度
  │
  └─→ 保存发布
       └─→ 验证完整性 → 保存草稿/发布版本 → 成功提示
```

#### 1.4 技术选型

| 技术点 | 选型 | 理由 |
|--------|------|------|
| 工作流引擎 | React Flow v12+ | 成熟、社区活跃、与 Next.js 兼容 |
| 状态管理 | Zustand + zundo | 轻量、撤销/重做开箱即用 |
| 布局算法 | elk.js | 复杂分支支持（后端 8 种节点类型） |
| 表单 | React Hook Form + Zod | 类型安全、验证能力强 |
| 动画 | Framer Motion | 流畅的交互体验 |
| 草稿同步 | SWR + 防抖 | 自动同步到后端 |

#### 1.5 核心特性

**撤销/重做系统**
```typescript
// 基于快照的实现
import { zundo } from 'zundo'

const workflowStore = create(
  zundo(
    set => ({
      nodes: [],
      edges: [],
      // ...
    }),
    {
      limit: 50,  // 最多 50 步历史
    }
  )
)
```

**草稿自动保存**
```typescript
// 防抖 2 秒保存
const debouncedSave = useDebounce(() => {
  mutate(['/api/workflows/draft', { nodes, edges, viewport }])
}, 2000)

// 页面关闭时同步
useEffect(() => {
  const handleBeforeUnload = () => {
    navigator.sendBeacon('/api/workflows/draft', JSON.stringify({
      nodes, edges, viewport
    }))
  }
  window.addEventListener('beforeunload', handleBeforeUnload)
  return () => window.removeEventListener('beforeunload', handleBeforeUnload)
}, [])
```

**SSE 实时执行状态**
```typescript
// 调试模式接收执行事件
useEffect(() => {
  const eventSource = new EventSource(`/api/workflows/${id}/run`)

  eventSource.addEventListener('node_started', (e) => {
    updateNodeStatus(JSON.parse(e.data).node_id, 'running')
  })

  eventSource.addEventListener('node_completed', (e) => {
    updateNodeStatus(JSON.parse(e.data).node_id, 'completed')
  })

  return () => eventSource.close()
}, [])
```

#### 1.6 工作量估算

| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 基础画布 + React Flow 集成 | 5 天 | - |
| 8 种节点类型组件 | 8 天 | 基础画布 |
| 节点配置面板 | 5 天 | 节点组件 |
| 工具栏 + 撤销/重做 | 2 天 | - |
| 草稿同步 + 持久化 | 2 天 | - |
| 调试模式 + SSE | 3 天 | 后端事件 API |
| 自动布局 (elk.js) | 2 天 | - |
| 变量选择器 | 2 天 | - |
| 连接验证 | 1 天 | - |
| 键盘快捷键 | 1 天 | - |
| 小地图 + 搜索 | 2 天 | - |
| **总计** | **33 天 (约 6 周)** | **2 前端工程师** |

---

### 方案 2：多 Agent 编排页面

**优先级**: P0 | **状态**: 🔴 完全缺失 | **后端**: API 已存在

#### 2.1 页面结构

```
/multi-agents                      # Crew 列表
/multi-agents/create               # 创建 Crew
/multi-agents/[id]                 # Crew 详情
/multi-agents/[id]/edit           # 编辑 Crew
/multi-agents/[id]/run           # 运行 Crew
```

#### 2.2 组件拆分

```
app/
├── multi-agents/
│   ├── page.tsx                   # 列表页
│   ├── create/
│   │   └── page.tsx               # 创建向导
│   ├── [id]/
│   │   ├── page.tsx               # 详情页
│   │   ├── edit/
│   │   │   └── page.tsx           # 编辑页
│   │   ├── run/
│   │   │   └── page.tsx           # 运行页
│   │   └── components/
│   │       ├── CrewVisualizer/   # Crew 可视化
│   │       ├── AgentCard/        # Agent 卡片
│   │       ├── HandoffFlow/      # Handoff 流程图
│   │       └── ModeSelector/     # 协作模式选择
```

#### 2.3 页面设计

**创建向导 (3 步)**

```tsx
// Step 1: 选择协作模式
<ModeSelector
  modes={[
    { id: 'sequential', name: '顺序执行', description: '...' },
    { id: 'hierarchical', name: '层级管理', description: '...' },
    { id: 'parallel', name: '并行执行', description: '...' },
    { id: 'consensus', name: '共识决策', description: '...' },
  ]}
/>

// Step 2: 添加 Agent
<AgentSelector
  availableAgents={agents}
  selectedAgents={crew.agents}
/>

// Step 3: 配置 Handoff 规则
<HandoffConfig
  agents={crew.agents}
  handoffs={crew.handoffs}
/>
```

**Crew 可视化**

```tsx
<CrewVisualizer
  mode={crew.mode}
  agents={crew.agents}
  handoffs={crew.handoffs}
  render={(mode) => (
    mode === 'hierarchical' ? <HierarchyTree /> :
    mode === 'parallel' ? <ParallelFlow /> :
    mode === 'consensus' ? <ConsensusMatrix /> :
    <SequentialFlow />
  )}
/>
```

#### 2.4 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表页 + CRUD | 2 天 |
| 创建向导 | 3 天 |
| Crew 可视化 | 4 天 |
| Handoff 流程图 | 3 天 |
| 运行页 + SSE | 3 天 |
| **总计** | **15 天 (约 3 周)** |

---

### 方案 3：评估页面

**优先级**: P0 | **状态**: 🔴 完全缺失 | **后端**: API 已存在

#### 3.1 页面结构

```
/evaluations                           # 评估列表
/evaluations/create                   # 创建评估
/evaluations/[id]                     # 评估详情
/evaluations/[id]/run                # 运行评估
/evaluations/datasets                 # 数据集管理
```

#### 3.2 页面设计

**评估详情页**

```tsx
<EvaluationDetail>
  {/* 头部：评估概览 */}
  <EvaluationHeader
    name={evaluation.name}
    status={evaluation.status}
    metrics={evaluation.metrics}
  />

  {/* 左侧：配置面板 */}
  <EvalConfig>
    <DatasetSelector />
    <AgentSelector />
    <MetricSelector
      options={[
        'faithfulness', 'relevancy', 'precision',
        'recall', 'tool_accuracy'
      ]}
    />
  </EvalConfig>

  {/* 右侧：结果可视化 */}
  <ResultsView>
    <MetricCards metrics={results.metrics} />
    <RagasChart data={results.ragas_scores} />
    <ComparisonChart before={baseline} after={results} />
    <TestCaseTable cases={results.test_cases} />
  </ResultsView>
</EvaluationDetail>
```

#### 3.3 核心组件

**Ragas 指标卡片**

```tsx
<MetricCard
  title="Faithfulness"
  value={0.87}
  trend="+5%"
  description="回答事实准确性"
/>
```

**A/B 对比视图**

```tsx
<ComparisonView>
  <ComparisonTable
    before={baselineResults}
    after={currentResults}
    metrics={['faithfulness', 'relevancy']}
  />
  <ImprovementHighlight delta={delta} />
</ComparisonView>
```

#### 3.4 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + 创建 | 2 天 |
| 详情页布局 | 2 天 |
| 指标可视化 | 3 天 |
| A/B 对比视图 | 2 天 |
| 测试用例表格 | 1 天 |
| **总计** | **10 天 (约 2 周)** |

---

### 方案 4：触发器管理页面

**优先级**: P0 | **状态**: 🔴 完全缺失

#### 4.1 页面结构

```
/triggers                        # 触发器列表
/triggers/create                 # 创建触发器
/triggers/[id]                  # 触发器详情
```

#### 4.2 页面设计

**触发器类型**

```tsx
<TriggerTypeSelector>
  <TriggerType
    id="schedule"
    name="定时触发"
    icon={<Clock />}
    config={<CronExpressionEditor />}
  />
  <TriggerType
    id="webhook"
    name="Webhook"
    icon={<Webhook />}
    config={<WebhookConfig />}
  />
  <TriggerType
    id="event"
    name="事件触发"
    icon={<Event />}
    config={<EventSelector />}
  />
</TriggerTypeSelector>
```

#### 4.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + CRUD | 2 天 |
| 定时配置 (Cron) | 2 天 |
| Webhook 配置 | 1 天 |
| 事件触发配置 | 1 天 |
| **总计** | **6 天 (约 1 周)** |

---

### 方案 5：Webhook 管理页面

**优先级**: P0 | **状态**: 🔴 完全缺失

#### 5.1 页面结构

```
/webhooks                        # Webhook 列表
/webhooks/create                 # 创建 Webhook
/webhooks/[id]                  # Webhook 详情
/webhooks/[id]/logs             # Webhook 日志
```

#### 5.2 页面设计

**Webhook 详情**

```tsx
<WebhookDetail>
  <WebhookHeader
    url={webhook.url}
    secret={webhook.secret}
    status={webhook.status}
  />

  <RequestConfig>
    <HttpMethodSelector />
    <HeadersEditor />
    <AuthConfig />
  </RequestConfig>

  <EventLog>
    <LogTable logs={webhook.logs} />
    <RetryButton />
  </EventLog>
</WebhookDetail>
```

#### 5.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + CRUD | 2 天 |
| 详情页配置 | 2 天 |
| 日志查看 | 1 天 |
| **总计** | **5 天 (约 1 周)** |

---

### 方案 6：租户管理页面

**优先级**: P0 | **状态**: 🔴 完全缺失

#### 6.1 页面结构

```
/admin/tenants                   # 租户列表
/admin/tenants/create            # 创建租户
/admin/tenants/[id]             # 租户详情
```

#### 6.2 页面设计

**租户详情**

```tsx
<TenantDetail>
  <TenantInfo
    name={tenant.name}
    status={tenant.status}
    quota={tenant.max_agents}
  />

  <QuotaConfig>
    <QuotaSlider
      label="最大 Agent 数"
      value={tenant.max_agents}
      onChange={updateQuota}
    />
    <FeatureToggle
      features={tenant.features}
    />
  </QuotaConfig>

  <DepartmentList departments={tenant.departments} />
  <UsageStats stats={tenant.usage} />
</TenantDetail>
```

#### 6.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + CRUD | 2 天 |
| 配额管理 | 2 天 |
| 部门管理 | 1 天 |
| 用量统计 | 1 天 |
| **总计** | **6 天 (约 1 周)** |

---

### 方案 7：角色管理页面

**优先级**: P0 | **状态**: 🔴 完全缺失

#### 7.1 页面结构

```
/admin/roles                     # 角色列表
/admin/roles/create              # 创建角色
/admin/roles/[id]               # 角色详情
```

#### 7.2 页面设计

**权限配置矩阵**

```tsx
<PermissionMatrix
  roles={roles}
  resources={resources}
  actions={['create', 'read', 'update', 'delete'}}
  render={(role, resource, action) => (
    <PermissionCheckbox
      checked={hasPermission(role, resource, action)}
      onChange={(checked) => togglePermission(role, resource, action)}
    />
  )}
/>
```

#### 7.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + CRUD | 2 天 |
| 权限矩阵 | 3 天 |
| 角色复制 | 1 天 |
| **总计** | **6 天 (约 1 周)** |

---

### 方案 8：用户管理页面

**优先级**: P0 | **状态**: 🔴 完全缺失

#### 8.1 页面结构

```
/admin/users                      # 用户列表
/admin/users/create              # 创建用户
/admin/users/[id]                # 用户详情
```

#### 8.2 页面设计

**用户详情**

```tsx
<UserDetail>
  <UserInfo user={user} />
  <RoleSelector
    availableRoles={roles}
    selectedRoles={user.roles}
  />
  <ActivityLog logs={user.audit_logs} />
</UserDetail>
```

#### 8.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 列表 + CRUD | 2 天 |
| 角色分配 | 1 天 |
| 活动日志 | 1 天 |
| **总计** | **4 天 (约 1 周)** |

---

### 方案 9：Agent 对话页重写

**优先级**: P0 | **状态**: 🟡 极薄 (57 行) | **影响**: 核心场景

#### 9.1 当前问题

- 无代码高亮
- 无 Markdown 渲染
- 无停止按钮
- SSE 流式效果差
- 无消息引用

#### 9.2 组件拆分

```
app/
├── agents/
│   └── [id]/
│       └── chat/
│           ├── page.tsx
│           ├── components/
│           │   ├── ChatContainer/
│           │   │   ├── index.tsx
│           │   │   ├── MessageList.tsx
│           │   │   ├── MessageInput.tsx
│           │   │   └── StopButton.tsx
│           │   ├── ChatMessage/
│           │   │   ├── index.tsx
│           │   │   ├── UserMessage.tsx
│           │   │   ├── AssistantMessage.tsx
│           │   │   ├── ToolCall.tsx
│           │   │   └── ThinkingIndicator.tsx
│           │   ├── MarkdownRenderer/
│           │   │   ├── index.tsx
│           │   │   ├── CodeBlock.tsx
│           │   │   └── CopyButton.tsx
│           │   └── MessageActions/
│           │       ├── CopyButton.tsx
│           │       ├── RegenerateButton.tsx
│           │       └── ReferenceButton.tsx
│           └── hooks/
│               ├── use-stream-chat.ts
│               └── use-message-actions.ts
```

#### 9.3 技术选型

| 功能 | 技术选型 |
|------|---------|
| Markdown 渲染 | react-markdown |
| 代码高亮 | highlight.js + react-highlight |
| 代码复制 | clipboard.js |
| 打字机效果 | 自定义或 framer-motion |
| SSE | EventSource + SWR |

#### 9.4 核心特性

**流式打字机效果**

```tsx
<ThinkingIndicator>
  <PulseDots />
  <span>Agent 正在思考...</span>
</ThinkingIndicator>

<StreamingMessage content={content}>
  <TypewriterEffect speed={30} />
</StreamingMessage>
```

**工具调用可视化**

```tsx
<ToolCall
  name={tool.name}
  input={tool.input}
  status={tool.status}
>
  {tool.status === 'running' && <Spinner />}
  {tool.status === 'completed' && (
    <ToolOutput output={tool.output} />
  )}
</ToolCall>
```

#### 9.5 工作量估算

| 任务 | 工作量 |
|------|--------|
| 消息列表重构 | 2 天 |
| Markdown 渲染 | 1 天 |
| 代码高亮 + 复制 | 1 天 |
| SSE 流式 + 打字机 | 2 天 |
| 停止按钮 | 1 天 |
| 消息操作 | 1 天 |
| 工具调用可视化 | 1 天 |
| **总计** | **9 天 (约 2 周)** |

---

### 方案 10：上手引导 Onboarding

**优先级**: P0 | **状态**: 🔴 完全缺失 | **影响**: 新用户转化

#### 10.1 引导流程

**阶段一：欢迎 (30 秒)**

```tsx
<WelcomeScreen>
  <HeroTitle>构建您的第一个 AI Agent</HeroTitle>
  <TemplateCarousel>
    <TemplateCard
      title="客服助手"
      description="基于知识库的智能客服"
      icon={<CustomerService />}
    />
    <TemplateCard
      title="数据分析"
      description="自动化数据分析和报告"
      icon={<Analytics />}
    />
    <TemplateCard
      title="内容创作"
      description="文章生成和内容优化"
      icon={<Create />}
    />
  </TemplateCarousel>
  <StartButton>开始创建</StartButton>
</WelcomeScreen>
```

**阶段二：快速创建 (2 分钟)**

```tsx
<QuickCreateWizard>
  {/* Step 1: 选择模板 */}
  <Step>选择模板 → 下一步</Step>

  {/* Step 2: 配置 Agent */}
  <AgentConfigForm>
    <NameInput />
    <DescriptionInput />
    <ModelSelector />
  </AgentConfigForm>

  {/* Step 3: 连接知识库 (可选) */}
  <KnowledgeConnector />

  {/* Step 4: 测试对话 */}
  <TestChat />

  {/* 完成 */}
  <SuccessScreen>
    <Confetti />
    <CallToAction>继续编辑或发布</CallToAction>
  </SuccessScreen>
</QuickCreateWizard>
```

#### 10.2 技术实现

```tsx
// 引导状态管理
const onboardingStore = create((set) => ({
  step: 0,
  completed: false,
  template: null,
  nextStep: () => set((state) => ({ step: state.step + 1 })),
  skip: () => set({ completed: true }),
}))

// 进度指示器
<OnboardingProgress current={step} total={4} />

// 跳过逻辑
<SkipButton onClick={() => onboardingStore.skip()} />
```

#### 10.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 欢迎页 | 1 天 |
| 模板选择 | 1 天 |
| 创建向导 | 2 天 |
| 测试对话 | 1 天 |
| 成功页 | 0.5 天 |
| 跳过逻辑 | 0.5 天 |
| **总计** | **6 天 (约 1 周)** |

---

## P1 阶段 (3-6月) — 建立竞争壁垒

### 方案 11：工具市场 UI

**优先级**: P1 | **状态**: 🔴 完全缺失

#### 11.1 页面结构

```
/tools/marketplace                # 工具市场
/tools/marketplace/[id]          # 工具详情
/tools/marketplace/[id]/install  # 安装配置
/tools/my                        # 我安装的工具
```

#### 11.2 页面设计

**市场首页**

```tsx
<ToolMarketplace>
  <HeroBanner
    featuredTools={['claude-openai-migrator', 'rag-pipeline']}
  />

  <CategoryNav>
    <Category id="productivity">生产力</Category>
    <Category id="data">数据处理</Category>
    <Category id="integration">集成</Category>
    <Category id="ai">AI 能力</Category>
  </CategoryNav>

  <ToolGrid>
    <ToolCard
      tool={tool}
      showInstallButton
      onClick={() => router.push(`/tools/marketplace/${tool.id}`)}
    />
  </ToolGrid>

  <FeaturedSection title="热门推荐">
    <ToolCarousel tools={trendingTools} />
  </FeaturedSection>
</ToolMarketplace>
```

**工具详情**

```tsx
<ToolDetail>
  <ToolHeader
    name={tool.name}
    icon={tool.icon}
    publisher={tool.publisher}
    rating={tool.rating}
  />

  <ToolGallery screenshots={tool.screenshots} />

  <ToolDescription>
    <Markdown>{tool.description}</Markdown>
  </ToolDescription>

  <ToolSpec>
    <ParamList params={tool.parameters} />
    <OutputSchema schema={tool.output} />
  </ToolSpec>

  <InstallActions>
    <InstallButton onClick={installTool} />
    <TestButton onClick={testTool} />
  </InstallActions>

  <Reviews reviews={tool.reviews} />
</ToolDetail>
```

#### 11.3 工作量估算

| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 市场首页 | 3 天 | 后端工具 API |
| 工具详情页 | 3 天 | 后端工具 API |
| 分类搜索 | 2 天 | - |
| 安装配置 | 2 天 | 后端安装 API |
| 评分评论 | 2 天 | 后端评论 API |
| 我的工具 | 1 天 | - |
| **总计** | **13 天 (约 2.5 周)** |

---

### 方案 12：评估 Playground 可视化

**优先级**: P1 | **状态**: 🔴 完全缺失

#### 12.1 页面结构

```
/evaluations/[id]/playground      # 评估 Playground
/evaluations/[id]/playground/config    # 配置
/evaluations/[id]/playground/run       # 运行
```

#### 12.2 页面设计

**Playground 主界面**

```tsx
<EvalPlayground>
  {/* 左侧：输入 */}
  <InputPanel>
    <TestCaseInput />
    <BatchUpload />
    <DatasetSelector />
  </InputPanel>

  {/* 中间：执行 */}
  <ExecutionPanel>
    <AgentSelector />
    <RunButton onClick={runEvaluation} />
    <ProgressIndicator />
  </ExecutionPanel>

  {/* 右侧：输出 */}
  <OutputPanel>
    <MetricDashboard metrics={results.metrics} />
    <TestCaseTable results={results.cases} />
    <ComparisonView before={baseline} after={results} />
  </OutputPanel>
</EvalPlayground>
```

**实时指标仪表盘**

```tsx
<MetricDashboard>
  <MetricGauge
    title="Faithfulness"
    value={0.87}
    threshold={0.8}
    status="good"
  />
  <MetricTrend
    title="Relevancy"
    history={[0.75, 0.78, 0.82, 0.85]}
  />
  <MetricComparison
    metrics={results.metrics}
    baseline={baseline}
  />
</MetricDashboard>
```

#### 12.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 布局设计 | 2 天 |
| 输入面板 | 2 天 |
| 执行面板 | 2 天 |
| 输出面板 | 3 天 |
| 指标仪表盘 | 3 天 |
| 实时更新 | 2 天 |
| **总计** | **14 天 (约 3 周)** |

---

### 方案 13：前端测试覆盖提升

**优先级**: P1 | **状态**: 🔴 当前 0.10 (4 文件/457 行)

#### 13.1 目标

- 从 10% 提升至 60%+
- 覆盖所有核心组件和页面
- 集成 Playwright E2E 测试

#### 13.2 测试策略

**单元测试 (Vitest + React Testing Library)**

```typescript
// 组件测试示例
describe('WorkflowCanvas', () => {
  it('should render nodes and edges', () => {
    const { container } = render(
      <WorkflowCanvas nodes={mockNodes} edges={mockEdges} />
    )
    expect(container.querySelectorAll('.react-flow__node')).toHaveLength(3)
  })

  it('should handle node drag', async () => {
    const onNodeDrag = vi.fn()
    render(<WorkflowCanvas onNodeDrag={onNodeDrag} />)
    
    const node = screen.getByTestId('node-1')
    await fireEvent.dragStart(node)
    
    expect(onNodeDrag).toHaveBeenCalled()
  })
})
```

**集成测试 (MSW + Testing Library)**

```typescript
describe('Agent Creation Flow', () => {
  it('should create agent and redirect to detail', async () => {
    const { user } = setupUser()
    render(<AgentCreatePage />)
    
    await user.type(screen.getByLabelText('名称'), 'Test Agent')
    await user.click(screen.getByRole('button', { name: '创建' }))
    
    await waitFor(() => {
      expect(screen.getByText('创建成功')).toBeVisible()
    })
  })
})
```

**E2E 测试 (Playwright)**

```typescript
test('workflow execution flow', async ({ page }) => {
  await page.goto('/workflows/test/edit')
  
  // 添加节点
  await page.dragAndDrop('#llm-node', '#canvas')
  await page.dragAndDrop('#code-node', '#canvas')
  
  // 连接节点
  await page.click('.handle-source[data-node="llm"]')
  await page.click('.handle-target[data-node="code"]')
  
  // 运行
  await page.click('button:has-text("运行")')
  
  // 验证结果
  await expect(page.locator('.node-status.completed')).toHaveCount(2)
})
```

#### 13.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 核心组件测试 (20+) | 5 天 |
| 页面集成测试 (10+) | 3 天 |
| E2E 测试场景 (5+) | 3 天 |
| CI/CD 集成 | 1 天 |
| 覆盖率报告 | 1 天 |
| **总计** | **13 天 (约 2.5 周)** |

---

## P2 阶段 (6-12月) — 扩大领先优势

### 方案 14：i18n 国际化

**优先级**: P2 | **状态**: 🔴 全中文硬编码

#### 14.1 技术选型

- **框架**: next-intl
- **语言**: 中文 (默认)、英文、日语
- **格式**: ICU MessageFormat

#### 14.2 实现方案

**目录结构**

```
messages/
├── zh.json       # 中文
├── en.json       # 英文
└── ja.json       # 日语

app/
└── [locale]/
    └── ...
```

**使用示例**

```tsx
import { useTranslations } from 'next-intl'

function AgentList() {
  const t = useTranslations('agents')
  return (
    <div>
      <h1>{t('title')}</h1>
      <button>{t('actions.create')}</button>
    </div>
  )
}
```

#### 14.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 框架集成 | 2 天 |
| 文本提取 (500+) | 3 天 |
| 翻译 (中/英/日) | 5 天 |
| 日期/数字格式化 | 1 天 |
| RTL 支持 (可选) | 2 天 |
| **总计** | **13 天 (约 2.5 周)** |

---

### 方案 15：可观测性仪表盘

**优先级**: P2 | **状态**: 🔴 完全缺失

#### 15.1 页面结构

```
/observability                   # 可观测性首页
/observability/metrics          # 指标监控
/observability/traces           # 追踪查看
/observability/logs             # 日志查询
/observability/alerts           # 告警配置
```

#### 15.2 页面设计

**指标监控**

```tsx
<MetricsDashboard>
  <MetricCard
    title="Agent 调用次数"
    value={stats.total_calls}
    trend="+12%"
    chart={<LineChart data={stats.calls_history} />}
  />
  <MetricCard
    title="平均延迟"
    value={stats.avg_latency + 'ms'}
    trend="-5%"
    chart={<AreaChart data={stats.latency_history} />}
  />
  <MetricCard
    title="错误率"
    value={(stats.error_rate * 100) + '%'}
    status={stats.error_rate > 0.05 ? 'critical' : 'good'}
  />
  <MetricCard
    title="Token 消耗"
    value={stats.total_tokens}
    breakdown={stats.token_by_model}
  />
</MetricsDashboard>
```

**追踪查看**

```tsx
<TraceViewer>
  <TraceGantt
    traces={traces}
    renderNode={(trace) => (
      <TraceNode
        name={trace.agent_name}
        duration={trace.duration}
        status={trace.status}
        onClick={() => showTraceDetail(trace)}
      />
    )}
  />
  <TraceDetail trace={selectedTrace}>
    <TraceTimeline events={trace.events} />
    <TraceInput input={trace.input} />
    <TraceOutput output={trace.output} />
    <TraceMetadata metadata={trace.metadata} />
  </TraceDetail>
</TraceViewer>
```

#### 15.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 指标监控 | 4 天 |
| 追踪查看 | 5 天 |
| 日志查询 | 3 天 |
| 告警配置 | 2 天 |
| **总计** | **14 天 (约 3 周)** |

---

### 方案 16：移动端响应式设计

**优先级**: P2 | **状态**: 🔴 当前 2/10

#### 16.1 技术选型

- **CSS 框架**: Tailwind CSS (已有)
- **断点**: sm (640px), md (768px), lg (1024px), xl (1280px)
- **测试**: BrowserStack + Playwright

#### 16.2 响应式策略

**布局适配**

```tsx
// Dashboard 响应式布局
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div className="lg:col-span-2">
    <MainContent />
  </div>
  <div className="hidden lg:block">
    <Sidebar />
  </div>
</div>
```

**触摸优化**

```tsx
// 移动端友好的交互
<button className="min-h-[44px] min-w-[44px]">
  点击区域 > 44x44px
</button>
```

**移动端导航**

```tsx
// 移动端抽屉菜单
<MobileNav>
  <Sheet>
    <SheetTrigger>
      <MenuButton />
    </SheetTrigger>
    <SheetContent side="left">
      <NavigationMenu />
    </SheetContent>
  </Sheet>
</MobileNav>
```

#### 16.3 工作量估算

| 任务 | 工作量 |
|------|--------|
| 布局适配 (10+ 页面) | 5 天 |
| 组件响应式 (20+) | 3 天 |
| 触摸交互优化 | 2 天 |
| 移动端测试 | 2 天 |
| 性能优化 | 2 天 |
| **总计** | **14 天 (约 3 周)** |

---

## 总体工作量汇总

### P0 阶段 (0-3 月)

| 方案 | 工作量 | 工程师 |
|------|--------|--------|
| 1. Workflow 编辑器 | 6 周 (33 天) | 2FE |
| 2. 多 Agent 编排 | 3 周 (15 天) | 1FE |
| 3. 评估页面 | 2 周 (10 天) | 1FE |
| 4. 触发器管理 | 1 周 (6 天) | 1FE |
| 5. Webhook 管理 | 1 周 (5 天) | 1FE |
| 6. 租户管理 | 1 周 (6 天) | 1FE |
| 7. 角色管理 | 1 周 (6 天) | 1FE |
| 8. 用户管理 | 1 周 (4 天) | 1FE |
| 9. Agent 对话重写 | 2 周 (9 天) | 1FE |
| 10. Onboarding | 1 周 (6 天) | 1FE |
| **小计** | **20 周 (100 天)** | **3FE 并行 8 周** |

### P1 阶段 (3-6 月)

| 方案 | 工作量 | 工程师 |
|------|--------|--------|
| 11. 工具市场 | 2.5 周 (13 天) | 1FE |
| 12. 评估 Playground | 3 周 (14 天) | 1FE |
| 13. 测试覆盖提升 | 2.5 周 (13 天) | 1FE |
| **小计** | **8 周 (40 天)** | **1FE + 持续** |

### P2 阶段 (6-12 月)

| 方案 | 工作量 | 工程师 |
|------|--------|--------|
| 14. i18n 国际化 | 2.5 周 (13 天) | 1FE |
| 15. 可观测性仪表盘 | 3 周 (14 天) | 1FE |
| 16. 移动端响应式 | 3 周 (14 天) | 1FE |
| **小计** | **8.5 周 (41 天)** | **1FE 持续** |

### 总计

- **P0**: 100 天 (约 5 人月)
- **P1**: 40 天 (约 2 人月)
- **P2**: 41 天 (约 2 人月)
- **总计**: 181 天 ≈ **9 人月**

---

## 实施路线图

### 第 1-2 月：Workflow 编辑器 + 核心页面

**目标**: 完成最致命短板

- 第 1-4 周：Workflow 编辑器 (2FE)
- 第 1-2 周：多 Agent 编排 (1FE)
- 第 1 周：评估页面 (1FE)
- 第 2 周：触发器 + Webhook (1FE)
- 第 3 周：租户 + 角色 + 用户 (1FE)
- 第 3-4 周：Agent 对话重写 (1FE)
- 第 4 周：Onboarding (1FE)

**并行策略**: 3 前端工程师同时工作，按优先级串行交付

### 第 3 月：整合 + 测试

**目标**: P0 验收和稳定

- 完整测试 P0 所有功能
- 修复 bug
- 性能优化
- 文档完善

### 第 4-6 月：P1 阶段

**目标**: 建立竞争壁垒

- 第 4-6 周：工具市场 (1FE)
- 第 6-9 周：评估 Playground (1FE)
- 持续：测试覆盖 (1FE)

### 第 6-12 月：P2 阶段

**目标**: 扩大领先优势

- 持续：i18n、可观测性、移动端

---

## 风险与缓解

### 风险 1：Workflow 编辑器复杂度超预期

**缓解**:
- 先实现核心节点 (LLM/Code/HTTP)
- 分阶段发布 (MVP → 完整版)
- 参考 Dify 开源实现

### 风险 2：后端 API 不完整

**缓解**:
- 前后端并行开发
- 使用 Mock 数据先行开发 UI
- 及时沟通 API 需求

### 风险 3：人员不足

**缓解**:
- 优先级严格执行 (P0 → P1 → P2)
- 外包非核心页面
- 使用组件库减少开发量

---

## 附录：技术决策记录

### A1. 为什么选择 React Flow 而非自研？

1. **时间成本**: 自研需要 6+ 月，React Flow 即刻可用
2. **维护成本**: 社区维护 vs 自行维护
3. **功能成熟度**: React Flow 已处理边界情况
4. **扩展性**: 足够的自定义空间

### A2. 为什么选择 Zustand 而非 Redux？

1. **学习成本低**: API 简洁
2. **Bundle size 小**: 约 1KB vs Redux 3KB
3. **与 React Flow 配合好**: 众多案例验证
4. **zundo 支持**: 撤销/重做开箱即用

### A3. 为什么选择 elk.js 而非 dagre.js？

1. **复杂分支支持**: 后端有 Parallel/Loop/Iteration
2. **自定义布局能力**: 支持固定位置
3. **节点排序**: 保持添加顺序
4. **性能**: 7.8MB 可接受

---

**计划完成时间**: 2026-05-29  
**下一步**: 与团队评审计划，确认优先级和资源分配

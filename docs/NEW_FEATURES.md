# 新功能文档

## 1. 键盘快捷键系统

### 全局快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+D` | 跳转到 Dashboard |
| `Ctrl+A` | 跳转到 Agents |
| `Ctrl+K` | 跳转到 Knowledge |
| `Ctrl+W` | 跳转到 Workflows |
| `Ctrl+T` | 跳转到 Tools |
| `Ctrl+N` | 创建新资源 |
| `Ctrl+S` | 保存 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+Z` | 重做 |
| `Ctrl+/` | 显示快捷键帮助 |
| `Ctrl+K` | 打开命令面板 |
| `Esc` | 关闭弹窗/面板 |

### 工作流编辑器快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+Z` | 重做 |
| `Delete` | 删除选中节点 |
| `Ctrl+S` | 保存工作流 |
| `Ctrl+R` | 运行工作流 |

### 聊天快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 发送消息 |
| `Esc` | 停止生成 |
| `Ctrl+L` | 清空聊天 |

### 使用方法

```tsx
import { useKeyboardShortcuts, useWorkflowShortcuts, useChatShortcuts } from '@/hooks/useKeyboardShortcuts';

// 在组件中使用
function MyComponent() {
  useKeyboardShortcuts(); // 启用全局快捷键

  // 或者使用特定场景的快捷键
  useWorkflowShortcuts({
    onUndo: () => { /* 撤销逻辑 */ },
    onRedo: () => { /* 重做逻辑 */ },
    onDelete: () => { /* 删除逻辑 */ },
    onSave: () => { /* 保存逻辑 */ },
    onRun: () => { /* 运行逻辑 */ },
  });

  return <div>...</div>;
}
```

---

## 2. 命令面板

命令面板提供快速导航和操作功能。

### 打开方式

- 按 `Ctrl+K` (Windows/Linux) 或 `Cmd+K` (Mac)
- 点击顶部导航栏的搜索图标

### 功能

- 快速搜索和跳转到页面
- 执行常用操作（创建 Agent、工作流等）
- 支持键盘导航（↑↓ 选择，Enter 确认，Esc 关闭）

### 使用方法

```tsx
import CommandPalette from '@/components/CommandPalette';

function App() {
  const [open, setOpen] = useState(false);

  return (
    <CommandPalette open={open} onClose={() => setOpen(false)} />
  );
}
```

---

## 3. 响应式设计系统

### 断点定义

| 断点 | 宽度 | 设备类型 |
|------|------|----------|
| `xs` | < 640px | 手机 |
| `sm` | 640px - 767px | 大手机/小平板 |
| `md` | 768px - 1023px | 平板 |
| `lg` | 1024px - 1279px | 小桌面 |
| `xl` | 1280px - 1535px | 桌面 |
| `2xl` | ≥ 1536px | 大桌面 |

### 使用方法

```tsx
import { useResponsive, useIsMobile, useIsTablet, useIsDesktop } from '@/hooks/useResponsive';

function MyComponent() {
  const { isMobile, isTablet, isDesktop, breakpoint, width } = useResponsive();

  // 或者使用简化的 hooks
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();

  return (
    <div>
      {isMobile && <MobileLayout />}
      {isTablet && <TabletLayout />}
      {isDesktop && <DesktopLayout />}
    </div>
  );
}
```

### 响应式值 Hook

```tsx
import { useResponsiveValue } from '@/hooks/useResponsive';

function MyComponent() {
  const columns = useResponsiveValue(
    { xs: 1, sm: 2, md: 3, lg: 4 },
    3 // 默认值
  );

  return <Grid columns={columns}>...</Grid>;
}
```

---

## 4. 性能优化 Hooks

### 防抖 (Debounce)

```tsx
import { useDebounce } from '@/hooks/usePerformance';

function SearchInput() {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    // 使用 debouncedSearch 进行搜索
    fetchResults(debouncedSearch);
  }, [debouncedSearch]);

  return <input value={search} onChange={e => setSearch(e.target.value)} />;
}
```

### 节流 (Throttle)

```tsx
import { useThrottle } from '@/hooks/usePerformance';

function ScrollHandler() {
  const [scrollY, setScrollY] = useState(0);
  const throttledScrollY = useThrottle(scrollY, 100);

  useEffect(() => {
    // 使用 throttledScrollY 处理滚动
  }, [throttledScrollY]);

  return <div onScroll={e => setScrollY(e.currentTarget.scrollTop)}>...</div>;
}
```

### 虚拟列表

```tsx
import { useVirtualList } from '@/hooks/usePerformance';

function VirtualList({ items }) {
  const { visibleItems, totalHeight, onScroll } = useVirtualList({
    items,
    itemHeight: 50,
    containerHeight: 400,
    overscan: 5,
  });

  return (
    <div style={{ height: 400, overflow: 'auto' }} onScroll={onScroll}>
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map(({ item, index, style }) => (
          <div key={index} style={style}>
            {item.name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Local Storage Hook

```tsx
import { useLocalStorage } from '@/hooks/usePerformance';

function Settings() {
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  const [language, setLanguage] = useLocalStorage('language', 'zh-CN');

  return (
    <div>
      <select value={theme} onChange={e => setTheme(e.target.value)}>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  );
}
```

---

## 5. 通知系统

### 使用方法

```tsx
import { useNotification, useToast } from '@/components/NotificationProvider';

function MyComponent() {
  const { success, error, warning, info } = useNotification();
  // 或者
  const { toast } = useToast();

  const handleSave = async () => {
    try {
      await saveData();
      success('保存成功', '数据已成功保存');
      // 或者
      toast('success', '保存成功', '数据已成功保存');
    } catch (err) {
      error('保存失败', '请稍后重试');
    }
  };

  return <button onClick={handleSave}>Save</button>;
}
```

### 通知类型

| 类型 | 图标 | 用途 |
|------|------|------|
| `success` | ✅ | 操作成功 |
| `error` | ❌ | 操作失败 |
| `warning` | ⚠️ | 警告信息 |
| `info` | ℹ️ | 提示信息 |

---

## 6. 骨架屏组件

### 使用方法

```tsx
import { SkeletonLoader, AgentCardSkeleton, TableSkeleton, FormSkeleton, DashboardSkeleton } from '@/components/ui';

function AgentsPage() {
  const { loading } = useLoading('agents');

  if (loading) {
    return <AgentCardSkeleton />;
  }

  return <AgentList agents={agents} />;
}
```

### 可用组件

| 组件 | 用途 |
|------|------|
| `SkeletonLoader` | 通用骨架屏 |
| `AgentCardSkeleton` | Agent 卡片列表骨架屏 |
| `TableSkeleton` | 表格骨架屏 |
| `FormSkeleton` | 表单骨架屏 |
| `DashboardSkeleton` | Dashboard 骨架屏 |

---

## 7. 主题系统

### 可用主题

| 主题 | 预览 |
|------|------|
| `default` | 蓝色主题（默认） |
| `dark` | 暗色主题 |
| `blue` | 专业蓝主题 |
| `green` | 自然绿主题 |
| `purple` | 创意紫主题 |
| `orange` | 活力橙主题 |

### 使用方法

```tsx
import { ConfigProvider } from 'antd';
import { getTheme } from '@/lib/theme';

function App() {
  const [themeName, setThemeName] = useState('default');
  const theme = getTheme(themeName);

  return (
    <ConfigProvider theme={theme}>
      <AppContent />
    </ConfigProvider>
  );
}
```

---

## 8. 缓存系统

### 使用方法

```tsx
import { memoryCache, localStorageCache, CACHE_KEYS } from '@/lib/cache';

// 基本使用
memoryCache.set(CACHE_KEYS.AGENTS, agents, 5 * 60 * 1000); // 缓存 5 分钟
const cachedAgents = memoryCache.get(CACHE_KEYS.AGENTS);

// 使用工厂函数
const agents = await memoryCache.getOrSet(
  CACHE_KEYS.AGENTS,
  () => api.listAgents(),
  5 * 60 * 1000
);

// React Hook
function AgentsPage() {
  const { data, loading, error, invalidate } = useCache(
    CACHE_KEYS.AGENTS,
    () => api.listAgents(),
    5 * 60 * 1000
  );

  return (
    <div>
      <button onClick={invalidate}>刷新</button>
      {loading ? <Skeleton /> : <AgentList agents={data} />}
    </div>
  );
}
```

---

## 9. 加载状态管理

### 使用方法

```tsx
import { useLoading, useAsyncOperation, LOADING_KEYS } from '@/lib/loadingManager';

function AgentsPage() {
  const { loading, startLoading, stopLoading } = useLoading(LOADING_KEYS.AGENTS);
  // 或者
  const { loading, execute } = useAsyncOperation(LOADING_KEYS.AGENTS);

  const fetchAgents = async () => {
    const result = await execute(
      () => api.listAgents(),
      {
        loadingMessage: '加载 Agents...',
        onSuccess: (data) => { /* 处理成功 */ },
        onError: (error) => { /* 处理错误 */ },
      }
    );
  };

  return (
    <div>
      {loading && <Spin />}
      <button onClick={fetchAgents}>刷新</button>
    </div>
  );
}
```

---

## 10. 表单验证系统

### 使用方法

```tsx
import { z } from 'zod';
import { agentSchemas, validateForm, useFormValidation } from '@/lib/validation';

function CreateAgentForm() {
  const { errors, validate, getFieldError, hasErrors } = useFormValidation(agentSchemas.create);

  const handleSubmit = (values) => {
    if (!validate(values)) {
      return;
    }
    // 提交表单
  };

  return (
    <Form onFinish={handleSubmit}>
      <Form.Item
        name="name"
        validateStatus={getFieldError('name') ? 'error' : ''}
        help={getFieldError('name')}
      >
        <Input />
      </Form.Item>
    </Form>
  );
}
```

### 验证 Schema

| Schema | 用途 |
|--------|------|
| `commonSchemas` | 通用验证规则 |
| `agentSchemas` | Agent 相关验证 |
| `knowledgeSchemas` | 知识库相关验证 |
| `workflowSchemas` | 工作流相关验证 |
| `modelSchemas` | 模型相关验证 |
| `toolSchemas` | 工具相关验证 |
| `userSchemas` | 用户相关验证 |

---

## 11. 错误处理系统

### 使用方法

```tsx
import { handleError, withErrorHandling, withRetry } from '@/lib/errorHandler';

// 基本使用
try {
  await api.createAgent(data);
} catch (error) {
  handleError(error);
}

// 使用包装函数
const result = await withErrorHandling(
  () => api.createAgent(data),
  { showMessage: true, showNotification: true }
);

// 使用重试逻辑
const data = await withRetry(
  () => api.fetchData(),
  {
    maxRetries: 3,
    baseDelay: 1000,
    retryOn: (error) => error instanceof NetworkError,
  }
);
```

### 错误类型

| 类型 | 状态码 | 说明 |
|------|--------|------|
| `NetworkError` | 0 | 网络错误 |
| `AuthenticationError` | 401 | 认证失败 |
| `AuthorizationError` | 403 | 权限不足 |
| `ValidationError` | 400 | 验证失败 |
| `NotFoundError` | 404 | 资源不存在 |
| `RateLimitError` | 429 | 请求过于频繁 |
| `TimeoutError` | 0 | 请求超时 |

---

## 12. 分析追踪系统

### 使用方法

```tsx
import { useAnalytics } from '@/lib/analytics';

function AgentsPage() {
  const analytics = useAnalytics();

  useEffect(() => {
    analytics.pageView('/agents', 'Agents Page');
  }, []);

  const handleCreateAgent = async () => {
    analytics.agentAction('Create', agentId);
    // 创建逻辑
  };

  const handleRunWorkflow = async () => {
    analytics.workflowAction('Run', workflowId, { duration: 1200 });
    // 运行逻辑
  };

  return <div>...</div>;
}
```

### 追踪方法

| 方法 | 用途 |
|------|------|
| `pageView` | 追踪页面访问 |
| `action` | 追踪用户操作 |
| `agentAction` | 追踪 Agent 操作 |
| `workflowAction` | 追踪工作流操作 |
| `knowledgeAction` | 追踪知识库操作 |
| `toolAction` | 追踪工具使用 |
| `error` | 追踪错误 |
| `performance` | 追踪性能指标 |
| `engagement` | 追踪用户参与度 |
| `identify` | 识别用户 |

---

## 13. MCP 工具扩展

### 新增内置工具

| 工具 | 功能 |
|------|------|
| `text_summarizer` | 文本摘要 |
| `json_processor` | JSON 处理 |
| `hash_generator` | 哈希生成 |
| `base64_codec` | Base64 编解码 |
| `uuid_generator` | UUID 生成 |
| `regex_engine` | 正则表达式 |
| `date_time` | 日期时间处理 |

### 新增 MCP 工具

| 工具 | 功能 |
|------|------|
| `check_safety` | 安全检查 |
| `manage_memory` | 记忆管理 |
| `list_models` | 模型列表 |
| `manage_multi_agent` | 多 Agent 管理 |
| `get_platform_stats` | 平台统计 |

### 新增 MCP 资源

| 资源 | 功能 |
|------|------|
| `memory://{agent_id}` | Agent 记忆 |
| `stats://{metric_type}` | 平台统计 |
| `models://{provider_type}` | 模型提供者 |
| `crew://{crew_id}` | 多 Agent 团队 |

---

## 14. 健康检查增强

### 检查组件

| 组件 | 说明 |
|------|------|
| `database` | MySQL 数据库 |
| `redis` | Redis 缓存 |
| `milvus` | Milvus 向量数据库 |
| `neo4j` | Neo4j 图数据库 |
| `elasticsearch` | Elasticsearch 搜索引擎 |

### API 响应

```json
{
  "status": "ok",
  "version": "1.0.0",
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

## 15. API 客户端增强

### 新增功能

- 请求重试机制（指数退避）
- 请求 ID 追踪（X-Request-ID）
- 5xx 错误自动重试
- 网络错误自动重试

### 配置

```typescript
const api = new ApiClient({
  retryCount: 3,      // 最大重试次数
  retryDelay: 1000,   // 基础重试延迟（毫秒）
});
```

---

## 技术栈总结

### 前端新增依赖

- `zod` - 表单验证
- `framer-motion` - 动画
- `zundo` - 状态撤销/重做

### 后端新增功能

- 7 个内置工具
- 5 个 MCP 工具
- 4 个 MCP 资源
- 健康检查增强

---

**文档版本**: 1.0.0
**最后更新**: 2026-05-30

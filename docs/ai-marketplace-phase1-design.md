# AI市集 Phase 1 详细设计文档

## 一、设计概述

### 1.1 设计目标

在不改变现有技术架构的前提下，在当前Agent Engine Platform之上构建"AI市集"业务层，实现中国建材集团采购需求文档中Phase 1的核心功能：

1. **AI市集浏览与发现** — 资产广场、多维检索、详情展示
2. **自主上架申报流程** — 用户提交→管理员审核→授权范围上线
3. **多层级组织架构** — 纵向穿透式权限、递归可见视图
4. **管理员管控能力** — 下架、冻结、违规标记、批量操作

### 1.2 设计原则

- **引擎层不动** — 所有现有engine保持不变
- **业务层扩展** — 在platform层新增marketplace_service
- **API层新增** — 新增api/v1/marketplace.py路由模块
- **前端新增页面** — 新增marketplace相关页面，不影响现有页面
- **数据层扩展** — 新增模型和字段，不修改现有表结构（仅新增）

---

## 二、数据库设计

### 2.1 新增模型：MarketplaceItem（市集资产）

**表名**: `marketplace_items`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) PK | UUID主键 |
| tenant_id | String(36) FK | 所属租户 |
| creator_id | String(36) FK | 创建者用户ID |
| asset_type | String(20) | 资产类型: agent/knowledge_base/workflow |
| asset_id | String(36) | 关联资产ID |
| title | String(200) | 市集展示标题 |
| summary | String(500) | 简介摘要 |
| description | Text | 详细描述（Markdown） |
| cover_image | String(500) | 封面图URL |
| category | String(50) | 业务分类 |
| tags | JSON | 标签列表 |
| visibility | String(20) | 可见范围: private/department/tenant/public |
| status | String(20) | 状态: draft/pending_review/approved/published/rejected/frozen/takedown |
| reject_reason | Text | 驳回原因 |
| version | Integer | 版本号 |
| config_snapshot | JSON | 资产配置快照（用于克隆） |
| avg_rating | Float | 平均评分 |
| rating_count | Integer | 评分次数 |
| usage_count | Integer | 使用次数 |
| clone_count | Integer | 克隆次数 |
| featured | Boolean | 是否精选推荐 |
| promoted_level | String(20) | 提级层级: null/department/tenant/group |
| frozen_at | DateTime | 冻结时间 |
| frozen_reason | Text | 冻结原因 |
| published_at | DateTime | 发布时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 2.2 新增模型：MarketplaceReview（审核记录）

**表名**: `marketplace_reviews`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) PK | UUID主键 |
| item_id | String(36) FK | 市集资产ID |
| tenant_id | String(36) FK | 租户ID |
| submitter_id | String(36) FK | 提交者ID |
| reviewer_id | String(36) FK | 审核者ID |
| review_type | String(20) | 审核类型: publish/promote/demote |
| status | String(20) | 状态: pending/approved/rejected |
| comment | Text | 审核意见 |
| reviewed_at | DateTime | 审核时间 |
| created_at | DateTime | 提交时间 |

### 2.3 新增模型：MarketplaceRating（用户评分）

**表名**: `marketplace_ratings`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) PK | UUID主键 |
| item_id | String(36) FK | 市集资产ID |
| user_id | String(36) FK | 评分用户ID |
| tenant_id | String(36) FK | 用户所属租户 |
| score | Integer | 评分1-5 |
| comment | Text | 评价内容 |
| created_at | DateTime | 评分时间 |
| updated_at | DateTime | 更新时间 |

**唯一约束**: (item_id, user_id) — 每个用户对每个资产只能评分一次

### 2.4 新增模型：MarketplaceClone（克隆记录）

**表名**: `marketplace_clones`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) PK | UUID主键 |
| source_item_id | String(36) FK | 源市集资产ID |
| target_tenant_id | String(36) FK | 目标租户ID |
| target_asset_id | String(36) FK | 克隆出的新资产ID |
| cloner_id | String(36) FK | 克隆操作者ID |
| created_at | DateTime | 克隆时间 |

### 2.5 现有模型扩展

#### AgentModel 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| marketplace_item_id | String(36) nullable | 关联的市集资产ID |
| visibility | String(20) default "private" | 可见范围 |

#### TenantModel 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| parent_id | String(36) nullable | 上级租户ID（用于集团-子公司层级） |
| org_level | String(20) default "department" | 组织层级: group/subsidiary/department |
| org_path | String(500) | 组织路径（如 /group/sub1/dept2） |

#### DepartmentModel 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| external_code | String(50) | 外部系统组织编码（用于主数据同步） |

---

## 三、API设计

### 3.1 市集浏览 API（公开，需登录）

```
GET    /api/v1/marketplace/items          # 市集资产列表（支持搜索、筛选、排序）
GET    /api/v1/marketplace/items/{id}     # 资产详情
GET    /api/v1/marketplace/categories     # 分类列表
GET    /api/v1/marketplace/featured       # 精选推荐
GET    /api/v1/marketplace/hot            # 热门排行
```

**列表查询参数**:
- `keyword` — 关键词搜索（标题、描述）
- `category` — 分类筛选
- `tags` — 标签筛选（逗号分隔）
- `asset_type` — 资产类型筛选
- `sort_by` — 排序: latest/hottest/rating/usage
- `page`, `size` — 分页

**列表响应项**:
```json
{
  "id": "...",
  "title": "智能客服助手",
  "summary": "基于建材行业知识的智能客服...",
  "cover_image": "...",
  "category": "客户服务",
  "tags": ["客服", "建材", "FAQ"],
  "asset_type": "agent",
  "avg_rating": 4.5,
  "rating_count": 128,
  "usage_count": 1024,
  "clone_count": 56,
  "creator_tenant_name": "xx子公司",
  "creator_name": "张三",
  "published_at": "...",
  "featured": true,
  "promoted_level": "group"
}
```

### 3.2 试用 API

```
POST   /api/v1/marketplace/items/{id}/trial   # 创建试用会话
```

试用会话复用现有Chat API，但：
- 创建临时conversation，标记为trial
- 试用次数限制（每用户每天每资产最多5次）
- 试用不计入正式使用统计

### 3.3 评分 API

```
POST   /api/v1/marketplace/items/{id}/rating      # 提交/更新评分
GET    /api/v1/marketplace/items/{id}/ratings      # 获取评分列表
GET    /api/v1/marketplace/items/{id}/rating/me     # 获取当前用户评分
```

### 3.4 克隆 API

```
POST   /api/v1/marketplace/items/{id}/clone        # 克隆资产
```

克隆逻辑：
1. 读取源资产config_snapshot
2. 在目标租户下创建新资产（status=draft）
3. 记录克隆关系
4. 源资产clone_count+1

### 3.5 上架申报 API（需Contributor权限）

```
POST   /api/v1/marketplace/submissions                    # 提交上架申请
GET    /api/v1/marketplace/submissions                    # 查看我的提交记录
POST   /api/v1/marketplace/submissions/{id}/cancel        # 撤回提交
```

**提交请求体**:
```json
{
  "asset_type": "agent",
  "asset_id": "uuid-of-agent",
  "title": "智能客服助手",
  "summary": "基于建材行业知识的智能客服...",
  "description": "## 功能介绍\n...",
  "category": "客户服务",
  "tags": ["客服", "建材"],
  "visibility": "tenant"
}
```

### 3.6 审核管理 API（需Admin权限）

```
GET    /api/v1/marketplace/admin/reviews                 # 待审核列表
POST   /api/v1/marketplace/admin/reviews/{id}/approve    # 审核通过
POST   /api/v1/marketplace/admin/reviews/{id}/reject     # 审核驳回
```

### 3.7 资产管控 API（需Admin权限）

```
POST   /api/v1/marketplace/admin/items/{id}/freeze       # 冻结资产
POST   /api/v1/marketplace/admin/items/{id}/unfreeze     # 解冻资产
POST   /api/v1/marketplace/admin/items/{id}/takedown     # 强制下架
POST   /api/v1/marketplace/admin/items/{id}/promote      # 资产提级
POST   /api/v1/marketplace/admin/items/{id}/feature      # 设为精选
DELETE /api/v1/marketplace/admin/items/{id}/feature       # 取消精选
GET    /api/v1/marketplace/admin/items                    # 管理员资产列表（含跨级）
```

### 3.8 运营看板 API（需Admin权限）

```
GET    /api/v1/marketplace/admin/stats                   # 市集统计概览
GET    /api/v1/marketplace/admin/stats/trends            # 趋势数据
GET    /api/v1/marketplace/admin/stats/top-assets        # Top资产排行
GET    /api/v1/marketplace/admin/stats/org-coverage      # 组织覆盖统计
```

---

## 四、前端页面设计

### 4.1 新增路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/marketplace` | 市集首页 | 精选推荐、分类导航、热门排行、搜索 |
| `/marketplace/browse` | 浏览广场 | 完整资产列表、多维筛选 |
| `/marketplace/[id]` | 资产详情 | 详情展示、评分、评论、试用、克隆 |
| `/marketplace/submit` | 上架申报 | 选择资产、填写信息、提交审核 |
| `/marketplace/my-submissions` | 我的提交 | 提交记录、状态追踪 |
| `/marketplace/admin/reviews` | 审核中心 | 待审核列表、审核操作 |
| `/marketplace/admin/assets` | 资产管控 | 全量资产管控、下架/冻结/提级 |
| `/marketplace/admin/dashboard` | 运营看板 | 市集运营数据看板 |

### 4.2 市集首页设计

```
┌─────────────────────────────────────────────────────┐
│  [搜索栏]  [分类筛选]  [标签筛选]                      │
├─────────────────────────────────────────────────────┤
│  🌟 精选推荐                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│  │ 资产1 │ │ 资产2 │ │ 资产3 │ │ 资产4 │               │
│  │ ⭐4.8 │ │ ⭐4.6 │ │ ⭐4.5 │ │ ⭐4.4 │               │
│  └──────┘ └──────┘ └──────┘ └──────┘               │
├─────────────────────────────────────────────────────┤
│  🔥 热门排行                                          │
│  1. 智能客服助手  使用:1024  评分:4.5                   │
│  2. 合同审核助手  使用:856   评分:4.3                   │
│  ...                                                  │
├─────────────────────────────────────────────────────┤
│  📂 分类导航                                          │
│  [客户服务] [生产管理] [供应链] [财务] [人力] ...        │
├─────────────────────────────────────────────────────┤
│  📊 全部资产 (按 最新/最热/评分最高 排序)               │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│  │      │ │      │ │      │ │      │               │
│  └──────┘ └──────┘ └──────┘ └──────┘               │
└─────────────────────────────────────────────────────┘
```

### 4.3 资产详情页设计

```
┌─────────────────────────────────────────────────────┐
│  [封面图]   标题                                       │
│             分类 | 标签 | 来源: xx子公司                 │
│             ⭐ 4.5 (128评) | 🔥 1024次使用 | 📋 56次克隆│
│                                                      │
│             [立即试用]  [克隆到我的]                     │
├─────────────────────────────────────────────────────┤
│  [Tab] 详情介绍 | 编排逻辑 | 评价(128)                  │
├─────────────────────────────────────────────────────┤
│  ## 功能介绍                                          │
│  详细描述...                                           │
│                                                      │
│  ## 编排逻辑（白盒展示）                                │
│  ┌─────────────────────────────────┐                 │
│  │ [可视化流程图]                    │                 │
│  │ System Prompt → LLM → Tools     │                 │
│  │              ↓                  │                 │
│  │         Knowledge Base          │                 │
│  └─────────────────────────────────┘                 │
│                                                      │
│  ## 用户评价                                           │
│  ⭐⭐⭐⭐⭐ 张三 - 很好用 (2024-01-15)                  │
│  ⭐⭐⭐⭐  李四 - 不错，但可以改进 (2024-01-10)         │
│  [我要评价]                                            │
└─────────────────────────────────────────────────────┘
```

---

## 五、权限设计

### 5.1 新增RBAC权限资源

```python
# 新增权限资源
PERMISSIONS["marketplace"] = ["read", "submit", "review", "manage", "promote"]
```

### 5.2 角色权限矩阵

| 操作 | Viewer | Contributor | Admin | Owner |
|------|--------|-------------|-------|-------|
| 浏览市集 | ✅ | ✅ | ✅ | ✅ |
| 试用资产 | ✅ | ✅ | ✅ | ✅ |
| 评分评价 | ✅ | ✅ | ✅ | ✅ |
| 克隆资产 | ❌ | ✅ | ✅ | ✅ |
| 提交上架 | ❌ | ✅ | ✅ | ✅ |
| 审核资产 | ❌ | ❌ | ✅ | ✅ |
| 下架/冻结 | ❌ | ❌ | ✅ | ✅ |
| 资产提级 | ❌ | ❌ | ✅ | ✅ |
| 运营看板 | ❌ | ❌ | ✅ | ✅ |

### 5.3 可见范围逻辑

资产可见性遵循以下规则：
1. `private` — 仅创建者可见
2. `department` — 同部门可见
3. `tenant` — 同租户可见
4. `public` — 所有租户可见（需要approved/published状态）

穿透式可见：上级租户管理员可看到下级所有资产。

---

## 六、核心业务流程

### 6.1 上架审核流程

```
用户创建Agent → 编辑完善 → 点击"申请上架"
    ↓
填写市集信息（标题、简介、分类、标签）
    ↓
提交审核 → status: pending_review
    ↓
本级管理员审核
    ├─ 通过 → status: approved → 自动上线 → status: published
    └─ 驳回 → status: rejected + 驳回原因
         ↓
    用户修改后可重新提交
```

### 6.2 资产提级流程

```
管理员在运营看板发现优质资产
    ↓
点击"提级" → 选择提级层级（部门级/租户级/集团级）
    ↓
创建审核记录 → review_type: promote
    ↓
上级管理员审核
    ├─ 通过 → visibility扩大到目标层级
    └─ 驳回 → 保持原状
```

### 6.3 克隆流程

```
用户在详情页点击"克隆到我的"
    ↓
读取源资产config_snapshot
    ↓
在用户租户下创建新Agent（status: draft）
    ↓
复制system_prompt, tools, knowledge_base_ids, model_config
    ↓
记录克隆关系 → clone_count+1
    ↓
用户可在自己的Agent列表中编辑修改
```

---

## 七、文件清单

### 7.1 后端新增文件

```
backend/app/
├── models/
│   └── marketplace.py              # MarketplaceItem, Review, Rating, Clone模型
├── schemas/
│   └── marketplace.py              # 请求/响应Schema
├── api/v1/
│   └── marketplace.py              # API路由
├── platform/
│   └── marketplace_service/
│       ├── __init__.py
│       └── marketplace_service.py  # 业务逻辑层
└── alembic/versions/
    └── xxx_add_marketplace.py      # 数据库迁移
```

### 7.2 后端修改文件

```
backend/app/
├── models/__init__.py              # 新增marketplace模型导出
├── models/agent.py                 # AgentModel新增marketplace_item_id, visibility
├── models/tenant.py                # TenantModel新增parent_id, org_level, org_path
├── core/rbac.py                    # PERMISSIONS新增marketplace资源
├── api/v1/__init__.py              # 注册marketplace路由
└── schemas/__init__.py             # 新增marketplace schema导出
```

### 7.3 前端新增文件

```
frontend/src/
├── app/(platform)/marketplace/
│   ├── page.tsx                    # 市集首页
│   ├── browse/page.tsx             # 浏览广场
│   ├── [id]/page.tsx               # 资产详情
│   ├── submit/page.tsx             # 上架申报
│   ├── my-submissions/page.tsx     # 我的提交
│   └── admin/
│       ├── reviews/page.tsx        # 审核中心
│       ├── assets/page.tsx         # 资产管控
│       └── dashboard/page.tsx      # 运营看板
├── components/marketplace/
│   ├── AssetCard.tsx               # 资产卡片组件
│   ├── RatingStars.tsx             # 评分星星组件
│   ├── SearchFilters.tsx           # 搜索筛选组件
│   ├── WhiteBoxView.tsx            # 白盒化编排逻辑展示
│   └── ReviewForm.tsx              # 审核表单组件
└── types/marketplace.ts            # 市集相关类型定义
```

### 7.4 前端修改文件

```
frontend/src/
├── components/Sidebar.tsx          # 新增市集导航菜单项
├── lib/api.ts                      # 新增marketplace API方法
└── types/index.ts                  # 新增marketplace类型导出
```

---

## 八、实施计划

### Phase 1A: 数据层 + 基础API（第1-2周）
1. 创建marketplace模型
2. 创建数据库迁移
3. 创建Schemas
4. 实现marketplace_service
5. 实现基础CRUD API

### Phase 1B: 前端市集页面（第3周）
1. 市集首页
2. 浏览广场
3. 资产详情页
4. Sidebar导航更新

### Phase 1C: 审核流程 + 管控（第4周）
1. 上架申报流程
2. 审核中心
3. 管理员管控（下架/冻结/提级）
4. 运营看板

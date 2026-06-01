# AI市集 Phase 2 详细设计文档（10大增强模块）

> 基于采购需求文档逐条差距分析，本文档覆盖所有需要进一步设计和实施的功能增强点。

---

## 模块一：白盒化编排逻辑可视化

### 1.1 需求来源

采购文档 三(二)2："开放智能体核心编排逻辑可视化展示"
采购文档 三(三)1.2："开放智能体编排逻辑、流程细节白盒展示，帮助用户深度理解技术原理与应用场景"

### 1.2 当前状态

- 前端已有 `WorkflowCanvas` 组件（基于 `@xyflow/react`），支持 `readOnly` 模式
- AgentModel 存储 `system_prompt`, `tools`(JSON list), `knowledge_base_ids`(JSON list), `model_config`(JSON), `safety_config`(JSON)
- 但无将 Agent 配置转换为可视化流程图的逻辑

### 1.3 设计方案

#### 核心思路

将 Agent 的配置信息自动转换为一个**线性流程图**，展示 Agent 的完整编排逻辑：

```
[输入] → [System Prompt] → [LLM 推理] → [工具链] → [知识库检索] → [安全检查] → [输出]
```

#### 前端新增组件

**文件**: `frontend/src/components/marketplace/WhiteBoxView.tsx`

```tsx
// 组件接收 Agent 配置，自动生成 ReactFlow 节点和边
interface WhiteBoxViewProps {
  agentConfig: {
    system_prompt?: string;
    tools?: Array<{ name: string; type?: string }>;
    knowledge_base_ids?: string[];
    model_provider?: string;
    model_name?: string;
    model_config?: Record<string, any>;
    safety_config?: Record<string, any>;
  };
}
```

**节点生成逻辑**:

1. **输入节点** (type: `input`, color: `#1890ff`)
   - label: "用户输入"
   - config: `{ description: "用户发起的对话输入" }`

2. **System Prompt 节点** (type: `llm`, color: `#1890ff`)
   - label: "系统提示词"
   - config: `{ prompt: agentConfig.system_prompt, description: "定义Agent的角色和行为" }`
   - 仅在 `system_prompt` 非空时生成

3. **LLM 推理节点** (type: `llm`, color: `#1890ff`)
   - label: `${agentConfig.model_provider}/${agentConfig.model_name}`
   - config: `{ ...agentConfig.model_config, description: "大语言模型推理" }`

4. **工具链节点** (type: `tool`, color: `#52c41a`)
   - label: "工具调用"
   - config: `{ tools: agentConfig.tools, description: "可调用的外部工具列表" }`
   - 仅在 `tools` 非空时生成
   - 每个工具作为子节点展示

5. **知识库节点** (type: `knowledge`, color: `#722ed1`)
   - label: "知识库检索"
   - config: `{ knowledge_base_ids: agentConfig.knowledge_base_ids, description: "RAG检索增强" }`
   - 仅在 `knowledge_base_ids` 非空时生成

6. **安全检查节点** (type: `safety`, color: `#fa541c`)
   - label: "安全过滤"
   - config: `{ ...agentConfig.safety_config, description: "输入/输出安全检查" }`
   - 仅在 `safety_config` 非空时生成

7. **输出节点** (type: `output`, color: `#52c41a`)
   - label: "Agent响应"
   - config: `{ description: "最终输出给用户的响应" }`

**边生成逻辑**: 按顺序连接所有生成的节点，形成线性流程。

#### API 端点

**新增**: `GET /api/v1/marketplace/items/{item_id}/whitebox`

```python
@router.get("/items/{item_id}/whitebox")
async def get_whitebox_view(item_id: str, ...):
    """获取资产的白盒化编排逻辑."""
    svc = MarketplaceService(db)
    item = await svc.get_item(item_id)
    if not item:
        raise HTTPException(404, "Item not found")

    # 从config_snapshot中提取Agent配置
    config = item.get("config_snapshot", {})

    # 生成流程图数据
    nodes, edges = generate_whitebox_flow(config)

    return {"nodes": nodes, "edges": edges}
```

**后端新增函数** (`marketplace_service.py`):

```python
def _generate_whitebox_flow(self, config: dict) -> tuple[list, list]:
    """将Agent配置转换为可视化流程图节点和边."""
    nodes = []
    edges = []
    x, y = 0, 0
    step = 250  # 节点间距

    # 1. 输入节点
    nodes.append({
        "id": "input",
        "type": "custom",
        "label": "用户输入",
        "position": {"x": x, "y": y},
        "config": {"description": "用户发起的对话输入"},
        "style": {"background": "#1890ff"},
    })
    prev_id = "input"
    x += step

    # 2. System Prompt
    if config.get("system_prompt"):
        node_id = "system_prompt"
        nodes.append({
            "id": node_id,
            "type": "custom",
            "label": "系统提示词",
            "position": {"x": x, "y": y},
            "config": {
                "prompt": config["system_prompt"][:200] + "..." if len(config.get("system_prompt", "")) > 200 else config.get("system_prompt", ""),
                "description": "定义Agent的角色和行为规范",
            },
            "style": {"background": "#1890ff"},
        })
        edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        x += step

    # 3. LLM推理
    provider = config.get("model_provider", "")
    model = config.get("model_name", "")
    node_id = "llm"
    nodes.append({
        "id": node_id,
        "type": "custom",
        "label": f"LLM推理 ({provider}/{model})",
        "position": {"x": x, "y": y},
        "config": {
            "model_provider": provider,
            "model_name": model,
            "description": f"使用{provider}的{model}模型进行推理",
        },
        "style": {"background": "#1890ff"},
    })
    edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
    prev_id = node_id
    x += step

    # 4. 工具链
    tools = config.get("tools", [])
    if tools:
        node_id = "tools"
        tool_names = [t.get("name", t.get("function", {}).get("name", "unknown")) for t in tools]
        nodes.append({
            "id": node_id,
            "type": "custom",
            "label": f"工具调用 ({len(tools)}个)",
            "position": {"x": x, "y": y},
            "config": {
                "tools": tool_names,
                "description": f"可调用{len(tools)}个外部工具: {', '.join(tool_names[:5])}",
            },
            "style": {"background": "#52c41a"},
        })
        edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        x += step

    # 5. 知识库
    kb_ids = config.get("knowledge_base_ids", [])
    if kb_ids:
        node_id = "knowledge"
        nodes.append({
            "id": node_id,
            "type": "custom",
            "label": f"知识库检索 ({len(kb_ids)}个)",
            "position": {"x": x, "y": y},
            "config": {
                "knowledge_base_count": len(kb_ids),
                "description": f"从{len(kb_ids)}个知识库中检索相关文档片段",
            },
            "style": {"background": "#722ed1"},
        })
        edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        x += step

    # 6. 安全检查
    safety = config.get("safety_config", {})
    if safety:
        node_id = "safety"
        nodes.append({
            "id": node_id,
            "type": "custom",
            "label": "安全过滤",
            "position": {"x": x, "y": y},
            "config": {
                "description": "输入/输出内容安全检查（提示词注入检测、PII脱敏、敏感词过滤）",
            },
            "style": {"background": "#fa541c"},
        })
        edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        x += step

    # 7. 输出节点
    nodes.append({
        "id": "output",
        "type": "custom",
        "label": "Agent响应",
        "position": {"x": x, "y": y},
        "config": {"description": "最终输出给用户的响应"},
        "style": {"background": "#52c41a"},
    })
    edges.append({"id": f"e_{prev_id}_output", "source": prev_id, "target": "output"})

    return nodes, edges
```

#### 前端页面集成

在 `marketplace/[id]/page.tsx` 的"编排逻辑"Tab中，替换占位符为实际的 `WhiteBoxView` 组件：

```tsx
{
  key: 'whitebox',
  label: '编排逻辑',
  children: <WhiteBoxView item={item} />,
}
```

`WhiteBoxView` 组件调用 `GET /api/v1/marketplace/items/{id}/whitebox` 获取节点和边数据，然后使用 `WorkflowCanvas` 的 `readOnly` 模式渲染。

---

## 模块二：组织架构穿透式权限

### 2.1 需求来源

采购文档 三(四)2："与集团主数据平台实时同步组织架构信息，建立上级监管下级、逐级穿透的递归可见视图与权限管控体系"
验收标准 1："完成组织架构动态映射，实现纵向穿透可视、上级赋能下沉、本级自主管控"

### 2.2 当前状态

- `TenantModel` 已有 `parent_id`, `org_level`, `org_path` 字段，但无自引用relationship
- `DepartmentModel` 有完整的邻接表层级结构
- `auth.py` 的 `apply_data_scope` 支持 tenant/department/own 三种范围
- 但无跨租户穿透查询逻辑

### 2.3 设计方案

#### 2.3.1 TenantModel 增加自引用关系

```python
# tenant.py - TenantModel 新增 relationship
parent = relationship("TenantModel", remote_side="TenantModel.id", backref="children")
```

#### 2.3.2 组织架构服务

**新增文件**: `backend/app/platform/org_service/org_service.py`

```python
class OrgService:
    """组织架构穿透式权限服务."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_ancestors(self, tenant_id: str) -> list[str]:
        """获取租户的所有上级租户ID列表（从父到根）."""
        ancestors = []
        current_id = tenant_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            q = select(TenantModel.parent_id).where(TenantModel.id == current_id)
            result = await self.db.execute(q)
            parent_id = result.scalar_one_or_none()
            if parent_id:
                ancestors.append(parent_id)
            current_id = parent_id

        return ancestors

    async def get_tenant_descendants(self, tenant_id: str) -> list[str]:
        """获取租户的所有下级租户ID列表（BFS遍历）."""
        descendants = []
        queue = [tenant_id]
        visited = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if current != tenant_id:
                descendants.append(current)

            q = select(TenantModel.id).where(TenantModel.parent_id == current)
            result = await self.db.execute(q)
            children = [row[0] for row in result.all()]
            queue.extend(children)

        return descendants

    async def get_visible_tenant_ids(self, tenant_id: str, scope: str = "down") -> list[str]:
        """获取可见的租户ID列表.
        scope:
          - "self": 仅自身
          - "down": 自身+所有下级
          - "up": 自身+所有上级
          - "all": 自身+上级+下级
        """
        visible = [tenant_id]

        if scope in ("down", "all"):
            visible.extend(await self.get_tenant_descendants(tenant_id))

        if scope in ("up", "all"):
            visible.extend(await self.get_tenant_ancestors(tenant_id))

        return list(set(visible))

    async def sync_org_from_master(self, org_data: list[dict]) -> dict:
        """从集团主数据同步组织架构.
        org_data格式: [{"code": "xxx", "name": "xxx", "parent_code": "xxx", "level": "group/subsidiary/department"}]
        """
        synced = 0
        for org in org_data:
            q = select(TenantModel).where(TenantModel.code == org["code"])
            result = await self.db.execute(q)
            tenant = result.scalar_one_or_none()

            if tenant:
                tenant.name = org["name"]
                tenant.org_level = org.get("level", "department")
                # parent_code -> parent_id
                if org.get("parent_code"):
                    pq = select(TenantModel.id).where(TenantModel.code == org["parent_code"])
                    presult = await self.db.execute(pq)
                    parent_id = presult.scalar_one_or_none()
                    if parent_id:
                        tenant.parent_id = parent_id
                synced += 1
            else:
                # 创建新租户
                parent_id = None
                if org.get("parent_code"):
                    pq = select(TenantModel.id).where(TenantModel.code == org["parent_code"])
                    presult = await self.db.execute(pq)
                    parent_id = presult.scalar_one_or_none()

                new_tenant = TenantModel(
                    name=org["name"],
                    code=org["code"],
                    org_level=org.get("level", "department"),
                    parent_id=parent_id,
                )
                self.db.add(new_tenant)
                synced += 1

        await self.db.flush()

        # 更新org_path
        await self._update_all_org_paths()

        return {"synced": synced}

    async def _update_all_org_paths(self):
        """更新所有租户的org_path."""
        q = select(TenantModel)
        result = await self.db.execute(q)
        tenants = result.scalars().all()

        tenant_map = {t.id: t for t in tenants}

        for tenant in tenants:
            path_parts = []
            current = tenant
            visited = set()
            while current and current.id not in visited:
                visited.add(current.id)
                path_parts.append(current.name)
                current = tenant_map.get(current.parent_id)
            tenant.org_path = "/" + "/".join(reversed(path_parts))

        await self.db.flush()
```

#### 2.3.3 市集可见范围增强

在 `MarketplaceService.list_items` 中集成穿透式可见逻辑：

```python
async def list_items(self, tenant_id, user_id, ...):
    from app.platform.org_service.org_service import OrgService
    org_svc = OrgService(self.db)

    # 获取当前租户可见的所有租户ID（自身+下级+上级的public资产）
    visible_tenant_ids = await org_svc.get_visible_tenant_ids(tenant_id, scope="all")

    conditions = [
        MarketplaceItem.status.in_(["published", "approved"]),
        or_(
            MarketplaceItem.visibility == "public",
            MarketplaceItem.tenant_id.in_(visible_tenant_ids),
        ),
    ]
    # ... 其余逻辑不变
```

#### 2.3.4 管理员穿透式查看

**新增API**: `GET /api/v1/marketplace/admin/items/tree`

```python
@router.get("/admin/items/tree")
async def get_asset_tree(
    user=Depends(require_permission("marketplace", "manage")),
    tenant_id=Depends(get_tenant_id),
    db=Depends(get_db),
):
    """获取组织架构树+各节点资产数量."""
    org_svc = OrgService(db)
    mp_svc = MarketplaceService(db)

    # 获取所有下级租户
    descendant_ids = await org_svc.get_tenant_descendants(tenant_id)
    all_ids = [tenant_id] + descendant_ids

    # 统计每个租户的资产数
    stats = {}
    for tid in all_ids:
        count = await mp_svc.count_items_by_tenant(tid)
        if count > 0:
            stats[tid] = count

    # 构建树结构
    tree = await org_svc.build_org_tree(tenant_id, stats)
    return tree
```

---

## 模块三：双重审核流程

### 3.1 需求来源

采购文档 三(二)4："实行本级初审、跨级提级复核双重审核机制"
采购文档 三(三)2.1："负责本级用户智能体上架申请全流程审核，同步复核下级单位智能体提级发布申请"

### 3.2 当前状态

- 已有单级审核：`pending_review` → `approved`/`rejected`
- `MarketplaceReviewModel` 有 `review_type` 字段（publish/promote/demote）
- 但无跨级复核逻辑

### 3.3 设计方案

#### 审核状态机

```
用户提交 → pending_review (本级审核)
              ↓
         本级通过 → pending_promotion_review (需跨级复核) [仅visibility=public时]
              ↓
         上级通过 → approved → published
              ↓
         上级驳回 → rejected (回到提交者)
```

#### 状态定义扩展

| 状态 | 说明 |
|------|------|
| `draft` | 草稿 |
| `pending_review` | 待本级审核 |
| `pending_promotion_review` | 待上级复核（仅跨级提级时） |
| `approved` | 已通过 |
| `published` | 已发布 |
| `rejected` | 已驳回 |
| `frozen` | 已冻结 |
| `takedown` | 已下架 |

#### 审核流程逻辑

```python
async def approve_review(self, item_id, tenant_id, reviewer_id, comment=""):
    """审核通过."""
    item = await self._get_item(item_id, tenant_id)

    if item.status == "pending_review":
        # 本级审核通过
        if item.visibility == "public":
            # 需要跨级复核 → 提级到上级
            parent_tenant_id = await self._get_parent_tenant_id(tenant_id)
            if parent_tenant_id:
                item.status = "pending_promotion_review"
                # 创建复核审核记录
                review = MarketplaceReviewModel(
                    item_id=item.id,
                    tenant_id=parent_tenant_id,  # 上级租户
                    submitter_id=reviewer_id,
                    review_type="promote",
                    status="pending",
                )
                self.db.add(review)
                await self.db.flush()
                return {"id": item.id, "status": "pending_promotion_review", "message": "已提交上级复核"}
            else:
                # 无上级，直接通过
                item.status = "published"
                item.published_at = datetime.now(UTC).replace(tzinfo=None)
        else:
            # visibility=department/tenant，本级可直接决定
            item.status = "published"
            item.published_at = datetime.now(UTC).replace(tzinfo=None)

    elif item.status == "pending_promotion_review":
        # 上级复核通过
        item.status = "published"
        item.published_at = datetime.now(UTC).replace(tzinfo=None)

    # 更新审核记录
    # ... (同现有逻辑)

    await self.db.flush()
    return {"id": item.id, "status": item.status}
```

#### 新增API

```python
@router.get("/admin/reviews/pending-promotion")
async def list_pending_promotion_reviews(
    user=Depends(require_permission("marketplace", "review")),
    tenant_id=Depends(get_tenant_id),
    db=Depends(get_db),
):
    """列出待上级复核的提级申请."""
    svc = MarketplaceService(db)
    return await svc.list_pending_promotion_reviews(tenant_id)
```

---

## 模块四：资产变更日志

### 4.1 需求来源

验收标准 2："资产版本快照、变更日志全程可溯源、可查询"

### 4.2 当前状态

- `AgentVersionModel` 存储版本快照
- `OperationLogModel` 记录操作日志
- 但无针对市集资产的专门变更日志

### 4.3 设计方案

#### 新增模型

**文件**: `backend/app/models/marketplace.py` 新增

```python
class MarketplaceChangeLogModel(Base):
    """市集资产变更日志."""
    __tablename__ = "marketplace_change_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(36), ForeignKey("marketplace_items.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    operator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    change_type = Column(String(30), nullable=False)  # create/update/status_change/clone/promote/freeze/takedown
    field_name = Column(String(50), nullable=True)  # 变更的字段名
    old_value = Column(Text, nullable=True)  # 旧值(JSON字符串)
    new_value = Column(Text, nullable=True)  # 新值(JSON字符串)
    description = Column(String(500), default="")  # 变更描述
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    item = relationship("MarketplaceItem")
```

#### 变更记录逻辑

在 `MarketplaceService` 的关键操作中自动记录变更：

```python
async def _log_change(self, item_id, tenant_id, operator_id, change_type, field_name=None, old_value=None, new_value=None, description=""):
    """记录变更日志."""
    log = MarketplaceChangeLogModel(
        item_id=item_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        change_type=change_type,
        field_name=field_name,
        old_value=json.dumps(old_value, ensure_ascii=False) if old_value is not None else None,
        new_value=json.dumps(new_value, ensure_ascii=False) if new_value is not None else None,
        description=description,
    )
    self.db.add(log)
```

**触发点**:
- `submit_for_review` → `change_type="create"`
- `approve_review` / `reject_review` → `change_type="status_change"`
- `freeze_item` / `unfreeze_item` / `takedown_item` → `change_type="status_change"`
- `promote_item` → `change_type="promote"`
- `clone_item` → `change_type="clone"`

#### API 端点

```python
@router.get("/items/{item_id}/changelog")
async def get_changelog(item_id: str, page=1, size=20, ...):
    """获取资产变更日志."""
    # 查询 MarketplaceChangeLogModel，按 created_at 降序
```

#### 前端集成

在资产详情页新增"变更记录"Tab，展示变更日志表格。

---

## 模块五：末位清洗定时任务

### 5.1 需求来源

采购文档 三(二)5："依托用户真实评分、平台活跃度等数据，建立智能体末位清洗机制，保障平台资产质量"

### 5.2 设计方案

#### 清洗规则

| 条件 | 动作 |
|------|------|
| 上线≥30天 且 评分<2.0 且 使用<10次 | 自动标记为"待优化" |
| 上线≥90天 且 评分<1.5 且 使用<5次 | 自动冻结 |
| 连续90天使用次数=0 | 自动标记为"闲置" |

#### 新增 Celery 定时任务

**文件**: `backend/app/tasks/marketplace_tasks.py`

```python
from celery import shared_task
from datetime import datetime, UTC, timedelta

@shared_task(name="marketplace.cleanup_bottom_performers")
def cleanup_bottom_performers():
    """末位清洗定时任务 - 每日凌晨2点执行."""
    import asyncio
    asyncio.run(_async_cleanup())

async def _async_cleanup():
    from app.core.database import async_session_factory
    from app.models.marketplace import MarketplaceItem
    from sqlalchemy import select, and_, func

    async with async_session_factory() as db:
        now = datetime.now(UTC).replace(tzinfo=None)

        # 规则1: 上线≥30天 且 评分<2.0 且 使用<10次 → 标记待优化
        threshold_30d = now - timedelta(days=30)
        q1 = select(MarketplaceItem).where(
            and_(
                MarketplaceItem.status == "published",
                MarketplaceItem.published_at <= threshold_30d,
                MarketplaceItem.avg_rating < 2.0,
                MarketplaceItem.avg_rating > 0,  # 有评分的
                MarketplaceItem.usage_count < 10,
            )
        )
        result = await db.execute(q1)
        items = result.scalars().all()
        for item in items:
            item.status = "needs_optimization"  # 新增状态

        # 规则2: 上线≥90天 且 评分<1.5 且 使用<5次 → 冻结
        threshold_90d = now - timedelta(days=90)
        q2 = select(MarketplaceItem).where(
            and_(
                MarketplaceItem.status == "published",
                MarketplaceItem.published_at <= threshold_90d,
                MarketplaceItem.avg_rating < 1.5,
                MarketplaceItem.avg_rating > 0,
                MarketplaceItem.usage_count < 5,
            )
        )
        result = await db.execute(q2)
        items = result.scalars().all()
        for item in items:
            item.status = "frozen"
            item.frozen_at = now
            item.frozen_reason = "系统自动冻结：长期低评分低使用率"

        # 规则3: 连续90天使用次数=0 → 标记闲置
        q3 = select(MarketplaceItem).where(
            and_(
                MarketplaceItem.status == "published",
                MarketplaceItem.published_at <= threshold_90d,
                MarketplaceItem.usage_count == 0,
            )
        )
        result = await db.execute(q3)
        items = result.scalars().all()
        for item in items:
            item.status = "idle"  # 新增状态

        await db.commit()
```

#### Celery Beat 配置

```python
# celery_config.py
beat_schedule = {
    'marketplace-cleanup': {
        'task': 'marketplace.cleanup_bottom_performers',
        'schedule': crontab(hour=2, minute=0),  # 每日凌晨2点
    },
}
```

---

## 模块六：运营看板增强

### 6.1 需求来源

采购文档 三(三)2.4："动态监控智能体调用次数、Token消耗量、覆盖用户及企业数量、用户评分等核心数据"

### 6.2 当前状态

- `MarketplaceService.get_stats` 返回基础统计
- `UsageLogModel` / `ModelUsageDailyModel` 已有Token消耗数据
- 缺少：覆盖企业统计、运行时长、按租户/部门拆分

### 6.3 设计方案

#### 增强统计API

**扩展** `GET /api/v1/marketplace/admin/stats`

```python
async def get_enhanced_stats(self, tenant_id: str) -> dict:
    """增强版运营统计."""
    base_stats = await self.get_stats(tenant_id)

    # 1. 覆盖企业统计：有多少个租户发布了资产
    org_q = (
        select(
            MarketplaceItem.tenant_id,
            func.count(MarketplaceItem.id),
        )
        .where(
            MarketplaceItem.status.in_(["published", "approved"]),
        )
        .group_by(MarketplaceItem.tenant_id)
    )
    org_result = await self.db.execute(org_q)
    org_coverage = {row[0]: row[1] for row in org_result.all()}

    # 2. 覆盖用户统计：有多少用户使用过市集资产
    from app.models.conversation import ConversationModel
    user_q = (
        select(
            func.count(func.distinct(ConversationModel.user_id)),
        )
        .where(
            ConversationModel.agent_id.in_(
                select(AgentModel.id).where(
                    AgentModel.marketplace_item_id.isnot(None)
                )
            )
        )
    )
    user_result = await self.db.execute(user_q)
    covered_users = user_result.scalar() or 0

    # 3. Token消耗统计（关联UsageLogModel）
    from app.models.system import UsageLogModel
    token_q = (
        select(
            func.sum(UsageLogModel.total_tokens),
            func.sum(UsageLogModel.cost),
        )
        .where(
            UsageLogModel.tenant_id.in_([tenant_id]),  # 可扩展为下级租户
        )
    )
    token_result = await self.db.execute(token_q)
    token_row = token_result.one()

    # 4. 按租户统计资产分布
    tenant_q = (
        select(
            TenantModel.name,
            func.count(MarketplaceItem.id),
        )
        .join(TenantModel, MarketplaceItem.tenant_id == TenantModel.id)
        .where(MarketplaceItem.status.in_(["published", "approved"]))
        .group_by(TenantModel.name)
    )
    tenant_result = await self.db.execute(tenant_q)
    by_tenant = {row[0]: row[1] for row in tenant_result.all()}

    return {
        **base_stats,
        "covered_organizations": len(org_coverage),
        "covered_users": covered_users,
        "total_tokens": int(token_row[0] or 0),
        "total_cost": round(float(token_row[1] or 0), 2),
        "items_by_tenant": by_tenant,
        "org_coverage_detail": org_coverage,
    }
```

#### 新增趋势API

```python
@router.get("/admin/stats/trends")
async def get_stats_trends(
    days: int = Query(30, ge=7, le=365),
    user=Depends(require_permission("marketplace", "manage")),
    tenant_id=Depends(get_tenant_id),
    db=Depends(get_db),
):
    """获取市集趋势数据（按天）."""
    # 查询最近N天的每日新增资产数、使用次数、评分次数
    # 使用 MarketplaceChangeLogModel 和 MarketplaceRatingModel 的 created_at 按天聚合
```

#### 前端看板增强

在 `admin/dashboard/page.tsx` 中新增：
- 覆盖企业数量卡片
- 覆盖用户数量卡片
- Token消耗/成本卡片
- 按租户资产分布柱状图（ECharts）
- 趋势折线图（ECharts）

---

## 模块七：企业微信集成方案

### 7.1 需求来源

采购文档 三(一)1："搭建Web端、企业微信H5双端统一交互门户"
采购文档 三(四)4："集成企业微信、短信分级告警机制"
验收标准(四)："深度对接集团企业微信账号体系"

### 7.2 设计方案

#### 7.2.1 WeCom OAuth2 登录

**新增**: `backend/app/core/wecom_auth.py`

```python
"""企业微信OAuth2认证."""
import httpx
from app.config import settings

class WeComAuth:
    """企业微信OAuth2认证服务."""

    CORP_ID = settings.WECOM_CORP_ID  # 企业ID
    AGENT_ID = settings.WECOM_AGENT_ID  # 应用ID
    SECRET = settings.WECOM_SECRET  # 应用密钥

    @classmethod
    async def get_access_token(cls) -> str:
        """获取access_token."""
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {"corpid": cls.CORP_ID, "corpsecret": cls.SECRET}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            return data["access_token"]

    @classmethod
    async def get_user_info(cls, code: str) -> dict:
        """通过code获取用户信息."""
        token = await cls.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo?access_token={token}&code={code}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            return resp.json()
        # 返回: {"UserId": "xxx", "DeviceId": "xxx", "errcode": 0}

    @classmethod
    async def get_user_detail(cls, userid: str) -> dict:
        """获取用户详细信息."""
        token = await cls.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={token}&userid={userid}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            return resp.json()
        # 返回: {"userid": "xxx", "name": "张三", "department": [1, 2], "position": "工程师", ...}
```

#### 7.2.2 WeCom 登录 API

```python
# api/v1/auth.py 新增
@router.get("/wecom/login")
async def wecom_login_url():
    """获取企业微信OAuth2登录URL."""
    redirect_uri = settings.WECOM_REDIRECT_URI
    url = (
        f"https://open.work.weixin.qq.com/wwopen/sso/qrConnect"
        f"?appid={WeComAuth.CORP_ID}"
        f"&agentid={WeComAuth.AGENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state=random_state"
    )
    return {"url": url}

@router.get("/wecom/callback")
async def wecom_callback(code: str, db=Depends(get_db)):
    """企业微信OAuth2回调."""
    # 1. 通过code获取UserId
    user_info = await WeComAuth.get_user_info(code)
    userid = user_info.get("UserId")

    # 2. 获取用户详细信息
    detail = await WeComAuth.get_user_detail(userid)

    # 3. 查找或创建本地用户
    q = select(UserModel).where(UserModel.username == userid)
    result = await db.execute(q)
    user = result.scalar_one_or_none()

    if not user:
        # 根据department自动分配租户
        dept_ids = detail.get("department", [])
        tenant_id = await _map_wecom_dept_to_tenant(db, dept_ids)

        user = UserModel(
            username=userid,
            email=detail.get("email", ""),
            hashed_password="",  # WeCom用户无密码
            role="viewer",  # 默认角色
            tenant_id=tenant_id,
            status="active",
        )
        db.add(user)
        await db.flush()

    # 4. 生成JWT
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id})
    return {"access_token": token, "token_type": "bearer"}
```

#### 7.2.3 WeCom 消息通知

```python
# backend/app/core/wecom_notify.py
class WeComNotify:
    """企业微信消息通知."""

    @classmethod
    async def send_review_notification(cls, user_id: str, item_title: str, status: str):
        """发送审核结果通知."""
        # 通过webhook或应用消息发送
        message = {
            "touser": user_id,
            "msgtype": "markdown",
            "agentid": WeComAuth.AGENT_ID,
            "markdown": {
                "content": f"""
## AI市集审核通知
**资产名称**: {item_title}
**审核结果**: {"✅ 通过" if status == "approved" else "❌ 驳回"}
请登录平台查看详情。
"""
            }
        }
        await cls._send_message(message)

    @classmethod
    async def send_alert(cls, level: str, title: str, content: str):
        """发送告警通知（支持企业微信+短信）."""
        # 企业微信webhook
        webhook_url = settings.WECOM_WEBHOOK_URL
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={
                "msgtype": "markdown",
                "markdown": {
                    "content": f"## [{level}] {title}\n{content}"
                }
            })
```

#### 7.2.4 H5 移动端适配

前端需要：
1. 响应式布局（已有Ant Design基础支持）
2. `marketplace/page.tsx` 的卡片在移动端改为单列
3. 检测 User-Agent 判断是否在WeCom WebView中
4. 自动调用 WeCom JSSDK 实现免登

---

## 模块八：国密算法适配方案

### 8.1 需求来源

采购文档 五(四)："系统敏感数据采用国密算法加密存储"

### 8.2 设计方案

#### 集成点

| 当前实现 | 国密替换 | 说明 |
|----------|----------|------|
| `bcrypt` 密码哈希 | SM3 哈希 | `security.py` 的 `hash_password` / `verify_password` |
| AES-GCM API Key加密 | SM4-CBC 加密 | `security.py` 的 `encrypt_api_key` / `decrypt_api_key` |
| JWT签名(RS256/HS256) | SM2签名 | `security.py` 的 `create_access_token` / `decode_token` |
| HTTPS TLS | 国密TLS | Nginx/网关层配置 |

#### 实现方案

**新增文件**: `backend/app/core/sm_crypto.py`

```python
"""国密算法工具类."""
from gmssl import sm2, sm3, sm4
from gmssl.sm2 import CryptSM2
from gmssl.sm3 import sm3_hash
import os

class SM2Helper:
    """SM2非对称加密."""
    def __init__(self, private_key: str, public_key: str):
        self.crypt = CryptSM2(private_key=private_key, public_key=public_key)

    def encrypt(self, data: bytes) -> bytes:
        return self.crypt.encrypt(data)

    def decrypt(self, enc_data: bytes) -> bytes:
        return self.crypt.decrypt(enc_data)

    def sign(self, data: bytes) -> bytes:
        return self.crypt.sign(data)

    def verify(self, signature: bytes, data: bytes) -> bool:
        return self.crypt.verify(signature, data)


class SM3Helper:
    """SM3哈希算法."""
    @staticmethod
    def hash(data: str) -> str:
        return sm3_hash(data.encode())


class SM4Helper:
    """SM4对称加密."""
    def __init__(self, key: bytes):
        self.crypt = sm4.CryptSM4()
        self.crypt.set_key(key, sm4.SM4_ENCRYPT)

    def encrypt(self, data: bytes) -> bytes:
        return self.crypt.crypt_ecb(data)

    def decrypt(self, enc_data: bytes) -> bytes:
        self.crypt.set_key(self.key, sm4.SM4_DECRYPT)
        return self.crypt.crypt_ecb(enc_data)
```

#### 配置化切换

在 `config.py` 中新增：

```python
CRYPTO_BACKEND: str = "standard"  # "standard" 或 "gm" (国密)
SM2_PRIVATE_KEY: str = ""
SM2_PUBLIC_KEY: str = ""
SM4_KEY: str = ""
```

`security.py` 中根据配置动态选择加密后端：

```python
if settings.CRYPTO_BACKEND == "gm":
    from app.core.sm_crypto import SM3Helper as HashHelper
    from app.core.sm_crypto import SM4Helper as CipherHelper
else:
    # 使用标准 bcrypt + AES
```

---

## 模块九：等保三级技术方案

### 9.1 需求来源

采购文档 五(四)："满足网络安全等级保护三级标准，需配合采购人完成测评及备案工作"

### 9.2 等保三级安全加固清单

| 类别 | 要求 | 当前状态 | 加固措施 |
|------|------|----------|----------|
| **身份鉴别** | 双因素认证 | ⚠️ 仅密码 | 增加短信/邮件验证码 |
| **身份鉴别** | 登录失败锁定 | ✅ 已有IP限流 | 增加账号锁定（5次失败锁30分钟） |
| **身份鉴别** | 会话超时 | ⚠️ 仅JWT过期 | 增加前端会话超时（30分钟无操作自动登出） |
| **访问控制** | 最小权限原则 | ✅ RBAC已实现 | 增加默认角色权限审计 |
| **访问控制** | 权限分离 | ✅ 多角色 | 确认管理员/审计员/操作员分离 |
| **安全审计** | 审计日志 | ✅ OperationLog | 增加日志留存≥180天策略 |
| **安全审计** | 审计日志不可篡改 | ⚠️ 数据库可改 | 增加日志签名或写入只追加存储 |
| **数据完整性** | 传输加密 | ⚠️ 需确认HTTPS | 强制HTTPS，禁止HTTP |
| **数据完整性** | 存储加密 | ⚠️ 仅API Key | 扩展到敏感字段（密码、个人信息） |
| **数据保密性** | 敏感数据脱敏 | ✅ PII检测 | 确认脱敏策略覆盖所有PII |
| **数据备份** | 备份策略 | ⚠️ 未配置 | 配置每周全量+每日增量备份 |
| **入侵防范** | WAF | ⚠️ 无 | 部署WAF（Nginx ModSecurity或云WAF） |
| **入侵防范** | 漏洞扫描 | ⚠️ 无 | 定期漏洞扫描+依赖安全审计 |
| **恶意代码防范** | 防病毒 | ⚠️ 无 | 文件上传扫描（ClamAV） |

### 9.3 关键实施项

1. **HTTPS强制**: Nginx配置HTTP→HTTPS重定向+HSTS头
2. **安全头**: 添加CSP、X-Frame-Options、X-Content-Type-Options
3. **密码策略**: 最小8位+大小写+数字+特殊字符
4. **会话管理**: 前端30分钟无操作自动登出
5. **日志留存**: 配置日志归档策略≥180天
6. **备份策略**: MySQL每周全量+每日增量+异地备份
7. **依赖审计**: `pip audit` / `npm audit` 定期检查

---

## 模块十：监控告警方案

### 10.1 需求来源

采购文档 三(四)4："搭建全链路可观测运维平台，实时监测系统QPS、服务器负载、接口响应等核心指标"
采购文档 五(六)："全链路留存操作日志、访问日志、错误日志，日志留存时长≥180天；支持对接Prometheus+Grafana、ELK等主流监控系统"

### 10.2 设计方案

#### 10.2.1 Prometheus 指标暴露

**新增文件**: `backend/app/core/metrics.py`

```python
"""Prometheus指标定义."""
from prometheus_client import Counter, Histogram, Gauge, Info

# HTTP请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 业务指标
marketplace_items_total = Gauge(
    'marketplace_items_total',
    'Total marketplace items',
    ['status']
)

marketplace_ratings_total = Counter(
    'marketplace_ratings_total',
    'Total marketplace ratings',
    ['score']
)

marketplace_clones_total = Counter(
    'marketplace_clones_total',
    'Total marketplace clones'
)

# 系统指标
active_users = Gauge(
    'active_users',
    'Currently active users'
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens consumed',
    ['provider', 'model', 'type']  # type: prompt/completion
)
```

**中间件集成**: `backend/app/core/metrics_middleware.py`

```python
"""Prometheus指标采集中间件."""
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import http_requests_total, http_request_duration_seconds
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # 过滤健康检查和metrics端点
        if request.url.path not in ("/health", "/metrics"):
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

        return response
```

**Metrics端点**: `GET /metrics` (使用 `prometheus_client.make_asgi_app()`)

#### 10.2.2 Grafana Dashboard

预配置Dashboard JSON：

```json
{
  "dashboard": {
    "title": "AI市集运营监控",
    "panels": [
      {"title": "QPS", "targets": [{"expr": "rate(http_requests_total[5m])"}]},
      {"title": "响应时间P95", "targets": [{"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"}]},
      {"title": "错误率", "targets": [{"expr": "rate(http_requests_total{status_code=~'5..'}[5m]) / rate(http_requests_total[5m])"}]},
      {"title": "市集资产数", "targets": [{"expr": "marketplace_items_total"}]},
      {"title": "LLM调用量", "targets": [{"expr": "rate(llm_requests_total[5m])"}]},
      {"title": "Token消耗", "targets": [{"expr": "rate(llm_tokens_total[5m])"}]}
    ]
  }
}
```

#### 10.2.3 ELK 日志集成

**日志格式标准化**: JSON格式，包含字段：

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.api.v1.marketplace",
  "message": "Marketplace item created",
  "request_id": "uuid",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "method": "POST",
  "path": "/api/v1/marketplace/submissions",
  "status_code": 201,
  "duration_ms": 150,
  "ip": "10.0.0.1"
}
```

**Filebeat配置**:

```yaml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "ai-marketplace-%{+yyyy.MM.dd}"
```

#### 10.2.4 告警规则

```yaml
# Prometheus告警规则
groups:
  - name: ai-marketplace
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "错误率超过5%"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95响应时间超过3秒"

      - alert: HighCPU
        expr: process_cpu_seconds_total > 0.8
        for: 10m
        labels:
          severity: warning

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
```

**告警通知渠道**:
1. 企业微信Webhook（即时通知）
2. 短信（Critical级别）
3. 邮件（所有告警）

---

## 实施优先级与依赖关系

```
Phase 2A (第1周): 基础增强
├── G4 资产变更日志 [独立，低复杂度]
├── G5 末位清洗任务 [独立，低复杂度]
└── G6 运营看板增强 [独立，中复杂度]

Phase 2B (第2周): 核心功能
├── G1 白盒化可视化 [独立，中复杂度]
├── G3 双重审核流程 [依赖现有审核，中复杂度]
└── G2 组织架构穿透 [依赖TenantModel，高复杂度]

Phase 2C (第3周): 企业集成
├── G7 企业微信集成 [独立，高复杂度]
└── G8 国密算法适配 [独立，中复杂度]

Phase 2D (第4周): 安全合规
├── G9 等保三级适配 [依赖G8，高复杂度]
└── G10 监控告警 [独立，中复杂度]
```

### 文件清单汇总

| 模块 | 新增文件 | 修改文件 |
|------|----------|----------|
| G1 白盒化 | `components/marketplace/WhiteBoxView.tsx` | `marketplace/[id]/page.tsx`, `marketplace_service.py`, `api/marketplace.py` |
| G2 组织架构 | `platform/org_service/org_service.py` | `models/tenant.py`, `marketplace_service.py` |
| G3 双重审核 | — | `marketplace_service.py`, `api/marketplace.py`, `admin/reviews/page.tsx` |
| G4 变更日志 | — | `models/marketplace.py`, `marketplace_service.py`, `api/marketplace.py`, `[id]/page.tsx` |
| G5 末位清洗 | `tasks/marketplace_tasks.py` | — |
| G6 看板增强 | — | `marketplace_service.py`, `api/marketplace.py`, `admin/dashboard/page.tsx` |
| G7 企业微信 | `core/wecom_auth.py`, `core/wecom_notify.py` | `api/auth.py`, `config.py`, Sidebar.tsx |
| G8 国密 | `core/sm_crypto.py` | `core/security.py`, `config.py` |
| G9 等保 | — | `core/security.py`, Nginx配置, Docker配置 |
| G10 监控 | `core/metrics.py`, `core/metrics_middleware.py` | `main.py`, Docker Compose, 新增Grafana/FIlebeat配置 |

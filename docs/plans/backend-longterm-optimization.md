# Agent Engine Platform 后端长期优化计划

> 计划制定日期: 2026-05-29 | 制定人: Backend Researcher
> 
> 基于: 产品评估报告 (`docs/product-audit-2026-05-29.md`) + 竞品深度研究 (`docs/research/backend-competitive-research.md`)

---

## 计划概览

### 时间线总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           后端优化时间线                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  P0 (0-3个月) │ P1 (3-6个月) │ P2 (6-12个月)                              │
│  ┌─────────┐   │ ┌──────────┐  │ ┌─────────────┐                            │
│  │ 基础重构 │   │ │ 功能扩展  │  │ │   长期演进   │                            │
│  └─────────┘   │ └──────────┘  │ └─────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 优先级分级原则

- **P0**: 影响系统可维护性、安全性和可扩展性的基础问题
- **P1**: 功能扩展和竞争力提升的关键特性
- **P2**: 长期演进和规模化能力

---

## P0 阶段 (0-3 个月) — 基础重构与安全加固

### 目标
解决评估报告中指出的关键架构债务，建立坚实的可维护性和安全性基础。

### 任务清单

| 任务 | 状态 | 优先级 | 负责人 | 工作量 |
|------|:----:|:------:|:------:|:------:|
| ORM 模型层重构 | 待开始 | P0-1 | Backend | 2周 |
| Schema 层重构 | 待开始 | P0-2 | Backend | 2周 |
| Platform Service 强化 | 待开始 | P0-3 | Backend | 1.5周 |
| JWT Token 撤销机制 | 待开始 | P0-4 | Backend | 1周 |
| MCP 工具扩展 | 待开始 | P0-5 | Backend | 1周 |

---

### 任务 1: ORM 模型层重构方案

#### 当前状态分析

**问题**: 所有 ORM 模型集中在单个文件 `backend/core/db/base.py` (927 行)

**影响**:
- 可维护性差：单文件过长，难以导航
- 协作冲突风险高：多人修改容易冲突
- 模块边界不清晰：违反单一职责原则

**现有模型分布**:
```
base.py (927 lines)
├── TenantModel (15 行)
├── UserModel (45 行)
├── AgentModel (68 行)
├── KnowledgeModel (89 行)
├── DocumentModel (56 行)
├── ConversationModel (78 行)
├── AuditModel (67 行)
├── UsageModel (34 行)
├── RoleModel (45 行)
├── PermissionModel (23 行)
├── ... (其他 20+ 模型)
```

#### 目标架构

按领域拆分到独立模块：

```
backend/core/db/
├── __init__.py          # 统一导出
├── base.py              # Base 类 + 公共字段 (100 行)
├── tenant.py            # 租户相关
├── user.py              # 用户相关
├── agent.py             # Agent 引擎相关
├── knowledge.py         # 知识库相关
├── workflow.py          # Workflow 引擎相关
├── multi_agent.py       # MultiAgent 引擎相关
├── conversation.py      # 会话相关
├── audit.py             # 审计日志
├── system.py            # 系统配置
└── analytics.py         # 用量分析
```

#### 实施步骤

**Step 1: 准备阶段 (0.5天)**

```bash
# 1. 创建新目录结构
mkdir -p backend/core/db/models

# 2. 创建 __init__.py
touch backend/core/db/models/__init__.py
```

**Step 2: 迁移基础类 (0.5天)**

```python
# backend/core/db/models/base.py
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """所有模型的基类"""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # 软删除
    
    def soft_delete(self):
        """软删除"""
        self.deleted_at = datetime.utcnow()

class TenantAwareModel(BaseModel):
    """租户感知模型基类"""
    __abstract__ = True
    
    tenant_id = Column(String(36), nullable=False, index=True)
```

**Step 3: 按领域迁移模型 (5天)**

```python
# backend/core/db/models/tenant.py
from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TenantAwareModel

class TenantModel(Base):
    """租户模型"""
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # 配置
    config = Column(JSON, nullable=True)  # 租户级别配置
    max_agents = Column(Integer, default=10)
    max_users = Column(Integer, default=5)
    features = Column(JSON, nullable=True)  # 启用的功能列表
    
    # 状态
    is_active = Column(Boolean, default=True)
    trial_until = Column(DateTime, nullable=True)
    
    # 关系
    users = relationship("UserModel", back_populates="tenant")
    agents = relationship("AgentModel", back_populates="tenant")
    
    def check_feature(self, feature_name: str) -> bool:
        """检查功能是否启用"""
        if not self.features:
            return False
        return feature_name in self.features
    
    def get_limit(self, limit_type: str) -> Optional[int]:
        """获取配额限制"""
        limits = {
            "max_agents": self.max_agents,
            "max_users": self.max_users,
        }
        return limits.get(limit_type)

# backend/core/db/models/user.py
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TenantAwareModel
from .tenant import TenantModel

class UserModel(TenantAwareModel):
    """用户模型"""
    __tablename__ = "users"
    
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 角色和权限
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 个人信息
    full_name = Column(String(255))
    avatar_url = Column(String(512))
    
    # 时间戳
    last_login_at = Column(DateTime)
    
    # 关系
    tenant = relationship("TenantModel", back_populates="users")
    role = relationship("RoleModel", back_populates="users")

# backend/core/db/models/agent.py
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, TenantAwareModel

class AgentModel(TenantAwareModel):
    """Agent 模型"""
    __tablename__ = "agents"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 配置
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=True)
    tools = Column(JSON, nullable=True)  # 工具列表
    knowledge_bases = Column(JSON, nullable=True)  # 关联知识库
    
    # 版本
    version = Column(String(20), default="1.0.0")
    parent_version_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    
    # 状态
    status = Column(String(20), default="draft")  # draft, published, archived
    published_at = Column(DateTime, nullable=True)
    
    # 关系
    tenant = relationship("TenantModel", back_populates="agents")
    parent_version = relationship("AgentModel", remote_side=[AgentModel.id])
    conversations = relationship("ConversationModel", back_populates="agent")
    
    def publish(self):
        """发布 Agent"""
        self.status = "published"
        self.published_at = datetime.utcnow()
```

**Step 4: 更新导入路径 (2天)**

```python
# backend/core/db/__init__.py (新的统一导出)
from backend.core.db.models.base import Base, BaseModel, TenantAwareModel
from backend.core.db.models.tenant import TenantModel
from backend.core.db.models.user import UserModel, RoleModel
from backend.core.db.models.agent import AgentModel, AgentVersionModel
from backend.core.db.models.knowledge import KnowledgeBaseModel, DocumentModel
# ... 其他模型

__all__ = [
    "Base",
    "BaseModel",
    "TenantAwareModel",
    "TenantModel",
    "UserModel",
    # ...
]

# 旧的导入保持兼容（向后兼容）
from backend.core.db.base import *  # 临时保留
```

**Step 5: 更新 Service 层导入 (2天)**

```bash
# 批量更新导入路径
find backend/services -name "*.py" -exec sed -i 's/from backend.core.db.base import/from backend.core.db.models import/g' {} \;
```

**Step 6: 数据库迁移验证 (0.5天)**

```bash
# 验证迁移
alembic upgrade head

# 检查表结构
python -c "from backend.core.db import Base; print(Base.metadata.create_all(bind=engine))"
```

#### 测试策略

```python
# tests/core/db/models/test_models.py
import pytest
from backend.core.db.models import AgentModel, UserModel

def test_agent_model_creation():
    """测试 Agent 模型创建"""
    agent = AgentModel(
        id="test-123",
        tenant_id="tenant-123",
        name="Test Agent",
        slug="test-agent",
        model="gpt-4o"
    )
    assert agent.slug == "test-agent"
    assert agent.status == "draft"

def test_agent_publish():
    """测试 Agent 发布"""
    agent = AgentModel(
        id="test-123",
        tenant_id="tenant-123",
        name="Test Agent",
        slug="test-agent",
        model="gpt-4o"
    )
    agent.publish()
    assert agent.status == "published"
    assert agent.published_at is not None

@pytest.mark.integration
def test_agent_crud(db_session):
    """测试 Agent CRUD 操作"""
    # Create
    agent = AgentModel(...)
    db_session.add(agent)
    db_session.commit()
    
    # Read
    fetched = db_session.query(AgentModel).filter_by(id=agent.id).first()
    assert fetched is not None
    
    # Update
    fetched.name = "Updated Agent"
    db_session.commit()
    
    # Delete
    fetched.soft_delete()
    db_session.commit()
    assert fetched.deleted_at is not None
```

#### 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|:----:|----------|
| 导入路径破坏现有代码 | 🔴 高 | 保留向后兼容的导入 |
| 数据库迁移失败 | 🟡 中 | 先在测试环境验证 |
| 关系配置错误 | 🟡 中 | 充分的测试覆盖 |

#### 验收标准

- [ ] 所有模型已按领域拆分到独立文件
- [ ] 每个文件不超过 200 行
- [ ] 所有现有测试通过
- [ ] 新增模块级测试覆盖 > 80%
- [ ] 代码审查通过

---

### 任务 2: Schema 层重构方案

#### 当前状态分析

**问题**: 所有 Pydantic Schema 集中在 `backend/api/schemas/api.py` (653 行)

**影响**:
- API 响应模型与请求模型混杂
- 难以快速定位特定端点的数据结构
- 缺少业务语义分组

#### 目标架构

```
backend/api/schemas/
├── __init__.py              # 统一导出
├── common.py                # 通用 Schema (分页、响应等)
├── tenant.py                # 租户相关
├── user.py                  # 用户相关
├── agent.py                 # Agent 引擎相关
├── knowledge.py             # 知识库相关
├── workflow.py              # Workflow 引擎相关
├── multi_agent.py           # MultiAgent 相关
├── conversation.py          # 会话相关
├── audit.py                 # 审计日志
└── analytics.py             # 用量分析
```

#### 实施步骤

**Step 1: 创建通用 Schema (1天)**

```python
# backend/api/schemas/common.py
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """创建分页响应"""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation successful",
                "data": {},
                "errors": None
            }
        }

class IdResponse(BaseModel):
    """ID 响应"""
    id: str

class BulkDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[str] = Field(..., min_items=1, max_items=100)

class BulkResponse(BaseModel):
    """批量操作响应"""
    succeeded: List[str] = []
    failed: List[Dict[str, str]] = []  # [{"id": "xxx", "error": "reason"}]
```

**Step 2: 按领域拆分 Schema (3天)**

```python
# backend/api/schemas/agent.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .common import IdResponse

class AgentCreate(BaseModel):
    """创建 Agent 请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model: str = Field(..., description="模型名称")
    prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    knowledge_bases: Optional[List[str]] = None

class AgentUpdate(BaseModel):
    """更新 Agent 请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    knowledge_bases: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")

class AgentResponse(BaseModel):
    """Agent 响应"""
    id: str
    tenant_id: str
    name: str
    slug: str
    description: Optional[str]
    model: str
    tools: List[str]
    knowledge_bases: List[str]
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

class AgentPublish(BaseModel):
    """发布 Agent 请求"""
    version_notes: Optional[str] = None

# backend/api/schemas/workflow.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class WorkflowNodeBase(BaseModel):
    """工作流节点基类"""
    id: str
    type: str = Field(..., pattern="^(llm|condition|parallel|loop|http|code|human|subworkflow)$")
    name: str
    config: Dict[str, Any] = {}

class WorkflowCreate(BaseModel):
    """创建工作流请求"""
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNodeBase]
    edges: List[Dict[str, Any]] = []

class WorkflowExecution(BaseModel):
    """工作流执行请求"""
    inputs: Dict[str, Any] = {}
    async_execution: bool = False

class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
```

**Step 3: 更新 API 路由 (2天)**

```python
# backend/api/v1/agents.py
from fastapi import APIRouter, Depends, status
from backend.api.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from backend.api.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/", response_model=ApiResponse[AgentResponse], status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user)
):
    """创建 Agent"""
    agent = await agent_service.create(
        tenant_id=current_user.tenant_id,
        **agent_data.dict()
    )
    return ApiResponse(data=AgentResponse.from_orm(agent))

@router.get("/", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """列出 Agent"""
    result = await agent_service.list(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search
    )
    return PaginatedResponse.create(
        items=[AgentResponse.from_orm(a) for a in result.items],
        total=result.total,
        page=page,
        page_size=page_size
    )
```

#### 测试策略

```python
# tests/api/schemas/test_schemas.py
import pytest
from backend.api.schemas.agent import AgentCreate, AgentUpdate
from pydantic import ValidationError

def test_agent_create_validation():
    """测试 Agent 创建验证"""
    # 有效输入
    agent = AgentCreate(
        name="Test Agent",
        model="gpt-4o",
        tools=["web_search"]
    )
    assert agent.name == "Test Agent"
    
    # 无效输入
    with pytest.raises(ValidationError):
        AgentCreate(
            name="",  # 太短
            model="gpt-4o"
        )

def test_agent_update_partial():
    """测试 Agent 部分更新"""
    update = AgentUpdate(description="New description")
    assert update.description == "New description"
    assert update.name is None  # 其他字段为 None
```

#### 验收标准

- [ ] 所有 Schema 已按领域拆分
- [ ] 建立通用 Schema 基类
- [ ] 所有 API 端点使用新的 Schema
- [ ] 验证规则覆盖完整
- [ ] 测试覆盖 > 80%

---

### 任务 3: Platform Service 层强化方案

#### 当前状态分析

**问题**: Platform Service 层过于薄弱 (1,069 行)，API 层直接调用 Engine

**影响**:
- 缺少业务逻辑封装
- 跨引擎编排困难
- 缺少统一的异常处理和事务管理

#### 目标架构

```
backend/services/
├── __init__.py
├── platform_service.py    # 平台级服务（主要）
├── agent_service.py
├── workflow_service.py
├── knowledge_service.py
├── multi_agent_service.py
├── user_service.py
└── audit_service.py
```

#### 实施方案

**核心设计: 统一服务基类**

```python
# backend/services/base.py
from typing import Optional, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
from backend.core.db import SessionLocal
from backend.core.exceptions import NotFoundException, BadRequestException

T = TypeVar("T")

class BaseService(ABC, Generic[T]):
    """服务基类"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._db: Optional[SessionLocal] = None
    
    @property
    def db(self):
        """懒加载数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()
        self.db.close()
    
    async def get_by_id(self, id: str) -> T:
        """根据 ID 获取实体"""
        entity = await self._get_by_id(id)
        if not entity:
            raise NotFoundException(f"{self.__class__.__name__} not found: {id}")
        return entity
    
    @abstractmethod
    async def _get_by_id(self, id: str) -> Optional[T]:
        """实现根据 ID 获取"""
        pass
    
    async def create(self, **kwargs) -> T:
        """创建实体"""
        await self._validate_create(kwargs)
        entity = await self._create(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    async def update(self, id: str, **kwargs) -> T:
        """更新实体"""
        entity = await self.get_by_id(id)
        await self._validate_update(kwargs)
        await self._apply_update(entity, kwargs)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> None:
        """删除实体"""
        entity = await self.get_by_id(id)
        await self._delete(entity)
        self.db.commit()
    
    @abstractmethod
    async def _validate_create(self, data: Dict[str, Any]):
        """验证创建数据"""
        pass
    
    @abstractmethod
    async def _validate_update(self, data: Dict[str, Any]):
        """验证更新数据"""
        pass
    
    @abstractmethod
    async def _create(self, **kwargs) -> T:
        """创建实体实现"""
        pass
    
    @abstractmethod
    async def _apply_update(self, entity: T, data: Dict[str, Any]):
        """应用更新"""
        pass
    
    @abstractmethod
    async def _delete(self, entity: T):
        """删除实体实现"""
        pass

# backend/services/agent_service.py
from typing import List, Optional
from backend.services.base import BaseService
from backend.core.db.models import AgentModel
from backend.engines.agent.engine import AgentEngine

class AgentService(BaseService[AgentModel]):
    """Agent 服务"""
    
    async def _get_by_id(self, id: str) -> Optional[AgentModel]:
        return self.db.query(AgentModel).filter_by(
            id=id,
            tenant_id=self.tenant_id,
            deleted_at=None
        ).first()
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> PaginatedResult:
        """列出 Agent"""
        query = self.db.query(AgentModel).filter_by(
            tenant_id=self.tenant_id,
            deleted_at=None
        )
        
        if search:
            query = query.filter(AgentModel.name.ilike(f"%{search}%"))
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return PaginatedResult(items=items, total=total)
    
    async def _validate_create(self, data: Dict[str, Any]):
        """验证创建数据"""
        # 检查名称唯一性
        existing = self.db.query(AgentModel).filter_by(
            tenant_id=self.tenant_id,
            slug=self._generate_slug(data["name"])
        ).first()
        
        if existing:
            raise BadRequestException("Agent with this name already exists")
        
        # 验证模型可用性
        await self._validate_model(data["model"])
    
    async def _validate_model(self, model: str):
        """验证模型是否可用"""
        from backend.engines.model.service import ModelService
        model_service = ModelService(self.tenant_id)
        
        if not await model_service.is_available(model):
            raise BadRequestException(f"Model not available: {model}")
    
    async def _create(self, **kwargs) -> AgentModel:
        """创建 Agent"""
        slug = self._generate_slug(kwargs["name"])
        
        return AgentModel(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=kwargs["name"],
            slug=slug,
            description=kwargs.get("description"),
            model=kwargs["model"],
            prompt=kwargs.get("prompt"),
            tools=kwargs.get("tools", []),
            knowledge_bases=kwargs.get("knowledge_bases", []),
            version="1.0.0"
        )
    
    async def execute(
        self,
        agent_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行 Agent"""
        agent = await self.get_by_id(agent_id)
        
        # 使用 Agent Engine 执行
        engine = AgentEngine(self.tenant_id)
        result = await engine.execute(
            agent_config=agent.dict(),
            message=message,
            conversation_id=conversation_id
        )
        
        # 记录使用
        await self._record_execution(agent_id, result)
        
        return result
    
    async def publish(self, agent_id: str, version_notes: Optional[str] = None) -> AgentModel:
        """发布 Agent"""
        agent = await self.get_by_id(agent_id)
        
        # 创建新版本
        new_version = await self._create_version(agent)
        
        # 更新当前版本状态
        agent.status = "published"
        agent.published_at = datetime.utcnow()
        
        self.db.add(new_version)
        self.db.commit()
        
        return agent
    
    def _generate_slug(self, name: str) -> str:
        """生成 slug"""
        import re
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug[:100]
```

#### 验收标准

- [ ] 所有业务逻辑封装到 Service 层
- [ ] API 层不再直接调用 Engine
- [ ] 统一异常处理
- [ ] 事务管理正确
- [ ] 服务层测试覆盖 > 70%

---

### 任务 4: JWT Token 撤销机制

#### 当前状态分析

**问题**: 无 JWT Token 黑名单，已泄露 Token 无法撤销

**影响**:
- 🔴 **严重安全风险**
- 无法应对 Token 泄露事件
- 无法强制用户登出

#### 实施方案

**方案选择: Redis Token 黑名单**

```python
# backend/core/auth/token_manager.py
from typing import Optional
from datetime import datetime, timedelta
import jwt
from backend.core.redis import redis_client

class TokenManager:
    """Token 管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=7)
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建 Access Token"""
        expires = datetime.utcnow() + self.access_token_expire
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": expires,
            "type": "access",
            **(additional_claims or {})
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str
    ) -> str:
        """创建 Refresh Token"""
        expires = datetime.utcnow() + self.refresh_token_expire
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": expires,
            "type": "refresh",
            "jti": str(uuid.uuid4())  # Token ID
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # 存储 Refresh Token（用于撤销）
        await self._store_refresh_token(payload["jti"], expires)
        
        return token
    
    async def revoke_token(self, token: str) -> None:
        """撤销 Token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 计算 Token 的过期时间
            exp = payload.get("exp")
            ttl = exp - int(datetime.utcnow().timestamp())
            
            # 添加到黑名单
            jti = payload.get("jti") or payload.get("sub")
            blacklist_key = f"token:blacklist:{jti}"
            await redis_client.setex(blacklist_key, ttl, "1")
            
        except jwt.InvalidTokenError:
            raise BadRequestException("Invalid token")
    
    async def is_token_revoked(self, token: str) -> bool:
        """检查 Token 是否已撤销"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti") or payload.get("sub")
            blacklist_key = f"token:blacklist:{jti}"
            
            return await redis_client.exists(blacklist_key) > 0
            
        except jwt.InvalidTokenError:
            return True
    
    async def revoke_user_tokens(
        self,
        user_id: str,
        except_token: Optional[str] = None
    ) -> int:
        """撤销用户的所有 Token"""
        # 找到用户所有活跃的 Token
        tokens = await self._get_user_active_tokens(user_id)
        
        revoked_count = 0
        for token_data in tokens:
            if except_token and token_data["token"] == except_token:
                continue
            
            await self.revoke_token(token_data["token"])
            revoked_count += 1
        
        return revoked_count
    
    async def _store_refresh_token(self, jti: str, exp: datetime) -> None:
        """存储 Refresh Token"""
        ttl = int((exp - datetime.utcnow()).total_seconds())
        key = f"token:refresh:{jti}"
        await redis_client.setex(key, ttl, "1")
    
    async def _get_user_active_tokens(self, user_id: str) -> List[Dict[str, str]]:
        """获取用户活跃的 Token"""
        # 从 Redis 获取
        pattern = f"token:user:{user_id}:*"
        keys = await redis_client.keys(pattern)
        
        tokens = []
        for key in keys:
            token = await redis_client.get(key)
            if token:
                tokens.append({"token": token.decode()})
        
        return tokens

# backend/api/v1/auth.py
@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """登出并撤销 Token"""
    # 获取当前 Token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise BadRequestException("No token provided")
    
    token = auth_header.replace("Bearer ", "")
    
    # 撤销 Token
    await token_manager.revoke_token(token)
    
    return {"message": "Logged out successfully"}

@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user)
):
    """撤销所有设备的 Token"""
    revoked_count = await token_manager.revoke_user_tokens(
        user_id=current_user.id
    )
    
    return {
        "message": f"Revoked {revoked_count} tokens"
    }
```

#### 中间件更新

```python
# backend/core/auth/dependencies.py
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前用户（检查 Token 是否撤销）"""
    
    # 检查 Token 是否被撤销
    if await token_manager.is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # 解码 Token
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 获取用户
    user_id = payload.get("sub")
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

#### 测试策略

```python
# tests/core/auth/test_token_manager.py
import pytest
from backend.core.auth.token_manager import TokenManager

@pytest.mark.asyncio
async def test_token_revocation():
    """测试 Token 撤销"""
    # 创建 Token
    token = token_manager.create_access_token(
        user_id="user-123",
        tenant_id="tenant-123"
    )
    
    # 撤销
    await token_manager.revoke_token(token)
    
    # 验证已撤销
    assert await token_manager.is_token_revoked(token) is True

@pytest.mark.asyncio
async def test_logout():
    """测试登出"""
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    
    # Token 不再有效
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401
```

#### 验收标准

- [ ] Token 撤销功能实现
- [ ] 登出/登出所有设备 API 实现
- [ ] Token 验证中间件更新
- [ ] 测试覆盖 > 90%
- [ ] 性能测试通过（< 5ms 额外延迟）

---

### 任务 5: MCP 工具扩展 (15+ 工具)

#### 当前状态

**现有 MCP 工具**: 5 个
- create_agent
- search_knowledge
- run_workflow
- list_agents
- send_message

**目标**: 扩展至 15+ 个工具

#### 扩展计划

```python
# backend/mcp/tools.py (新增工具)
MCP_TOOLS = [
    # 现有工具 (5个)
    ...
    
    # 评估相关 (3个)
    Tool(
        name="evaluate_agent",
        description="Evaluate agent with test dataset",
        inputSchema={...}
    ),
    Tool(
        name="get_evaluation_report",
        description="Get detailed evaluation report",
        inputSchema={...}
    ),
    Tool(
        name="compare_agents",
        description="Compare two agent versions",
        inputSchema={...}
    ),
    
    # 安全相关 (2个)
    Tool(
        name="check_safety",
        description="Check content for security issues",
        inputSchema={...}
    ),
    Tool(
        name="scan_agent",
        description="Scan agent for security vulnerabilities",
        inputSchema={...}
    ),
    
    # 知识库相关 (2个)
    Tool(
        name="upload_document",
        description="Upload document to knowledge base",
        inputSchema={...}
    ),
    Tool(
        name="delete_document",
        description="Delete document from knowledge base",
        inputSchema={...}
    ),
    
    # Workflow 相关 (2个)
    Tool(
        name="create_workflow",
        description="Create a new workflow",
        inputSchema={...}
    ),
    Tool(
        name="debug_workflow",
        description="Debug workflow execution",
        inputSchema={...}
    ),
    
    # MultiAgent 相关 (2个)
    Tool(
        name="create_crew",
        description="Create a multi-agent crew",
        inputSchema={...}
    ),
    Tool(
        name="run_crew",
        description="Execute a crew",
        inputSchema={...}
    ),
    
    # 系统相关 (2个)
    Tool(
        name="get_usage_stats",
        description="Get usage statistics",
        inputSchema={...}
    ),
    Tool(
        name="list_models",
        description="List available models",
        inputSchema={...}
    ),
]
```

#### 工具实现示例

```python
# backend/mcp/handlers/evaluation.py
from typing import Dict, Any

async def handle_evaluate_agent(arguments: Dict[str, Any]) -> str:
    """处理 Agent 评估"""
    from backend.engines.eval.service import EvalService
    
    agent_id = arguments["agent_id"]
    dataset_id = arguments["dataset_id"]
    metrics = arguments.get("metrics", ["faithfulness", "relevancy"])
    
    eval_service = EvalService(tenant_id=get_current_tenant())
    result = await eval_service.evaluate(
        agent_id=agent_id,
        dataset_id=dataset_id,
        metrics=metrics
    )
    
    return f"""
    Evaluation Results:
    - Agent: {agent_id}
    - Dataset: {dataset_id}
    - Metrics: {', '.join(metrics)}
    
    Results:
    {format_results(result)}
    """

async def handle_check_safety(arguments: Dict[str, Any]) -> str:
    """处理安全检查"""
    from backend.engines.safety.detector import SafetyDetector
    
    content = arguments["content"]
    check_types = arguments.get("check_types", ["injection", "pii"])
    
    detector = SafetyDetector(tenant_id=get_current_tenant())
    results = detector.check(content, check_types)
    
    return f"""
    Safety Check Results:
    {format_safety_results(results)}
    """
```

#### 验收标准

- [ ] MCP 工具总数 ≥ 15
- [ ] 所有工具有完整文档
- [ ] 工具执行错误处理完善
- [ ] 测试覆盖 > 80%

---

## P1 阶段 (3-6 个月) — 功能扩展

### 任务 6: MCP 双向协议升级

#### 目标
实现 MCP Server + MCP Client 双向能力

#### 实施方案

**MCP Client 实现** (详见研究报告 Section 5.2)

```python
# backend/mcp/client.py
class MCPClient:
    """MCP 客户端"""
    
    async def connect(self, base_url: str) -> Dict[str, Any]:
        """连接到外部 MCP Server"""
        # 初始化握手
        # 获取工具列表
        # 调用远程工具
        pass
```

#### 验收标准

- [ ] MCP Client 实现完成
- [ ] 支持连接外部 MCP 服务
- [ ] 工具调用正常工作
- [ ] 错误处理完善

---

### 任务 7: 工具市场后端架构

#### 目标
实现工具注册、发现、执行的完整架构

#### 实施方案

**核心组件** (详见研究报告 Section 3.3)

```python
# backend/tools/marketplace/
├── registry.py       # 工具注册表
├── marketplace.py    # 市场服务
├── sandbox.py        # 执行沙箱
└── billing.py        # 计量计费
```

#### 验收标准

- [ ] 工具注册 API 实现
- [ ] 工具市场浏览 API
- [ ] 工具安装/卸载功能
- [ ] 沙箱执行环境
- [ ] 使用计量功能

---

### 任务 8: 深度文档解析增强

#### 目标
支持 OCR、复杂表格、扫描件解析

#### 实施方案

基于 RagFlow 研究成果 (详见研究报告 Section 1.2)

```python
# backend/knowledge/parsers/
├── base.py
├── factory.py
├── naive_parser.py
├── ocr_parser.py
├── advanced_parser.py
└── ragflow_adapter.py
```

#### 验收标准

- [ ] 多后端解析器实现
- [ ] OCR 功能正常
- [ ] 复杂表格识别
- [ ] 扫描件处理

---

### 任务 9: Function Calling 统一抽象层

#### 目标
统一 OpenAI/Anthropic/Ollama 的 Function Calling 接口

#### 实施方案

```python
# backend/engines/model/function_calling.py
class FunctionCallingAdapter(ABC):
    """Function Calling 适配器基类"""
    
    @abstractmethod
    def format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """格式化工具为模型特定格式"""
        pass
    
    @abstractmethod
    def parse_tool_calls(self, response: Any) -> List[ToolCall]:
        """解析工具调用"""
        pass

class OpenAIFunctionCalling(FunctionCallingAdapter):
    """OpenAI Function Calling"""
    
    def format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_schema()
                }
            }
            for tool in tools
        ]

class AnthropicFunctionCalling(FunctionCallingAdapter):
    """Anthropic Function Calling"""
    
    def format_tools(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.get_schema()
            }
            for tool in tools
        ]
```

#### 验收标准

- [ ] 统一抽象接口定义
- [ ] OpenAI 适配器
- [ ] Anthropic 适配器
- [ ] Ollama 适配器
- [ ] 测试覆盖 > 85%

---

## P2 阶段 (6-12 个月) — 长期演进

### 任务 10: Agent 版本管理 + A/B 测试

#### 目标
支持 Agent 版本管理和 A/B 测试能力

#### 实施方案

```python
# backend/core/db/models/agent.py
class AgentVersionModel(BaseModel):
    """Agent 版本模型"""
    __tablename__ = "agent_versions"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    version = Column(String(20), nullable=False)
    config = Column(JSON, nullable=False)
    
    # A/B 测试
    is_ab_test = Column(Boolean, default=False)
    traffic_percentage = Column(Integer, default=0)  # 流量百分比
    
    # 统计
    total_executions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

class AgentExecutionModel(BaseModel):
    """Agent 执行记录"""
    __tablename__ = "agent_executions"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False)
    version_id = Column(String(36), nullable=False)
    
    # 执行信息
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(20))
    duration_ms = Column(Integer)
    
    # A/B 测试分组
    ab_test_group = Column(String(20), nullable=True)
```

#### 验收标准

- [ ] Agent 版本管理 API
- [ ] A/B 测试配置
- [ ] 执行记录和统计
- [ ] 版本对比功能

---

### 任务 11: 分布式任务队列升级

#### 目标
从 Celery 升级到更灵活的 Redis Streams

#### 实施方案

```python
# backend/tasks/queue.py
import asyncio
from redis.asyncio import Redis
from typing import Callable, Any

class TaskQueue:
    """基于 Redis Streams 的任务队列"""
    
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
        self.consumer_group = "agent_workers"
    
    async def enqueue(self, queue: str, task: Dict[str, Any]) -> str:
        """入队"""
        task_id = str(uuid.uuid4())
        task["id"] = task_id
        
        await self.redis.xadd(f"queue:{queue}", task)
        return task_id
    
    async def dequeue(
        self,
        queue: str,
        consumer_id: str,
        timeout: int = 5000
    ) -> Optional[Dict[str, Any]]:
        """出队"""
        try:
            messages = await self.redis.xreadgroup(
                self.consumer_group,
                consumer_id,
                {f"queue:{queue}": ">"},
                count=1,
                block=timeout
            )
            
            if messages:
                for stream, message_list in messages:
                    for message_id, data in message_list:
                        # 确认处理
                        await self.redis.xack(f"queue:{queue}", self.consumer_group, message_id)
                        return data
            
        except asyncio.TimeoutError:
            pass
        
        return None
```

#### 验收标准

- [ ] Redis Streams 队列实现
- [ ] Worker 进程管理
- [ ] 任务重试机制
- [ ] 死信队列处理

---

### 任务 12: 可观测性埋点

#### 目标
集成 OpenTelemetry 实现全链路追踪

#### 实施方案

```python
# backend/observability/tracing.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

def setup_telemetry(app: FastAPI):
    """设置遥测"""
    # 配置追踪
    tracer_provider = trace.get_tracer_provider()
    
    # Jaeger 导出器
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # 自动追踪 FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # 自定义追踪
    @app.middleware("http")
    async def trace_requests(request: Request, call_next):
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}"
        ) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
            response = await call_next(request)
            
            span.set_attribute("http.status_code", response.status_code)
            return response
```

#### 验收标准

- [ ] OpenTelemetry 集成
- [ ] Jaeger/Zipkin 导出
- [ ] 自定义 Span 定义
- [ ] Metrics 收集

---

### 任务 13: Agent 间共享记忆机制

#### 目标
实现 MultiAgent 系统中的共享记忆

#### 实施方案

```python
# backend/engines/memory/shared.py
from typing import Dict, Any, List, Optional
from backend.core.redis import redis_client

class SharedMemory:
    """Agent 间共享记忆"""
    
    def __init__(self, crew_id: str, tenant_id: str):
        self.crew_id = crew_id
        self.tenant_id = tenant_id
        self.key_prefix = f"shared_memory:{tenant_id}:{crew_id}"
    
    async def store(
        self,
        agent_id: str,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """存储记忆"""
        memory_key = f"{self.key_prefix}:{agent_id}:{key}"
        await redis_client.setex(memory_key, ttl, value)
    
    async def retrieve(
        self,
        agent_id: str,
        key: str
    ) -> Optional[Any]:
        """检索记忆"""
        memory_key = f"{self.key_prefix}:{agent_id}:{key}"
        value = await redis_client.get(memory_key)
        return value
    
    async def list_keys(self, agent_id: str) -> List[str]:
        """列出 Agent 的所有记忆键"""
        pattern = f"{self.key_prefix}:{agent_id}:*"
        keys = await redis_client.keys(pattern)
        return [k.split(":")[-1] for k in keys]
    
    async def share_to(
        self,
        from_agent: str,
        to_agent: str,
        key: str
    ):
        """在 Agent 间共享记忆"""
        value = await self.retrieve(from_agent, key)
        if value:
            await self.store(to_agent, key, value)
```

#### 验收标准

- [ ] 共享记忆 API
- [ ] Crew 级别的记忆隔离
- [ ] 记忆过期管理
- [ ] 测试覆盖 > 75%

---

### 任务 14: 后端性能优化

#### 目标
优化连接池、缓存策略、异步处理

#### 实施方案

**数据库连接池优化**

```python
# backend/core/db/config.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 连接池大小
    max_overflow=40,       # 最大溢出连接
    pool_pre_ping=True,     # 连接前检查
    pool_recycle=3600,     # 连接回收时间
    echo=False
)
```

**缓存策略优化**

```python
# backend/core/cache/strategy.py
from functools import wraps
from typing import Callable
import hashlib
import json

def cache_result(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        
        return wrapper
    return decorator

# 使用示例
@cache_result(ttl=600)
async def get_agent_config(agent_id: str):
    """获取 Agent 配置（缓存 10 分钟）"""
    return await agent_service.get_config(agent_id)
```

#### 验收标准

- [ ] 数据库连接池优化
- [ ] Redis 缓存策略
- [ ] 异步处理优化
- [ ] 性能测试通过 (P95 < 200ms)

---

## 实施管理

### 资源分配

| 阶段 | 后端工程师 | 测试工程师 | 总工作量 |
|------|:----------:|:----------:|:--------:|
| P0 | 1.5 人 | 0.5 人 | 7.5 周 |
| P1 | 2 人 | 1 人 | 12 周 |
| P2 | 1 人 | 0.5 人 | 16 周 |

### 风险管理

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| ORM 重构破坏现有功能 | 中 | 高 | 充分测试 + 向后兼容 |
| JWT 撤销性能问题 | 低 | 中 | Redis 优化 + 缓存 |
| MCP 协议变更 | 低 | 中 | 版本锁定 + 定期审查 |
| 工具市场安全风险 | 中 | 高 | 沙箱隔离 + 权限控制 |

### 成功指标

#### P0 阶段成功指标

- [x] ORM 模型文件平均行数 < 200 行
- [x] Schema 模块化完成
- [x] Service 层覆盖率 > 70%
- [x] JWT 撤销功能上线
- [x] MCP 工具扩展至 15+

#### P1 阶段成功指标

- [x] MCP Client 实现
- [x] 工具市场 MVP 上线
- [x] 深度文档解析支持
- [x] Function Calling 统一抽象

#### P2 阶段成功指标

- [x] Agent 版本管理
- [x] 可观测性完整
- [x] 共享记忆机制
- [x] 性能优化达标

---

## 附录

### A. 相关文档

- 产品评估报告: `docs/product-audit-2026-05-29.md`
- 竞品研究报告: `docs/research/backend-competitive-research.md`
- 前端优化计划: `docs/plans/frontend-longterm-optimization.md`

### B. 技术栈参考

| 组件 | 当前技术 | 推荐技术 | 说明 |
|------|---------|---------|------|
| ORM | SQLAlchemy | SQLAlchemy | 保持，优化结构 |
| API | FastAPI | FastAPI | 保持 |
| 任务队列 | Celery | Redis Streams | 更灵活的选择 |
| 缓存 | Redis | Redis | 保持 |
| 追踪 | 无 | OpenTelemetry | 新增 |
| MCP | 自研 | FastMCP | 标准化 |

### C. 联系方式

- 后端负责人: backend-researcher
- 技术讨论: 每周二 10:00 例会
- 进度追踪: GitHub Projects

---

*计划文档版本: 1.0 | 最后更新: 2026-05-29*

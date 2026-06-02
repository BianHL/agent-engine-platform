"""Tenant and Organization models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, generate_uuid


class TenantModel(Base, EnterpriseMixin):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="active")
    parent_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    org_level = Column(String(20), default="company")
    org_path = Column(String(500), default="")
    max_agents = Column(Integer, default=10)
    max_users = Column(Integer, default=100)
    max_storage_gb = Column(Integer, default=10)
    features = Column(JSON, default=dict)
    settings = Column(JSON, nullable=True)
    subscription_plan = Column(String(20), default="free")
    subscription_expires_at = Column(DateTime, nullable=True)
    billing_email = Column(String(200), nullable=True)
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    timezone = Column(String(50), default="Asia/Shanghai")
    locale = Column(String(10), default="zh-CN")
    version = Column(Integer, default=1)

    # relationships
    users = relationship("UserModel", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("AgentModel", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBaseModel", back_populates="tenant", cascade="all, delete-orphan")
    model_providers = relationship("ModelProviderModel", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("ConversationModel", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("RoleModel", back_populates="tenant", cascade="all, delete-orphan")
    departments = relationship("DepartmentModel", back_populates="tenant", cascade="all, delete-orphan")
    tags = relationship("TagModel", back_populates="tenant", cascade="all, delete-orphan")
    marketplace_items = relationship("MarketplaceItem", back_populates="tenant", cascade="all, delete-orphan")
    parent = relationship("TenantModel", remote_side=[id], backref="children")


class DepartmentModel(Base, EnterpriseMixin):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True)
    parent_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    level = Column(Integer, default=1)
    path = Column(String(500), default="")
    leader_id = Column(String(36), nullable=True)
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")
    version = Column(Integer, default=1)

    # relationships
    tenant = relationship("TenantModel", back_populates="departments")
    parent = relationship("DepartmentModel", remote_side=[id], backref="children")


class TagModel(Base):
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7))
    category = Column(String(30), nullable=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uk_tags_tenant_name"),
    )

    # relationships
    tenant = relationship("TenantModel", back_populates="tags")
    bindings = relationship("TagBindingModel", back_populates="tag", cascade="all, delete-orphan")


class TagBindingModel(Base):
    __tablename__ = "tag_bindings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tag_id = Column(String(36), ForeignKey("tags.id"), index=True, nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    __table_args__ = (
        UniqueConstraint("tag_id", "target_type", "target_id", name="uk_tag_target"),
    )

    # relationships
    tag = relationship("TagModel", back_populates="bindings")

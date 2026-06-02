"""Agent related models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, OptimisticLockMixin, generate_uuid


class AgentModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    model_provider = Column(String(50))
    model_name = Column(String(100))
    model_config = Column(JSON, default=dict)
    system_prompt = Column(Text)
    user_prompt_template = Column(Text, nullable=True)
    tools = Column(JSON, default=list)
    knowledge_base_ids = Column(JSON, default=list)
    safety_config = Column(JSON, default=dict)
    status = Column(String(20), default="draft", index=True)
    visibility = Column(String(20), default="private")
    version = Column(Integer, default=1)
    published_at = Column(DateTime)
    marketplace_item_id = Column(String(36), nullable=True, index=True)
    # Statistics (denormalized for performance)
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    last_used_at = Column(DateTime, nullable=True)

    # relationships
    tenant = relationship("TenantModel", back_populates="agents")
    conversations = relationship("ConversationModel", back_populates="agent", cascade="all, delete-orphan")
    versions = relationship("AgentVersionModel", back_populates="agent", cascade="all, delete-orphan")
    ab_tests = relationship("ABTestModel", back_populates="agent", cascade="all, delete-orphan")
    handoffs = relationship("HandoffModel", foreign_keys="HandoffModel.source_agent_id", cascade="all, delete-orphan")


class AgentVersionModel(Base):
    __tablename__ = "agent_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    version = Column(Integer, nullable=False)
    config_snapshot = Column(JSON, default=dict)
    change_log = Column(Text, nullable=True)
    published_at = Column(DateTime)
    published_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    agent = relationship("AgentModel", back_populates="versions")


class AgentTagModel(Base):
    """Deprecated: Use TagModel and TagBindingModel instead."""
    __tablename__ = "agent_tags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id"), index=True, nullable=False)
    tag = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

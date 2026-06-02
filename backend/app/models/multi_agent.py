"""Multi-Agent/Crew related models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, generate_uuid


class CrewModel(Base, EnterpriseMixin):
    __tablename__ = "crews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    process = Column(String(20), default="sequential")
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    total_executions = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)

    # relationships
    executions = relationship("CrewExecutionModel", back_populates="crew", cascade="all, delete-orphan")


class CrewExecutionModel(Base):
    __tablename__ = "crew_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    crew_id = Column(String(36), ForeignKey("crews.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="running", index=True)
    inputs = Column(JSON, default=dict)
    results = Column(JSON, default=list)
    agent_results = Column(JSON, nullable=True)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    crew = relationship("CrewModel", back_populates="executions")


class TaskModel(Base):
    """Generic async task tracking model."""
    __tablename__ = "async_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)
    priority = Column(Integer, default=0)
    progress = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error_message = Column(Text)
    inputs = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))


class HandoffModel(Base, EnterpriseMixin):
    """Agent handoff configuration and tracking."""
    __tablename__ = "agent_handoffs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    source_agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    target_agent_ids = Column(JSON, default=list)
    handoff_config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    total_handoffs = Column(Integer, default=0)
    last_handoff_at = Column(DateTime, nullable=True)

    # relationships
    source_agent = relationship("AgentModel", foreign_keys=[source_agent_id])

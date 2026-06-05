"""Workflow related models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, OptimisticLockMixin, generate_uuid


class WorkflowModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    icon_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    dag_config = Column(JSON, default=dict)
    max_execution_time = Column(Integer)
    max_iterations = Column(Integer, default=100)
    retry_policy = Column(JSON, nullable=True)
    status = Column(String(20), default="draft", index=True)
    visibility = Column(String(20), default="private")
    version = Column(Integer, default=1)
    published_at = Column(DateTime)
    # Statistics (denormalized for performance)
    total_executions = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_duration_ms = Column(Integer, nullable=True)
    last_executed_at = Column(DateTime, nullable=True)

    # relationships
    nodes = relationship("WorkflowNodeModel", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdgeModel", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecutionModel", back_populates="workflow", cascade="all, delete-orphan")
    triggers = relationship("TriggerModel", back_populates="workflow", cascade="all, delete-orphan")
    versions = relationship("WorkflowVersionModel", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNodeModel(Base):
    __tablename__ = "workflow_nodes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), index=True, nullable=False)
    node_id = Column(String(100), nullable=False)
    node_type = Column(String(30), nullable=False)
    label = Column(String(200))
    description = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    workflow = relationship("WorkflowModel", back_populates="nodes")

    __table_args__ = (
        UniqueConstraint("workflow_id", "node_id", name="uk_wn_node"),
    )


class WorkflowEdgeModel(Base):
    __tablename__ = "workflow_edges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), index=True, nullable=False)
    source_node_id = Column(String(100), nullable=False)
    target_node_id = Column(String(100), nullable=False)
    source_handle = Column(String(50), nullable=True)
    target_handle = Column(String(50), nullable=True)
    condition_expression = Column(Text)
    label = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    workflow = relationship("WorkflowModel", back_populates="edges")


class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), index=True, nullable=False)
    workflow_version = Column(Integer, nullable=False, default=1)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    trigger_type = Column(String(20), default="manual")
    trigger_id = Column(String(36), nullable=True)
    status = Column(String(20), default="running", index=True)
    node_states = Column(JSON, default=dict)
    current_node_id = Column(String(100), nullable=True)
    variables = Column(JSON, default=dict)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    execution_log = Column(JSON, default=list)
    node_logs = Column(JSON, default=list)
    trace_tree = Column(JSON, default=dict)
    trace_id = Column(String(36), index=True)
    error_message = Column(Text)
    error_node_id = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    workflow = relationship("WorkflowModel", back_populates="executions")


class WorkflowVersionModel(Base):
    """Stores immutable snapshots of workflow DAG config for version history."""
    __tablename__ = "workflow_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    dag_config = Column(JSON, default=dict)
    change_log = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    workflow = relationship("WorkflowModel", back_populates="versions")

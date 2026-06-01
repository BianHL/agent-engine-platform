"""Extended database models for version management, compliance, and plugins."""
from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class AgentVersionModel(Base):
    """Agent version model for version management."""

    __tablename__ = "agent_versions"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    system_prompt = Column(Text, nullable=False)
    model_provider = Column(String(50))
    model_name = Column(String(100))
    config = Column(JSON, default={})
    description = Column(Text)
    is_active = Column(Boolean, default=False)
    created_by = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    agent = relationship("AgentModel", back_populates="versions")


class ABTestModel(Base):
    """A/B test model for agent version testing."""

    __tablename__ = "ab_tests"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    version_a_id = Column(String(36), ForeignKey("agent_versions.id"), nullable=False)
    version_b_id = Column(String(36), ForeignKey("agent_versions.id"), nullable=False)
    traffic_split = Column(Float, default=0.5)
    metric = Column(String(50), default="satisfaction")
    duration_hours = Column(Integer, default=24)
    min_samples = Column(Integer, default=100)
    status = Column(String(20), default="created")  # created, running, completed, stopped
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    results = Column(JSON)
    tenant_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    agent = relationship("AgentModel", back_populates="ab_tests")
    version_a = relationship("AgentVersionModel", foreign_keys=[version_a_id])
    version_b = relationship("AgentVersionModel", foreign_keys=[version_b_id])


class PluginModel(Base):
    """Plugin model for marketplace."""

    __tablename__ = "plugins"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    version = Column(String(20), nullable=False)
    author = Column(String(100), default="")
    category = Column(String(50), default="general", index=True)
    tags = Column(JSON, default=[])
    icon = Column(String(500))
    homepage = Column(String(500))
    repository = Column(String(500))
    config_schema = Column(JSON)
    entry_point = Column(String(200), nullable=False)
    dependencies = Column(JSON, default=[])
    permissions = Column(JSON, default=[])
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft, published, archived
    tenant_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    installs = relationship("PluginInstallModel", back_populates="plugin")
    ratings = relationship("PluginRatingModel", back_populates="plugin")


class PluginInstallModel(Base):
    """Plugin installation model."""

    __tablename__ = "plugin_installs"

    id = Column(String(36), primary_key=True)
    plugin_id = Column(String(36), ForeignKey("plugins.id"), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default="active")  # active, inactive, error
    config = Column(JSON)
    installed_by = Column(String(36), nullable=False)
    installed_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    plugin = relationship("PluginModel", back_populates="installs")


class PluginRatingModel(Base):
    """Plugin rating model."""

    __tablename__ = "plugin_ratings"

    id = Column(String(36), primary_key=True)
    plugin_id = Column(String(36), ForeignKey("plugins.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    plugin = relationship("PluginModel", back_populates="ratings")


class ComplianceReportModel(Base):
    """Compliance report model."""

    __tablename__ = "compliance_reports"

    id = Column(String(36), primary_key=True)
    report_type = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    summary = Column(JSON, nullable=False)
    details = Column(JSON)
    format = Column(String(20), default="json")
    tenant_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

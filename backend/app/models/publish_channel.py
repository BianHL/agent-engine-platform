"""Publish channel models."""
from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, generate_uuid


class PublishChannelModel(Base, EnterpriseMixin):
    __tablename__ = "publish_channels"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), index=True, nullable=False)
    type = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default="active")
    config = Column(JSON, default=dict)
    api_key_prefix = Column(String(10), nullable=True)
    total_calls = Column(Integer, default=0)
    calls_today = Column(Integer, default=0)

    agent = relationship("AgentModel", backref="publish_channels")

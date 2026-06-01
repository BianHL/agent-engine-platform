"""Audit and Operation Log models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class OperationLogModel(Base):
    __tablename__ = "operation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    username = Column(String(50), nullable=True)
    action = Column(String(20), nullable=False, index=True)
    resource_type = Column(String(50), index=True)
    resource_id = Column(String(36))
    resource_name = Column(String(200), nullable=True)
    details = Column(JSON, default=dict)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_body = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    risk_level = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    # relationships
    actor = relationship("UserModel", back_populates="operation_logs", foreign_keys=[user_id])

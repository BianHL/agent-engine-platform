"""User and Authentication models."""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, generate_uuid


class UserModel(Base, EnterpriseMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(200))
    phone = Column(String(30), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    salt = Column(String(64), nullable=True)
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(20), default="user")
    department_id = Column(String(36), index=True)
    position = Column(String(100), nullable=True)
    status = Column(String(20), default="active")
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    login_count = Column(Integer, default=0)
    password_changed_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    phone_verified_at = Column(DateTime, nullable=True)
    settings = Column(JSON, nullable=True)
    version = Column(Integer, default=1)

    # relationships
    tenant = relationship("TenantModel", back_populates="users")
    conversations = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")
    api_tokens = relationship("ApiTokenModel", back_populates="user", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLogModel", back_populates="actor", foreign_keys="OperationLogModel.user_id")
    marketplace_items = relationship("MarketplaceItem", back_populates="creator", foreign_keys="MarketplaceItem.creator_id")


class ApiTokenModel(Base):
    __tablename__ = "api_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    token_prefix = Column(String(10), nullable=False)
    token_hash = Column(String(200), nullable=False)
    permissions = Column(JSON, default=list)
    rate_limit = Column(Integer, nullable=True)
    allowed_ips = Column(JSON, nullable=True)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    last_used_ip = Column(String(45), nullable=True)
    usage_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    revoked_at = Column(DateTime, nullable=True)

    # relationships
    user = relationship("UserModel", back_populates="api_tokens")


class UserRoleModel(Base):
    """User-Role many-to-many association."""
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), index=True, nullable=False)
    tenant_id = Column(String(36), index=True, nullable=False)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class UserSessionModel(Base):
    """User session tracking for JWT management."""
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), index=True, nullable=False)
    tenant_id = Column(String(36), nullable=False)
    session_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=True)
    device_type = Column(String(30), nullable=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    last_active_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

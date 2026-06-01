"""SQLAlchemy Base class and common utilities."""
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class SoftDeleteMixin:
    """Mixin that adds soft delete support."""
    deleted_at = Column(DateTime, nullable=True, index=True)


class AuditMixin:
    """Mixin that adds audit fields."""
    created_by = Column(String(36), nullable=True)


class OptimisticLockMixin:
    """Mixin that adds optimistic locking support."""
    version_lock = Column(Integer, default=1, nullable=False)


class EnterpriseMixin(TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Combined mixin for enterprise-grade models."""
    pass

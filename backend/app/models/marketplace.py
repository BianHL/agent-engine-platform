"""Marketplace related models."""
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class MarketplaceItem(Base):
    __tablename__ = "marketplace_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    creator_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    asset_type = Column(String(20), nullable=False, index=True)
    asset_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(String(500), default="")
    description = Column(Text, default="")
    cover_image = Column(String(500), nullable=True)
    category = Column(String(50), default="", index=True)
    tags = Column(JSON, default=list)
    visibility = Column(String(20), default="tenant")
    status = Column(String(20), default="draft", index=True)
    reject_reason = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    config_snapshot = Column(JSON, default=dict)
    avg_rating = Column(Numeric(3, 2), default=0.0)
    rating_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    clone_count = Column(Integer, default=0)
    featured = Column(Boolean, default=False, index=True)
    promoted_level = Column(String(20), nullable=True)
    frozen_at = Column(DateTime, nullable=True)
    frozen_reason = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    tenant = relationship("TenantModel", back_populates="marketplace_items")
    creator = relationship("UserModel", back_populates="marketplace_items")
    reviews = relationship("MarketplaceReviewModel", back_populates="item", cascade="all, delete-orphan")
    ratings = relationship("MarketplaceRatingModel", back_populates="item", cascade="all, delete-orphan")


class MarketplaceReviewModel(Base):
    __tablename__ = "marketplace_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(36), ForeignKey("marketplace_items.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    submitter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    review_type = Column(String(20), default="publish")
    status = Column(String(20), default="pending", index=True)
    comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    item = relationship("MarketplaceItem", back_populates="reviews")


class MarketplaceRatingModel(Base):
    __tablename__ = "marketplace_ratings"
    __table_args__ = (
        UniqueConstraint("item_id", "user_id", name="uq_marketplace_rating_item_user"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(36), ForeignKey("marketplace_items.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    item = relationship("MarketplaceItem", back_populates="ratings")


class MarketplaceCloneModel(Base):
    __tablename__ = "marketplace_clones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_item_id = Column(String(36), ForeignKey("marketplace_items.id"), index=True, nullable=False)
    target_tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    target_asset_id = Column(String(36), nullable=False)
    cloner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class MarketplaceChangeLogModel(Base):
    """市集资产变更日志."""
    __tablename__ = "marketplace_change_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(36), ForeignKey("marketplace_items.id"), index=True, nullable=False)
    operator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    change_type = Column(String(20), nullable=False, index=True)
    before_snapshot = Column(JSON, nullable=True)
    after_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    item = relationship("MarketplaceItem")

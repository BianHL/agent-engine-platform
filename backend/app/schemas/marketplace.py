"""Marketplace related schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Marketplace Item ---

class CreateMarketplaceItemRequest(BaseModel):
    asset_type: str = Field(..., description="Asset type: agent/knowledge_base/workflow")
    asset_id: str = Field(..., description="ID of the source asset")
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field("", max_length=500)
    description: str = ""
    cover_image: Optional[str] = None
    category: str = ""
    tags: List[str] = []
    visibility: str = Field("tenant", description="private/department/tenant/public")


class UpdateMarketplaceItemRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None


class MarketplaceItemResponse(BaseModel):
    id: str
    tenant_id: str
    creator_id: str
    asset_type: str
    asset_id: str
    title: str
    summary: str
    description: str
    cover_image: Optional[str] = None
    category: str
    tags: List[str] = []
    visibility: str
    status: str
    version: int
    avg_rating: float
    rating_count: int
    usage_count: int
    clone_count: int
    featured: bool
    promoted_level: Optional[str] = None
    creator_name: Optional[str] = None
    creator_tenant_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MarketplaceListItemResponse(BaseModel):
    id: str
    asset_type: str
    title: str
    summary: str
    cover_image: Optional[str] = None
    category: str
    tags: List[str] = []
    avg_rating: float
    rating_count: int
    usage_count: int
    clone_count: int
    featured: bool
    promoted_level: Optional[str] = None
    creator_tenant_name: Optional[str] = None
    published_at: Optional[datetime] = None


# --- Review ---

class SubmitForReviewRequest(BaseModel):
    asset_type: str
    asset_id: str
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field("", max_length=500)
    description: str = ""
    cover_image: Optional[str] = None
    category: str = ""
    tags: List[str] = []
    visibility: str = "tenant"


class ReviewActionRequest(BaseModel):
    comment: str = ""


class MarketplaceReviewResponse(BaseModel):
    id: str
    item_id: str
    tenant_id: str
    submitter_id: str
    reviewer_id: Optional[str] = None
    review_type: str
    status: str
    comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    # Enriched fields
    item_title: Optional[str] = None
    submitter_name: Optional[str] = None


# --- Rating ---

class CreateRatingRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class MarketplaceRatingResponse(BaseModel):
    id: str
    item_id: str
    user_id: str
    score: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None


# --- Clone ---

class CloneResponse(BaseModel):
    id: str
    source_item_id: str
    target_tenant_id: str
    target_asset_id: str
    cloner_id: str
    created_at: datetime


# --- Admin ---

class FreezeRequest(BaseModel):
    reason: str = ""


class TakedownRequest(BaseModel):
    reason: str = ""


class PromoteRequest(BaseModel):
    target_level: str = Field(..., description="Target visibility: department/tenant/group")


class MarketplaceStatsResponse(BaseModel):
    total_items: int
    published_items: int
    pending_review_items: int
    total_ratings: int
    total_clones: int
    total_usage: int
    avg_rating: float
    items_by_category: Dict[str, int]
    items_by_status: Dict[str, int]
    items_by_tenant: Dict[str, int]

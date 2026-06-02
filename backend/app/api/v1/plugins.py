"""Plugin marketplace API endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db
from app.models.extended import PluginModel, PluginInstallModel, PluginRatingModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PluginCreate(BaseModel):
    name: str = Field(..., description="Plugin name", max_length=100)
    description: str = Field(default="", description="Plugin description", max_length=1000)
    version: str = Field(..., description="Plugin version (semver)")
    author: str = Field(default="", description="Plugin author", max_length=100)
    category: str = Field(default="general", description="Plugin category")
    tags: list[str] = Field(default_factory=list, description="Plugin tags")
    icon: Optional[str] = Field(default=None, description="Plugin icon URL")
    homepage: Optional[str] = Field(default=None, description="Plugin homepage URL")
    repository: Optional[str] = Field(default=None, description="Source code repository URL")
    config_schema: Optional[dict] = Field(default=None, description="Configuration schema")
    entry_point: str = Field(..., description="Plugin entry point")
    dependencies: list[str] = Field(default_factory=list, description="Plugin dependencies")
    permissions: list[str] = Field(default_factory=list, description="Required permissions")


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    icon: Optional[str] = None
    homepage: Optional[str] = None
    config_schema: Optional[dict] = None
    entry_point: Optional[str] = None
    dependencies: Optional[list[str]] = None
    permissions: Optional[list[str]] = None


class PluginResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: list[str]
    icon: Optional[str]
    homepage: Optional[str]
    repository: Optional[str]
    config_schema: Optional[dict]
    entry_point: str
    dependencies: list[str]
    permissions: list[str]
    downloads: int
    rating: float
    rating_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class PluginInstallResponse(BaseModel):
    id: str
    plugin_id: str
    tenant_id: str
    status: str
    config: Optional[dict]
    installed_at: datetime
    updated_at: datetime


class PluginRatingCreate(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Rating score (1-5)")
    comment: Optional[str] = Field(default=None, max_length=1000)


class PluginRatingResponse(BaseModel):
    id: str
    plugin_id: str
    user_id: str
    score: int
    comment: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Plugin CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[PluginResponse])
async def list_plugins(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="popular", regex="^(popular|rating|newest|name)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List plugins in the marketplace."""
    filters = [PluginModel.status == "published"]

    if category:
        filters.append(PluginModel.category == category)

    if search:
        search_filter = or_(
            PluginModel.name.ilike(f"%{search}%"),
            PluginModel.description.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    # Sorting
    if sort_by == "popular":
        order_by = desc(PluginModel.downloads)
    elif sort_by == "rating":
        order_by = desc(PluginModel.rating)
    elif sort_by == "newest":
        order_by = desc(PluginModel.created_at)
    else:
        order_by = PluginModel.name

    stmt = (
        select(PluginModel)
        .where(and_(*filters))
        .order_by(order_by)
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    plugins = result.scalars().all()

    return [
        PluginResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            author=p.author,
            category=p.category,
            tags=p.tags or [],
            icon=p.icon,
            homepage=p.homepage,
            repository=p.repository,
            config_schema=p.config_schema,
            entry_point=p.entry_point,
            dependencies=p.dependencies or [],
            permissions=p.permissions or [],
            downloads=p.downloads,
            rating=p.rating,
            rating_count=p.rating_count,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in plugins
    ]


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get plugin details."""
    stmt = select(PluginModel).where(PluginModel.id == plugin_id)
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return PluginResponse(
        id=plugin.id,
        name=plugin.name,
        description=plugin.description,
        version=plugin.version,
        author=plugin.author,
        category=plugin.category,
        tags=plugin.tags or [],
        icon=plugin.icon,
        homepage=plugin.homepage,
        repository=plugin.repository,
        config_schema=plugin.config_schema,
        entry_point=plugin.entry_point,
        dependencies=plugin.dependencies or [],
        permissions=plugin.permissions or [],
        downloads=plugin.downloads,
        rating=plugin.rating,
        rating_count=plugin.rating_count,
        status=plugin.status,
        created_at=plugin.created_at,
        updated_at=plugin.updated_at,
    )


@router.post("", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    data: PluginCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new plugin (for plugin developers)."""
    # Check name uniqueness
    stmt = select(PluginModel).where(PluginModel.name == data.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Plugin name already exists")

    plugin = PluginModel(
        name=data.name,
        description=data.description,
        version=data.version,
        author=data.author or user.get("username", ""),
        category=data.category,
        tags=data.tags,
        icon=data.icon,
        homepage=data.homepage,
        repository=data.repository,
        config_schema=data.config_schema,
        entry_point=data.entry_point,
        dependencies=data.dependencies,
        permissions=data.permissions,
        downloads=0,
        rating=0.0,
        rating_count=0,
        status="draft",
        tenant_id=tenant_id,
        created_by=user["id"],
    )
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)

    return PluginResponse(
        id=plugin.id,
        name=plugin.name,
        description=plugin.description,
        version=plugin.version,
        author=plugin.author,
        category=plugin.category,
        tags=plugin.tags or [],
        icon=plugin.icon,
        homepage=plugin.homepage,
        repository=plugin.repository,
        config_schema=plugin.config_schema,
        entry_point=plugin.entry_point,
        dependencies=plugin.dependencies or [],
        permissions=plugin.permissions or [],
        downloads=plugin.downloads,
        rating=plugin.rating,
        rating_count=plugin.rating_count,
        status=plugin.status,
        created_at=plugin.created_at,
        updated_at=plugin.updated_at,
    )


@router.put("/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: str,
    data: PluginUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update a plugin."""
    stmt = select(PluginModel).where(
        and_(PluginModel.id == plugin_id, PluginModel.created_by == user["id"])
    )
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found or not owned by you")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plugin, key, value)

    plugin.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(plugin)

    return PluginResponse(
        id=plugin.id,
        name=plugin.name,
        description=plugin.description,
        version=plugin.version,
        author=plugin.author,
        category=plugin.category,
        tags=plugin.tags or [],
        icon=plugin.icon,
        homepage=plugin.homepage,
        repository=plugin.repository,
        config_schema=plugin.config_schema,
        entry_point=plugin.entry_point,
        dependencies=plugin.dependencies or [],
        permissions=plugin.permissions or [],
        downloads=plugin.downloads,
        rating=plugin.rating,
        rating_count=plugin.rating_count,
        status=plugin.status,
        created_at=plugin.created_at,
        updated_at=plugin.updated_at,
    )


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a plugin."""
    stmt = select(PluginModel).where(
        and_(PluginModel.id == plugin_id, PluginModel.created_by == user["id"])
    )
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found or not owned by you")

    await db.delete(plugin)
    await db.commit()


# ---------------------------------------------------------------------------
# Plugin installation endpoints
# ---------------------------------------------------------------------------

@router.post("/{plugin_id}/install", response_model=PluginInstallResponse)
async def install_plugin(
    plugin_id: str,
    config: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Install a plugin for the current tenant."""
    # Check if plugin exists
    stmt = select(PluginModel).where(PluginModel.id == plugin_id)
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Check if already installed
    stmt = select(PluginInstallModel).where(
        and_(
            PluginInstallModel.plugin_id == plugin_id,
            PluginInstallModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Plugin already installed")

    install = PluginInstallModel(
        plugin_id=plugin_id,
        tenant_id=tenant_id,
        status="active",
        config=config,
        installed_by=user["id"],
    )
    db.add(install)

    # Increment download count
    plugin.downloads += 1

    await db.commit()
    await db.refresh(install)

    return PluginInstallResponse(
        id=install.id,
        plugin_id=install.plugin_id,
        tenant_id=install.tenant_id,
        status=install.status,
        config=install.config,
        installed_at=install.installed_at,
        updated_at=install.updated_at,
    )


@router.delete("/{plugin_id}/uninstall", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Uninstall a plugin."""
    stmt = select(PluginInstallModel).where(
        and_(
            PluginInstallModel.plugin_id == plugin_id,
            PluginInstallModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    install = result.scalar_one_or_none()
    if not install:
        raise HTTPException(status_code=404, detail="Plugin not installed")

    await db.delete(install)
    await db.commit()


@router.get("/installed", response_model=list[PluginInstallResponse])
async def list_installed_plugins(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """List installed plugins for the current tenant."""
    stmt = select(PluginInstallModel).where(PluginInstallModel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    installs = result.scalars().all()

    return [
        PluginInstallResponse(
            id=i.id,
            plugin_id=i.plugin_id,
            tenant_id=i.tenant_id,
            status=i.status,
            config=i.config,
            installed_at=i.installed_at,
            updated_at=i.updated_at,
        )
        for i in installs
    ]


# ---------------------------------------------------------------------------
# Plugin rating endpoints
# ---------------------------------------------------------------------------

@router.post("/{plugin_id}/ratings", response_model=PluginRatingResponse)
async def rate_plugin(
    plugin_id: str,
    data: PluginRatingCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Rate a plugin."""
    # Check if plugin exists
    stmt = select(PluginModel).where(PluginModel.id == plugin_id)
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Check if already rated
    stmt = select(PluginRatingModel).where(
        and_(
            PluginRatingModel.plugin_id == plugin_id,
            PluginRatingModel.user_id == user["id"],
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already rated this plugin")

    rating = PluginRatingModel(
        plugin_id=plugin_id,
        user_id=user["id"],
        score=data.score,
        comment=data.comment,
    )
    db.add(rating)

    # Update plugin rating
    stmt = select(func.avg(PluginRatingModel.score)).where(PluginRatingModel.plugin_id == plugin_id)
    result = await db.execute(stmt)
    avg_rating = result.scalar() or 0

    stmt = select(func.count(PluginRatingModel.id)).where(PluginRatingModel.plugin_id == plugin_id)
    result = await db.execute(stmt)
    rating_count = result.scalar() or 0

    plugin.rating = round(avg_rating, 2)
    plugin.rating_count = rating_count

    await db.commit()
    await db.refresh(rating)

    return PluginRatingResponse(
        id=rating.id,
        plugin_id=rating.plugin_id,
        user_id=rating.user_id,
        score=rating.score,
        comment=rating.comment,
        created_at=rating.created_at,
    )


@router.get("/{plugin_id}/ratings", response_model=list[PluginRatingResponse])
async def get_plugin_ratings(
    plugin_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get ratings for a plugin."""
    stmt = (
        select(PluginRatingModel)
        .where(PluginRatingModel.plugin_id == plugin_id)
        .order_by(desc(PluginRatingModel.created_at))
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    return [
        PluginRatingResponse(
            id=r.id,
            plugin_id=r.plugin_id,
            user_id=r.user_id,
            score=r.score,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in ratings
    ]


# ---------------------------------------------------------------------------
# Plugin categories
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=list[dict])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List plugin categories."""
    stmt = (
        select(PluginModel.category, func.count(PluginModel.id))
        .where(PluginModel.status == "published")
        .group_by(PluginModel.category)
        .order_by(desc(func.count(PluginModel.id)))
    )
    result = await db.execute(stmt)
    categories = result.all()

    return [{"name": cat, "count": count} for cat, count in categories]

"""Marketplace API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.platform.marketplace_service.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ========== Browse (public, login required) ==========

@router.get("/items")
async def list_items(
    keyword: str = Query("", description="Search keyword"),
    category: str = Query("", description="Category filter"),
    tags: str = Query("", description="Tags filter (comma-separated)"),
    asset_type: str = Query("", description="Asset type filter"),
    sort_by: str = Query("latest", description="Sort: latest/hottest/rating/clones"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List marketplace items with search, filter, and sort."""
    svc = MarketplaceService(db)
    return await svc.list_items(
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        keyword=keyword,
        category=category,
        tags=tags,
        asset_type=asset_type,
        sort_by=sort_by,
        page=page,
        size=size)


@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get marketplace item detail."""
    svc = MarketplaceService(db)
    item = await svc.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/featured")
async def get_featured(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get featured items."""
    svc = MarketplaceService(db)
    return await svc.get_featured(limit=limit)


@router.get("/hot")
async def get_hot(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get hot/trending items."""
    svc = MarketplaceService(db)
    return await svc.get_hot(limit=limit)


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get all categories."""
    svc = MarketplaceService(db)
    return await svc.get_categories()


# ========== Whitebox ==========

@router.get("/items/{item_id}/whitebox")
async def get_whitebox_view(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get white-box visualization data for an item."""
    from sqlalchemy import select
    from app.models.marketplace import MarketplaceItem as MarketplaceItemModel

    q = select(MarketplaceItemModel).where(MarketplaceItemModel.id == item_id)
    result = await db.execute(q)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    config = item.config_snapshot or {}
    svc = MarketplaceService(db)
    nodes, edges = svc.generate_whitebox_flow(config)
    return {"nodes": nodes, "edges": edges}


# ========== Trial ==========

@router.post("/items/{item_id}/trial")
async def create_trial(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "create"))):
    """Record a trial use of an item (increments usage_count)."""
    svc = MarketplaceService(db)
    item = await svc.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item["status"] not in ("published", "approved"):
        raise HTTPException(status_code=400, detail="Item not available for trial")
    await svc.record_trial(item_id)
    return {"status": "ok", "asset_type": item["asset_type"], "asset_id": item["asset_id"]}


# ========== Rating ==========

@router.post("/items/{item_id}/rating")
async def create_rating(
    item_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "create"))):
    """Create or update rating for an item."""
    svc = MarketplaceService(db)
    try:
        return await svc.create_rating(
            item_id=item_id,
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            score=body.get("score", 5),
            comment=body.get("comment"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/items/{item_id}/ratings")
async def get_ratings(
    item_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get ratings for an item."""
    svc = MarketplaceService(db)
    return await svc.get_item_ratings(item_id, page=page, size=size)


@router.get("/items/{item_id}/rating/me")
async def get_my_rating(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get current user's rating for an item."""
    svc = MarketplaceService(db)
    rating = await svc.get_my_rating(item_id, user["id"])
    if not rating:
        raise HTTPException(status_code=404, detail="No rating found")
    return rating


# ========== Clone ==========

@router.post("/items/{item_id}/clone")
async def clone_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "submit"))):
    """Clone an item to current user's tenant."""
    svc = MarketplaceService(db)
    try:
        return await svc.clone_item(
            item_id=item_id,
            cloner_id=user["id"],
            target_tenant_id=user["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== Submission (Contributor permission required) ==========

@router.post("/submissions", status_code=status.HTTP_201_CREATED)
async def submit_for_review(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "submit"))):
    """Submit an asset for marketplace review."""
    svc = MarketplaceService(db)
    try:
        return await svc.submit_for_review(
            tenant_id=user["tenant_id"],
            user_id=user["id"],
            data=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/submissions")
async def get_my_submissions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get my submission history."""
    svc = MarketplaceService(db)
    return await svc.get_my_submissions(
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        page=page,
        size=size)


@router.post("/submissions/{item_id}/cancel")
async def cancel_submission(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "submit"))):
    """Cancel a pending submission."""
    svc = MarketplaceService(db)
    try:
        return await svc.cancel_submission(item_id, user["tenant_id"], user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Review management (Admin permission required) ==========

@router.get("/admin/reviews")
async def list_pending_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "review"))):
    """List items pending review."""
    svc = MarketplaceService(db)
    return await svc.list_pending_reviews(
        tenant_id=user["tenant_id"], page=page, size=size)


@router.get("/admin/reviews/pending-promotion")
async def list_pending_promotion_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "review"))):
    """List items pending cross-level promotion review."""
    svc = MarketplaceService(db)
    return await svc.list_pending_promotion_reviews(
        tenant_id=user["tenant_id"], page=page, size=size)


@router.post("/admin/reviews/{item_id}/approve")
async def approve_review(
    item_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "review"))):
    """Approve a marketplace item."""
    svc = MarketplaceService(db)
    try:
        return await svc.approve_review(
            item_id=item_id,
            tenant_id=user["tenant_id"],
            reviewer_id=user["id"],
            comment=body.get("comment", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/reviews/{item_id}/reject")
async def reject_review(
    item_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "review"))):
    """Reject a marketplace item."""
    svc = MarketplaceService(db)
    try:
        return await svc.reject_review(
            item_id=item_id,
            tenant_id=user["tenant_id"],
            reviewer_id=user["id"],
            comment=body.get("comment", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Asset management (Admin permission required) ==========

@router.post("/admin/items/{item_id}/freeze")
async def freeze_item(
    item_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Freeze an item."""
    svc = MarketplaceService(db)
    try:
        return await svc.freeze_item(item_id, user["tenant_id"], body.get("reason", ""))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/items/{item_id}/unfreeze")
async def unfreeze_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Unfreeze an item."""
    svc = MarketplaceService(db)
    try:
        return await svc.unfreeze_item(item_id, user["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/items/{item_id}/takedown")
async def takedown_item(
    item_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Force takedown an item."""
    svc = MarketplaceService(db)
    try:
        return await svc.takedown_item(item_id, user["tenant_id"], body.get("reason", ""))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/items/{item_id}/promote")
async def promote_item(
    item_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "promote"))):
    """Promote an item to higher visibility level."""
    svc = MarketplaceService(db)
    try:
        return await svc.promote_item(
            item_id, user["tenant_id"], body.get("target_level", "tenant"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/items/{item_id}/feature")
async def set_featured(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Set item as featured."""
    svc = MarketplaceService(db)
    try:
        return await svc.toggle_featured(item_id, user["tenant_id"], True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/admin/items/{item_id}/feature")
async def unset_featured(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Remove item from featured."""
    svc = MarketplaceService(db)
    try:
        return await svc.toggle_featured(item_id, user["tenant_id"], False)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/admin/items")
async def list_admin_items(
    status_filter: str = Query("", alias="status"),
    keyword: str = Query(""),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """List all items for admin (all statuses)."""
    svc = MarketplaceService(db)
    return await svc.list_admin_items(
        tenant_id=user["tenant_id"],
        status=status_filter,
        keyword=keyword,
        page=page,
        size=size)


# ========== Changelog ==========

@router.get("/items/{item_id}/changelog")
async def get_changelog(
    item_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get changelog for a marketplace item."""
    svc = MarketplaceService(db)
    return await svc.get_changelog(item_id, page=page, size=size)


# ========== Stats dashboard (Admin permission required) ==========

@router.get("/admin/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Get marketplace statistics."""
    svc = MarketplaceService(db)
    return await svc.get_stats(user["tenant_id"])


@router.get("/admin/stats/trends")
async def get_stats_trends(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("marketplace", "manage"))):
    """Get marketplace trend data."""
    svc = MarketplaceService(db)
    return await svc.get_stats_trends(user["tenant_id"], days=days)

"""Trigger API endpoints for workflow scheduling."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.rbac import require_permission
from app.core.database import get_db
from app.core.scheduler import get_scheduler
from app.models.base import TriggerModel
from app.schemas.api import (
    CreateTriggerRequest,
    PaginatedResponse,
    StatusResponse,
    TriggerResponse,
)

router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_trigger(
    body: CreateTriggerRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Create a new trigger."""
    try:
        trigger = TriggerModel(
            tenant_id=user["tenant_id"],
            workflow_id=body.workflow_id,
            name=body.name,
            trigger_type=body.trigger_type,
            config=body.config,
            enabled=True,
        )
        db.add(trigger)
        await db.flush()

        # Register with scheduler if enabled
        scheduler = get_scheduler()
        scheduler.add_cron_trigger(trigger)

        return _trigger_to_dict(trigger)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trigger: {str(e)}")


@router.get("/")
async def list_triggers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List triggers for the current tenant."""
    try:
        offset = (page - 1) * size
        stmt = (
            select(TriggerModel)
            .where(TriggerModel.tenant_id == user["tenant_id"])
            .order_by(TriggerModel.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()

        count_stmt = (
            select(func.count())
            .select_from(TriggerModel)
            .where(TriggerModel.tenant_id == user["tenant_id"])
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        return PaginatedResponse(
            items=[_trigger_to_dict(t) for t in items],
            total=total,
            page=page,
            size=size,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list triggers: {str(e)}")


@router.put("/{trigger_id}")
async def update_trigger(
    trigger_id: str,
    body: CreateTriggerRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Update a trigger."""
    try:
        trigger = await _get_trigger(db, trigger_id, user["tenant_id"])
        trigger.name = body.name
        trigger.workflow_id = body.workflow_id
        trigger.trigger_type = body.trigger_type
        trigger.config = body.config
        trigger.updated_at = datetime.now(timezone.utc)
        await db.flush()

        # Re-register with scheduler
        scheduler = get_scheduler()
        if trigger.enabled:
            scheduler.remove_cron_trigger(trigger_id)
            scheduler.add_cron_trigger(trigger)

        return _trigger_to_dict(trigger)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update trigger: {str(e)}")


@router.delete("/{trigger_id}")
async def delete_trigger(
    trigger_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Delete a trigger."""
    try:
        trigger = await _get_trigger(db, trigger_id, user["tenant_id"])

        # Remove from scheduler
        scheduler = get_scheduler()
        scheduler.remove_cron_trigger(trigger_id)

        await db.delete(trigger)
        return StatusResponse(status="deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete trigger: {str(e)}")


@router.post("/{trigger_id}/enable")
async def enable_trigger(
    trigger_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Enable a trigger."""
    try:
        trigger = await _get_trigger(db, trigger_id, user["tenant_id"])
        trigger.enabled = True
        trigger.updated_at = datetime.now(timezone.utc)
        await db.flush()

        scheduler = get_scheduler()
        scheduler.add_cron_trigger(trigger)

        return _trigger_to_dict(trigger)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable trigger: {str(e)}")


@router.post("/{trigger_id}/disable")
async def disable_trigger(
    trigger_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Disable a trigger."""
    try:
        trigger = await _get_trigger(db, trigger_id, user["tenant_id"])
        trigger.enabled = False
        trigger.updated_at = datetime.now(timezone.utc)
        await db.flush()

        scheduler = get_scheduler()
        scheduler.remove_cron_trigger(trigger_id)

        return _trigger_to_dict(trigger)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable trigger: {str(e)}")


@router.post("/{trigger_id}/test")
async def test_trigger(
    trigger_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """Manually fire a trigger for testing."""
    try:
        trigger = await _get_trigger(db, trigger_id, user["tenant_id"])

        scheduler = get_scheduler()
        result = await scheduler.fire_trigger(trigger_id)

        return {"trigger": _trigger_to_dict(trigger), "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test trigger: {str(e)}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_trigger(db: AsyncSession, trigger_id: str, tenant_id: str) -> TriggerModel:
    stmt = select(TriggerModel).where(
        TriggerModel.id == trigger_id,
        TriggerModel.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    trigger = result.scalar_one_or_none()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return trigger


def _trigger_to_dict(t: TriggerModel) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "workflow_id": t.workflow_id,
        "trigger_type": t.trigger_type,
        "config": t.config,
        "enabled": t.enabled,
        "last_triggered_at": t.last_triggered_at.isoformat() if t.last_triggered_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }

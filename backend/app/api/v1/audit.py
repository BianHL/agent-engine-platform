"""Audit log API endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.base import OperationLogModel

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_operation_logs(
    action: Optional[str] = Query(None, description="Filter by action type (create/update/delete)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (agent/knowledge/workflow/etc)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List audit logs with filters."""
    stmt = (
        select(OperationLogModel)
        .where(OperationLogModel.tenant_id == user["tenant_id"])
        .order_by(OperationLogModel.created_at.desc())
    )

    if action:
        stmt = stmt.where(OperationLogModel.action == action)
    if resource_type:
        stmt = stmt.where(OperationLogModel.resource_type == resource_type)
    if user_id:
        stmt = stmt.where(OperationLogModel.user_id == user_id)
    if start_date:
        stmt = stmt.where(OperationLogModel.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(OperationLogModel.created_at <= datetime.fromisoformat(end_date))

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)

    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "user_id": log.user_id,
            "ip_address": log.ip_address,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in result.scalars().all()
    ]

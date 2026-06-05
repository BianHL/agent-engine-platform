"""Usage and cost tracking API endpoints."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.engines.model_engine.cost_tracker import CostTracker
from app.models.base import UsageLogModel
from app.schemas.api import DailyUsageResponse, ModelUsageResponse

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary")
async def get_usage_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get usage summary for the current tenant."""
    try:
        tracker = CostTracker(db)
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        return await tracker.get_usage(user["tenant_id"], start, end)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage summary: {str(e)}")


@router.get("/daily")
async def get_daily_usage(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get daily usage breakdown."""
    try:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        stmt = select(
            func.date(UsageLogModel.created_at).label("date"),
            func.sum(UsageLogModel.input_tokens).label("input_tokens"),
            func.sum(UsageLogModel.output_tokens).label("output_tokens"),
            func.sum(UsageLogModel.cost).label("cost"),
            func.count(UsageLogModel.id).label("requests")).where(
            UsageLogModel.tenant_id == user["tenant_id"],
            UsageLogModel.created_at >= start).group_by(
            func.date(UsageLogModel.created_at)
        ).order_by(
            func.date(UsageLogModel.created_at)
        )

        result = await db.execute(stmt)
        return [
            {
                "date": str(row.date),
                "input_tokens": row.input_tokens or 0,
                "output_tokens": row.output_tokens or 0,
                "cost": round(row.cost or 0.0, 6),
                "requests": row.requests or 0,
            }
            for row in result.all()
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily usage: {str(e)}")


@router.get("/models")
async def get_model_usage(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get usage breakdown by model."""
    try:
        stmt = select(
            UsageLogModel.model_name,
            UsageLogModel.model_provider,
            func.sum(UsageLogModel.input_tokens).label("input_tokens"),
            func.sum(UsageLogModel.output_tokens).label("output_tokens"),
            func.sum(UsageLogModel.cost).label("cost"),
            func.count(UsageLogModel.id).label("requests")).where(
            UsageLogModel.tenant_id == user["tenant_id"]).group_by(
            UsageLogModel.model_name,
            UsageLogModel.model_provider)

        result = await db.execute(stmt)
        return [
            {
                "model_name": row.model_name,
                "provider": row.model_provider,
                "input_tokens": row.input_tokens or 0,
                "output_tokens": row.output_tokens or 0,
                "cost": round(row.cost or 0.0, 6),
                "requests": row.requests or 0,
            }
            for row in result.all()
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model usage: {str(e)}")

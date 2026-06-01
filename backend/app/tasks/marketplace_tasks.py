"""Marketplace scheduled tasks -- marketplace maintenance and cleanup."""
import asyncio

from celery.utils.log import get_task_logger
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.marketplace_tasks.cleanup_bottom_performers")
def cleanup_bottom_performers():
    """Bottom-performer cleanup task (daily at 02:00).

    Rules:
    - Published >=30 days, avg_rating <2.0 (has ratings), usage_count <10 -> needs_optimization
    - Published >=90 days, avg_rating <1.5 (has ratings), usage_count <5  -> frozen
    - Published >=90 days, usage_count == 0 -> idle
    """

    async def _cleanup():
        from sqlalchemy import select, and_

        from app.core.database import async_session
        from app.models.marketplace import MarketplaceItem

        stats = {"needs_optimization": 0, "frozen": 0, "idle": 0}

        async with async_session() as db:
            now = datetime.now(timezone.utc).replace(tzinfo=None)

            # Rule 1: >=30 days, low rating, low usage -> needs_optimization
            threshold_30d = now - timedelta(days=30)
            q1 = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.status == "published",
                    MarketplaceItem.published_at <= threshold_30d,
                    MarketplaceItem.avg_rating < 2.0,
                    MarketplaceItem.avg_rating > 0,
                    MarketplaceItem.usage_count < 10,
                )
            )
            result = await db.execute(q1)
            for item in result.scalars().all():
                item.status = "needs_optimization"
                stats["needs_optimization"] += 1

            # Rule 2: >=90 days, very low rating, low usage -> frozen
            threshold_90d = now - timedelta(days=90)
            q2 = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.status == "published",
                    MarketplaceItem.published_at <= threshold_90d,
                    MarketplaceItem.avg_rating < 1.5,
                    MarketplaceItem.avg_rating > 0,
                    MarketplaceItem.usage_count < 5,
                )
            )
            result = await db.execute(q2)
            for item in result.scalars().all():
                item.status = "frozen"
                item.frozen_at = now
                item.frozen_reason = "系统自动冻结：长期低评分低使用率"
                stats["frozen"] += 1

            # Rule 3: >=90 days, zero usage -> idle
            q3 = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.status == "published",
                    MarketplaceItem.published_at <= threshold_90d,
                    MarketplaceItem.usage_count == 0,
                )
            )
            result = await db.execute(q3)
            for item in result.scalars().all():
                item.status = "idle"
                stats["idle"] += 1

            await db.commit()

        logger.info("Marketplace cleanup completed: %s", stats)
        return stats

    return asyncio.get_event_loop().run_until_complete(_cleanup())

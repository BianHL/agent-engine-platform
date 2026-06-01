"""Cleanup and maintenance tasks."""
import os
import time

from celery.utils.log import get_task_logger
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_memory")
def cleanup_expired_memory():
    """Clean up expired short-term memory entries."""
    logger.info("Running expired memory cleanup")
    # Redis TTL handles this automatically, but this task
    # can clean up orphaned long-term memories
    return {"status": "completed"}


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_temp_files")
def cleanup_temp_files(max_age_hours: int = 24):
    """Clean up temporary uploaded files older than max_age_hours."""
    upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
    if not os.path.exists(upload_dir):
        return {"status": "no_upload_dir"}

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0
    for root, dirs, files in os.walk(upload_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.getmtime(fp) < cutoff:
                    os.remove(fp)
                    removed += 1
            except OSError:
                pass

    logger.info(f"Cleaned up {removed} temp files")
    return {"removed": removed}


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_sessions")
def cleanup_expired_sessions(max_inactive_days: int = 30):
    """Delete conversations inactive beyond threshold and with status='inactive'."""
    import asyncio

    from app.models.base import ConversationModel
    from app.core.database import async_session

    async def _cleanup():
        async with async_session() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_inactive_days)
            stmt = select_conversations_for_cleanup(cutoff)
            result = await db.execute(stmt)
            conversation_ids = [row[0] for row in result.all()]

            if not conversation_ids:
                return {"deleted": 0}

            # 批量删除（级联删除会处理关联数据）
            for cid in conversation_ids:
                conv = await db.get(ConversationModel, cid)
                if conv:
                    await db.delete(conv)

            await db.flush()
            logger.info(f"Cleaned up {len(conversation_ids)} expired sessions")
            return {"deleted": len(conversation_ids)}

    from sqlalchemy import select

    def select_conversations_for_cleanup(cutoff):
        return (
            select(ConversationModel.id)
            .where(
                ConversationModel.status == "inactive",
                ConversationModel.updated_at < cutoff,
            )
        )

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_old_audit_logs")
def cleanup_old_audit_logs(retention_days: int = 90):
    """Delete operation_logs older than retention period."""
    import asyncio

    from app.models.base import OperationLogModel
    from app.core.database import async_session
    from sqlalchemy import select, delete

    async def _cleanup():
        async with async_session() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # 先计数
            count_stmt = select(OperationLogModel.id).where(
                OperationLogModel.created_at < cutoff
            )
            result = await db.execute(count_stmt)
            ids = [row[0] for row in result.all()]

            if not ids:
                return {"deleted": 0}

            # 批量删除
            await db.execute(
                delete(OperationLogModel).where(
                    OperationLogModel.created_at < cutoff
                )
            )
            await db.flush()

            logger.info(f"Cleaned up {len(ids)} old audit logs")
            return {"deleted": len(ids)}

    return asyncio.get_event_loop().run_until_complete(_cleanup())

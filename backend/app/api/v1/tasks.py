"""Task queue management API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.platform.task_service.task_service import TaskQueueService
from app.schemas.api import StatusResponse, TaskStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Singleton service instance (no DB dependency)
_task_service = TaskQueueService()


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    user: dict = Depends(get_current_user)):
    """Get the status and progress of an async task."""
    result = await _task_service.get_task_status(task_id)
    if result.get("status") == "UNKNOWN":
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    user: dict = Depends(require_permission("task", "update"))):
    """Cancel a running task."""
    result = await _task_service.cancel_task(task_id)
    return result


@router.get("/dead-letters")
async def list_dead_letters(
    user: dict = Depends(get_current_user)):
    """List dead letter queue entries (failed tasks)."""
    try:
        return await _task_service.get_dead_letters()
    except Exception as e:
        logger.error("Failed to retrieve dead letters: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve dead letter queue")


@router.post("/dead-letters/{index}/retry")
async def retry_dead_letter(
    index: int,
    user: dict = Depends(require_permission("task", "update"))):
    """Retry a dead letter task by index."""
    try:
        return await _task_service.retry_dead_letter(index)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

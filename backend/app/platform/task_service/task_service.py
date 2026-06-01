"""Task queue service wrapping Celery operations."""
import time
from typing import Optional


class TaskQueueService:
    """Service for submitting and tracking async tasks."""

    def __init__(self, celery_app=None):
        self._celery = celery_app
        # In-memory fallback when Celery is not available
        self._tasks: dict[str, dict] = {}

    async def submit_document_processing(
        self,
        document_id: str,
        file_path: str,
        file_type: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        chunking_strategy: str = "recursive",
        tenant_id: str = "",
        knowledge_base_id: str = "",
    ) -> str:
        """Submit a document processing task. Returns task_id."""
        if self._celery:
            result = self._celery.send_task(
                "app.tasks.document_tasks.process_document",
                kwargs={
                    "document_id": document_id,
                    "file_path": file_path,
                    "file_type": file_type,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "chunking_strategy": chunking_strategy,
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                },
                queue="document",
            )
            return result.id
        else:
            # Fallback: synchronous processing
            import asyncio
            task_id = f"local_{document_id}_{int(time.time())}"
            self._tasks[task_id] = {
                "task_id": task_id,
                "status": "PENDING",
                "progress": 0.0,
            }
            return task_id

    async def get_task_status(self, task_id: str) -> dict:
        """Get task status and progress."""
        if self._celery:
            from app.tasks.celery_app import celery_app
            result = celery_app.AsyncResult(task_id)
            response = {
                "task_id": task_id,
                "status": result.status,
            }
            if result.info and isinstance(result.info, dict):
                response.update(result.info)
            return response
        else:
            return self._tasks.get(task_id, {"task_id": task_id, "status": "UNKNOWN"})

    async def cancel_task(self, task_id: str) -> dict:
        """Cancel a running task."""
        if self._celery:
            self._celery.control.revoke(task_id, terminate=True)
            return {"task_id": task_id, "status": "cancelled"}
        else:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "CANCELLED"
            return {"task_id": task_id, "status": "cancelled"}

    async def get_dead_letters(self) -> list[dict]:
        """Get dead letter queue contents."""
        from app.tasks.document_tasks import get_dead_letters
        return get_dead_letters()

    async def retry_dead_letter(self, index: int) -> dict:
        """Retry a dead letter task."""
        from app.tasks.document_tasks import retry_dead_letter
        return retry_dead_letter(index)

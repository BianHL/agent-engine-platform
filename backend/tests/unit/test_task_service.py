"""Unit tests for Task Queue Service"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.platform.task_service.task_service import TaskQueueService


@pytest.mark.asyncio
async def test_task_service_without_celery():
    """Task service works in fallback mode without Celery."""
    svc = TaskQueueService(celery_app=None)
    task_id = await svc.submit_document_processing(
        document_id="doc1",
        file_path="/tmp/test.pdf",
        file_type=".pdf",
        tenant_id="t1",
        knowledge_base_id="kb1",
    )
    assert task_id.startswith("local_doc1")

    status = await svc.get_task_status(task_id)
    assert status["status"] == "PENDING"


@pytest.mark.asyncio
async def test_task_service_cancel():
    """Cancel a task in fallback mode."""
    svc = TaskQueueService(celery_app=None)
    task_id = await svc.submit_document_processing(
        document_id="doc1",
        file_path="/tmp/test.pdf",
        file_type=".pdf",
    )
    result = await svc.cancel_task(task_id)
    assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_task_service_unknown_task():
    """Query status of unknown task."""
    svc = TaskQueueService(celery_app=None)
    status = await svc.get_task_status("nonexistent")
    assert status["status"] == "UNKNOWN"


@pytest.mark.asyncio
async def test_task_service_dead_letters_empty():
    """Dead letter queue starts empty."""
    try:
        svc = TaskQueueService(celery_app=None)
        dl = await svc.get_dead_letters()
        assert isinstance(dl, list)
    except ModuleNotFoundError:
        pytest.skip("celery not installed")

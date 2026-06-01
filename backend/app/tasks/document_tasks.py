"""Document processing tasks with retry and progress tracking."""
import time
import traceback
from pathlib import Path

from celery import Task
from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)

# Dead letter queue storage (in-memory for now, would be DB in production)
_dead_letters: list[dict] = []


class RetryableTask(Task):
    """Base task with exponential backoff retry."""

    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed permanently: {exc}")
        _dead_letters.append({
            "task_id": task_id,
            "task_name": self.name,
            "args": args,
            "kwargs": kwargs,
            "error": str(exc),
            "traceback": str(einfo),
            "timestamp": time.time(),
        })

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(base=RetryableTask, bind=True, name="app.tasks.document_tasks.process_document")
def process_document(self, document_id: str, file_path: str, file_type: str,
                     chunk_size: int = 500, chunk_overlap: int = 50,
                     chunking_strategy: str = "recursive",
                     tenant_id: str = "", knowledge_base_id: str = ""):
    """Process a document: parse, chunk, and index."""
    from app.engines.knowledge_engine.chunker.chunker import DocumentChunker
    from app.engines.knowledge_engine.parser.pdf_parser import PDFParser
    from app.engines.knowledge_engine.parser.word_parser import WordParser
    from app.engines.knowledge_engine.parser.ppt_parser import PPTParser
    from app.engines.knowledge_engine.parser.excel_parser import ExcelParser
    from app.engines.knowledge_engine.parser.text_parser import TextParser

    PARSERS = {
        ".pdf": PDFParser(), ".docx": WordParser(), ".doc": WordParser(),
        ".pptx": PPTParser(), ".xlsx": ExcelParser(), ".xls": ExcelParser(),
        ".txt": TextParser(), ".csv": TextParser(), ".html": TextParser(),
        ".htm": TextParser(), ".md": TextParser(), ".json": TextParser(),
        ".xml": TextParser(),
    }

    logger.info(f"Processing document {document_id}: {file_path}")

    # Update progress
    self.update_state(state="PROGRESS", meta={"progress": 0.1, "stage": "parsing"})

    parser = PARSERS.get(file_type)
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")

    parsed = parser.safe_parse(file_path)
    content = parsed.get("content", "")

    self.update_state(state="PROGRESS", meta={"progress": 0.4, "stage": "chunking"})

    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_text(content, strategy=chunking_strategy)

    self.update_state(state="PROGRESS", meta={"progress": 0.7, "stage": "indexing"})

    # Index chunks (vector store integration would go here)
    chunk_data = [
        {
            "id": f"{document_id}_{i}",
            "content": chunk["content"],
            "metadata": {
                "document_id": document_id,
                "chunk_index": i,
                "tenant_id": tenant_id,
                "knowledge_base_id": knowledge_base_id,
            },
        }
        for i, chunk in enumerate(chunks)
    ]

    self.update_state(state="PROGRESS", meta={"progress": 1.0, "stage": "complete"})

    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "status": "ready",
    }


@celery_app.task(name="app.tasks.document_tasks.get_task_progress")
def get_task_progress(task_id: str) -> dict:
    """Query task progress by task_id."""
    result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.info and isinstance(result.info, dict):
        response.update(result.info)
    return response


@celery_app.task(name="app.tasks.document_tasks.cancel_task")
def cancel_task(task_id: str) -> dict:
    """Cancel a running task."""
    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
    return {"task_id": task_id, "status": "cancelled"}


def get_dead_letters() -> list[dict]:
    """Return dead letter queue contents."""
    return list(_dead_letters)


def retry_dead_letter(index: int) -> dict:
    """Retry a task from the dead letter queue."""
    if index < 0 or index >= len(_dead_letters):
        raise ValueError(f"Invalid dead letter index: {index}")
    entry = _dead_letters.pop(index)
    task = celery_app.send_task(
        entry["task_name"],
        args=entry["args"],
        kwargs=entry["kwargs"],
    )
    return {"new_task_id": task.id, "status": "retried"}

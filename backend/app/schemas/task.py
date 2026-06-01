"""Task and async operation related schemas."""
from typing import Any, Optional

from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    status: str

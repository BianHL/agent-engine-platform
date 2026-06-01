"""Memory related schemas."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryContextResponse(BaseModel):
    short_term: list
    working_summary: str
    relevant_memories: list


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=50)

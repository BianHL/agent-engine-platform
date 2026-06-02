"""Multi-Agent/Crew related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CreateCrewRequest(BaseModel):
    name: str
    description: str = ""
    process: str = "sequential"
    config: dict = {}


class UpdateCrewRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    process: Optional[str] = None
    config: Optional[dict] = None


class CrewResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    process: str
    config: dict
    status: str
    total_executions: int = 0
    last_executed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrewExecutionResponse(BaseModel):
    id: str
    crew_id: str
    tenant_id: str
    user_id: Optional[str] = None
    status: str
    inputs: dict
    results: Optional[list] = None
    agent_results: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExecuteCrewRequest(BaseModel):
    inputs: dict = {}
    user_id: Optional[str] = None


class HandoffRequest(BaseModel):
    source_agent_id: str
    target_agent_ids: List[str]
    handoff_config: dict = {}


class HandoffResponse(BaseModel):
    id: str
    tenant_id: str
    source_agent_id: str
    target_agent_ids: list
    handoff_config: dict
    status: str
    total_handoffs: int = 0
    last_handoff_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

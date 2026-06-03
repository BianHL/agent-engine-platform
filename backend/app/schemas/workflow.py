"""Workflow related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CreateWorkflowRequest(BaseModel):
    name: str
    description: str = ""
    icon_url: Optional[str] = None
    category: Optional[str] = None
    agent_id: Optional[str] = None
    dag_config: dict = {}
    max_execution_time: Optional[int] = None
    max_iterations: int = 100
    retry_policy: Optional[dict] = None
    visibility: str = "private"


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: Optional[str] = None
    dag_config: Optional[dict] = None
    max_execution_time: Optional[int] = None
    max_iterations: Optional[int] = None
    retry_policy: Optional[dict] = None
    visibility: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: str
    tenant_id: str
    agent_id: Optional[str] = None
    name: str
    description: str
    icon_url: Optional[str] = None
    category: Optional[str] = None
    dag_config: dict
    max_execution_time: Optional[int] = None
    max_iterations: int = 100
    retry_policy: Optional[dict] = None
    status: str
    visibility: str = "private"
    version: int
    published_at: Optional[datetime] = None
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: Optional[int] = None
    last_executed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_version: int
    tenant_id: str
    trigger_type: str = "manual"
    trigger_id: Optional[str] = None
    status: str
    node_states: dict
    current_node_id: Optional[str] = None
    variables: dict
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    execution_log: list
    node_logs: list
    trace_tree: dict
    trace_id: Optional[str] = None
    error_message: Optional[str] = None
    error_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RunWorkflowRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None
    trigger_type: str = "manual"


class CreateTriggerRequest(BaseModel):
    name: str
    workflow_id: str
    trigger_type: str = "cron"
    config: dict = {}
    filter_conditions: Optional[dict] = None


class TriggerResponse(BaseModel):
    id: str
    tenant_id: str
    workflow_id: str
    name: str
    trigger_type: str
    config: dict
    filter_conditions: Optional[dict] = None
    enabled: bool
    total_triggered: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_triggered_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    next_run_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version: int
    dag_config: dict
    change_log: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

"""Tool related schemas."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class CreateToolRequest(BaseModel):
    name: str
    description: str = ""
    icon_url: Optional[str] = None
    tool_type: str = "custom"
    api_schema: Optional[dict] = None
    api_endpoint: Optional[str] = None
    api_method: Optional[str] = None
    api_headers: Optional[dict] = None
    mcp_server_url: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    config: dict = {}
    timeout: int = 30
    retry_count: int = 0
    enabled: bool = True


class UpdateToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    api_schema: Optional[dict] = None
    api_endpoint: Optional[str] = None
    api_method: Optional[str] = None
    api_headers: Optional[dict] = None
    mcp_server_url: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    config: Optional[dict] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None
    enabled: Optional[bool] = None


class ToolResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    icon_url: Optional[str] = None
    tool_type: str
    api_schema: dict = {}
    api_endpoint: Optional[str] = None
    api_method: Optional[str] = None
    api_headers: Optional[dict] = None
    mcp_server_url: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    config: dict = {}
    timeout: int = 30
    retry_count: int = 0
    enabled: bool
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: Optional[int] = None
    last_used_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ToolExecutionResponse(BaseModel):
    id: str
    tool_id: str
    tenant_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    agent_id: Optional[str] = None
    input_data: dict
    output_data: Optional[dict] = None
    status: str
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExecuteToolRequest(BaseModel):
    params: Dict[str, Any] = {}
    timeout: int = 30

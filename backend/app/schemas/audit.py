"""Audit Log related schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OperationLogResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    details: Optional[dict] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_body: Optional[dict] = None
    response_status: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

"""Webhook related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CreateWebhookRequest(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str] = []
    headers: Optional[dict] = None
    max_retries: int = 3
    retry_interval_seconds: int = 60
    timeout_seconds: int = 30
    filter_conditions: Optional[dict] = None


class UpdateWebhookRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[dict] = None
    max_retries: Optional[int] = None
    retry_interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    filter_conditions: Optional[dict] = None
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    url: str
    events: List[str]
    headers: Optional[dict] = None
    max_retries: int = 3
    retry_interval_seconds: int = 60
    timeout_seconds: int = 30
    filter_conditions: Optional[dict] = None
    enabled: bool
    total_deliveries: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_delivered_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WebhookEventResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    payload: dict
    status: str
    retry_count: int
    next_retry_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

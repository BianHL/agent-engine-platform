"""User and Tenant related schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateTenantRequest(BaseModel):
    name: str
    code: str
    parent_id: Optional[str] = None
    org_level: str = "company"
    max_agents: int = 10
    max_users: int = 100
    max_storage_gb: int = 10
    subscription_plan: str = "free"
    features: dict = {}
    settings: Optional[dict] = None
    timezone: str = "Asia/Shanghai"
    locale: str = "zh-CN"
    billing_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    parent_id: Optional[str] = None
    org_level: str = "company"
    org_path: str = ""
    max_agents: int
    max_users: int
    max_storage_gb: int
    subscription_plan: str = "free"
    subscription_expires_at: Optional[datetime] = None
    features: dict
    settings: Optional[dict] = None
    timezone: str = "Asia/Shanghai"
    locale: str = "zh-CN"
    billing_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None
    max_agents: Optional[int] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[int] = None
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    billing_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class UpdateTenantFeaturesRequest(BaseModel):
    features: dict


class UpdateTenantQuotaRequest(BaseModel):
    max_agents: Optional[int] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[int] = None


class DepartmentCreate(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    leader_id: Optional[str] = None
    sort_order: int = 0


class DepartmentResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    level: int = 1
    path: str = ""
    leader_id: Optional[str] = None
    sort_order: int = 0
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Re-export user schemas from auth.py for convenience
from app.schemas.auth import (  # noqa: E402
    RegisterUserRequest,
    UpdateUserRequest,
    UserResponse,
)

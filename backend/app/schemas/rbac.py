"""RBAC (Role-Based Access Control) related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CreateRoleRequest(BaseModel):
    name: str
    code: str
    description: str = ""
    is_system: bool = False
    is_default: bool = False
    priority: int = 0
    data_scope: str = "self"
    permissions: List[str] = []


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    data_scope: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    description: str
    is_system: bool
    is_default: bool = False
    priority: int = 0
    data_scope: str = "self"
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateRolePermissionsRequest(BaseModel):
    permissions: List[str]


class RolePermissionResponse(BaseModel):
    role_id: str
    permissions: List[str]


class PermissionResponse(BaseModel):
    id: str
    module: str
    resource: str
    action: str
    name: str
    description: str = ""
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleRequest(BaseModel):
    user_id: str
    role_id: str


class UserRoleResponse(BaseModel):
    id: str
    user_id: str
    role_id: str
    tenant_id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

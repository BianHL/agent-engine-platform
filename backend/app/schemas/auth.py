"""Authentication related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    message: str
    revoked_at: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    tenant_id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    department_id: Optional[str] = None
    position: Optional[str] = None
    status: str
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    login_count: int = 0
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None
    settings: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    role: Optional[str] = "viewer"
    department_id: Optional[str] = None
    position: Optional[str] = None


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[dict] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)

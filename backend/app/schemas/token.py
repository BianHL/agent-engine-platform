"""API Token related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateTokenRequest(BaseModel):
    name: str
    permissions: List[str] = []  # list of "resource:action" strings, empty = unrestricted
    expiry_days: int = Field(30, ge=1, le=365)


class TokenResponseItem(BaseModel):
    id: str
    name: str
    permissions: List[str]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenCreatedResponse(BaseModel):
    id: str
    name: str
    token: str  # raw token — returned only once
    permissions: List[str]
    expires_at: Optional[datetime] = None


class UpdateTokenRequest(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None
    expiry_days: Optional[int] = Field(None, ge=1, le=365)

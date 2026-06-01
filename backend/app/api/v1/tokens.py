"""API Token management endpoints."""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.base import ApiTokenModel
from app.schemas.api import (
    CreateTokenRequest,
    TokenCreatedResponse,
    TokenResponseItem,
    UpdateTokenRequest,
)

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_token(
    body: CreateTokenRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("api_token", "create")),
):
    """Create an API token.

    Returns the raw token **once**. After this response the raw token is
    discarded; only the SHA-256 hash is stored.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=body.expiry_days)

    token = ApiTokenModel(
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        name=body.name,
        token_hash=token_hash,
        permissions=body.permissions,
        expires_at=expires_at,
        status="active",
    )
    db.add(token)
    await db.flush()

    return {
        "id": token.id,
        "name": token.name,
        "token": raw_token,
        "permissions": token.permissions or [],
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }


@router.get("/")
async def list_tokens(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List API tokens for the current user. Raw tokens are never returned."""
    stmt = (
        select(ApiTokenModel)
        .where(
            ApiTokenModel.user_id == user["id"],
            ApiTokenModel.tenant_id == user["tenant_id"],
        )
        .order_by(ApiTokenModel.created_at.desc())
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "permissions": t.permissions or [],
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tokens
    ]


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("api_token", "revoke")),
):
    """Revoke (deactivate) an API token."""
    stmt = select(ApiTokenModel).where(
        ApiTokenModel.id == token_id,
        ApiTokenModel.user_id == user["id"],
        ApiTokenModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    token.status = "revoked"
    await db.flush()
    return None


@router.put("/{token_id}")
async def update_token(
    token_id: str,
    body: UpdateTokenRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update a token's name, permissions, or expiry."""
    stmt = select(ApiTokenModel).where(
        ApiTokenModel.id == token_id,
        ApiTokenModel.user_id == user["id"],
        ApiTokenModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if token.status == "revoked":
        raise HTTPException(status_code=400, detail="Cannot update a revoked token")

    if body.name is not None:
        token.name = body.name
    if body.permissions is not None:
        token.permissions = body.permissions
    if body.expiry_days is not None:
        token.expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=body.expiry_days)

    await db.flush()

    return {
        "id": token.id,
        "name": token.name,
        "permissions": token.permissions or [],
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
        "status": token.status,
        "created_at": token.created_at.isoformat() if token.created_at else None,
    }

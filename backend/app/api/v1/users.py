"""User management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.rbac import require_permission
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.base import UserModel
from app.schemas.api import (
    PaginatedResponse,
    RegisterUserRequest,
    UpdateUserRequest,
    UserResponse)

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_ROLES = {"owner", "admin", "contributor", "viewer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_role("admin"))):
    """Register a new user (admin only)."""
    # Check if username already exists
    stmt = select(UserModel).where(UserModel.username == body.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    # Restrict role to viewer or contributor only, default to viewer
    role = body.role if body.role in ("viewer", "contributor") else "viewer"
    user = UserModel(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        email=body.email,
        role=role,
        tenant_id=_admin["tenant_id"],
    )
    db.add(user)
    await db.flush()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "status": user.status,
    }


@router.get("/me")
async def get_me(
    user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


@router.put("/me")
async def update_me(
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Update current user profile (email only for self-service)."""
    stmt = select(UserModel).where(UserModel.id == user["id"])
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        db_user.email = body.email
    await db.flush()

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "tenant_id": db_user.tenant_id,
        "status": db_user.status,
    }


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """List users in the current tenant (admin only)."""
    tenant_id = user["tenant_id"]

    count_result = await db.execute(
        select(func.count()).where(UserModel.tenant_id == tenant_id)
    )
    total = count_result.scalar()

    stmt = (
        select(UserModel)
        .where(UserModel.tenant_id == tenant_id)
        .order_by(UserModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "tenant_id": u.tenant_id,
                "status": u.status,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Update a user (admin only). Can change role and status."""
    stmt = select(UserModel).where(
        UserModel.id == user_id,
        UserModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        db_user.email = body.email
    if body.role is not None:
        if body.role not in ALLOWED_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Allowed: {', '.join(sorted(ALLOWED_ROLES))}")
        db_user.role = body.role
    if body.status is not None:
        db_user.status = body.status
    await db.flush()

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "tenant_id": db_user.tenant_id,
        "status": db_user.status,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Deactivate a user (admin only). Sets status to 'inactive'."""
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    stmt = select(UserModel).where(
        UserModel.id == user_id,
        UserModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.status = "inactive"
    await db.flush()
    return None


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Reset a user's password (admin only)."""
    stmt = select(UserModel).where(
        UserModel.id == user_id,
        UserModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    db_user.hashed_password = get_password_hash(body.new_password)
    await db.flush()
    return {"status": "ok"}

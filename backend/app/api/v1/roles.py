"""Role management API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.base import PermissionModel, RoleModel, RolePermissionModel
from app.schemas.api import (
    CreateRoleRequest,
    RolePermissionResponse,
    RoleResponse,
    UpdateRolePermissionsRequest,
)

router = APIRouter(prefix="/roles", tags=["roles"])


async def _resolve_permission_ids(
    db: AsyncSession,
    permission_strs: list[str],
) -> list[str]:
    """Resolve 'resource:action' strings to permission IDs.

    Creates missing permissions on the fly.
    """
    ids = []
    for perm_str in permission_strs:
        if ":" not in perm_str:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permission format: {perm_str}. Expected 'resource:action'.",
            )
        resource, action = perm_str.split(":", 1)
        stmt = select(PermissionModel).where(
            PermissionModel.resource == resource,
            PermissionModel.action == action,
        )
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            perm = PermissionModel(
                resource=resource,
                action=action,
                description=f"{action} on {resource}",
            )
            db.add(perm)
            await db.flush()
        ids.append(perm.id)
    return ids


@router.get("/")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all roles for the current tenant."""
    stmt = (
        select(RoleModel)
        .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
        .where(RoleModel.tenant_id == user["tenant_id"])
        .order_by(RoleModel.created_at)
    )
    result = await db.execute(stmt)
    roles = result.scalars().all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_system": r.is_system,
            "permissions": [
                f"{rp.permission.resource}:{rp.permission.action}"
                for rp in r.role_permissions
            ],
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in roles
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("role", "create")),
):
    """Create a custom role with permissions."""
    # Check for duplicate name
    stmt = select(RoleModel).where(
        RoleModel.tenant_id == user["tenant_id"],
        RoleModel.name == body.name,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Role name already exists")

    role = RoleModel(
        tenant_id=user["tenant_id"],
        name=body.name,
        description=body.description,
        is_system=False,
    )
    db.add(role)
    await db.flush()

    # Assign permissions
    if body.permissions:
        perm_ids = await _resolve_permission_ids(db, body.permissions)
        for pid in perm_ids:
            db.add(RolePermissionModel(role_id=role.id, permission_id=pid))
        await db.flush()

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "permissions": body.permissions,
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None,
    }


@router.put("/{role_id}")
async def update_role(
    role_id: str,
    body: CreateRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("role", "update")),
):
    """Update a role's name, description, and permissions."""
    stmt = select(RoleModel).where(
        RoleModel.id == role_id,
        RoleModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system roles")

    role.name = body.name
    role.description = body.description

    # Replace permissions
    stmt_del = select(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
    result_del = await db.execute(stmt_del)
    for rp in result_del.scalars().all():
        await db.delete(rp)

    if body.permissions:
        perm_ids = await _resolve_permission_ids(db, body.permissions)
        for pid in perm_ids:
            db.add(RolePermissionModel(role_id=role.id, permission_id=pid))

    await db.flush()

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "permissions": body.permissions,
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None,
    }


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("role", "delete")),
):
    """Delete a custom role. System roles cannot be deleted."""
    stmt = select(RoleModel).where(
        RoleModel.id == role_id,
        RoleModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")

    await db.delete(role)
    await db.flush()
    return None


@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List permissions for a role."""
    stmt = (
        select(RoleModel)
        .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
        .where(
            RoleModel.id == role_id,
            RoleModel.tenant_id == user["tenant_id"],
        )
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return {
        "role_id": role.id,
        "permissions": [
            f"{rp.permission.resource}:{rp.permission.action}"
            for rp in role.role_permissions
        ],
    }


@router.put("/{role_id}/permissions")
async def set_role_permissions(
    role_id: str,
    body: UpdateRolePermissionsRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("role", "update")),
):
    """Replace all permissions for a role."""
    stmt = select(RoleModel).where(
        RoleModel.id == role_id,
        RoleModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Remove existing
    stmt_del = select(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
    result_del = await db.execute(stmt_del)
    for rp in result_del.scalars().all():
        await db.delete(rp)

    # Add new
    if body.permissions:
        perm_ids = await _resolve_permission_ids(db, body.permissions)
        for pid in perm_ids:
            db.add(RolePermissionModel(role_id=role.id, permission_id=pid))

    await db.flush()

    return {
        "role_id": role.id,
        "permissions": body.permissions,
    }

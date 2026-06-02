"""Role-Based Access Control (RBAC) permission system."""
from __future__ import annotations

import json
import logging
from typing import Optional, Set

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.base import PermissionModel, RoleModel, RolePermissionModel, UserModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis cache constants
# ---------------------------------------------------------------------------

_CACHE_TTL = 300  # 5 minutes
_CACHE_PREFIX = "rbac:perms"

# ---------------------------------------------------------------------------
# Permission definitions: resource -> allowed actions
# ---------------------------------------------------------------------------

PERMISSIONS: dict[str, list[str]] = {
    "agent": ["create", "read", "update", "delete", "publish"],
    "knowledge": ["create", "read", "update", "delete", "upload"],
    "workflow": ["create", "read", "update", "delete", "execute"],
    "tool": ["create", "read", "update", "delete", "execute"],
    "conversation": ["create", "read", "delete"],
    "user": ["create", "read", "update", "delete"],
    "tenant": ["read", "update", "manage_features", "manage_quota"],
    "audit": ["read", "export"],
    "api_token": ["create", "read", "revoke"],
    "webhook": ["create", "read", "update", "delete"],
    "role": ["create", "read", "update", "delete"],
    "marketplace": ["read", "submit", "review", "manage", "promote"],
}

# ---------------------------------------------------------------------------
# Default roles and their permission sets
# ---------------------------------------------------------------------------

# Each default role maps to a list of "resource:action" strings.
# Owner gets everything; Admin gets everything except tenant management;
# Contributor gets create/read/update on main resources; Viewer gets read only.

DEFAULT_ROLES: dict[str, dict] = {
    "Owner": {
        "description": "Full access to all resources",
        "is_system": True,
        "permissions": [
            f"{res}:{act}"
            for res, actions in PERMISSIONS.items()
            for act in actions
        ],
    },
    "Admin": {
        "description": "Administrative access, excluding tenant management",
        "is_system": True,
        "permissions": [
            f"{res}:{act}"
            for res, actions in PERMISSIONS.items()
            if res != "tenant"
            for act in actions
        ],
    },
    "Contributor": {
        "description": "Create, read, and update on main resources",
        "is_system": True,
        "permissions": [
            "agent:create", "agent:read", "agent:update",
            "knowledge:create", "knowledge:read", "knowledge:update", "knowledge:upload",
            "workflow:create", "workflow:read", "workflow:update", "workflow:execute",
            "tool:create", "tool:read", "tool:update", "tool:execute",
            "conversation:create", "conversation:read",
            "api_token:create", "api_token:read",
            "webhook:create", "webhook:read",
        ],
    },
    "Viewer": {
        "description": "Read-only access to resources",
        "is_system": True,
        "permissions": [
            "agent:read",
            "knowledge:read",
            "workflow:read",
            "tool:read",
            "conversation:read",
            "user:read",
            "tenant:read",
            "audit:read",
            "api_token:read",
            "webhook:read",
        ],
    },
}


async def _get_or_create_permission(
    db: AsyncSession,
    resource: str,
    action: str,
) -> PermissionModel:
    """Get existing permission or create a new one."""
    stmt = select(PermissionModel).where(
        PermissionModel.resource == resource,
        PermissionModel.action == action,
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm:
        return perm

    perm = PermissionModel(
        resource=resource,
        action=action,
        module=resource,
        name=f"{resource}:{action}",
        description=f"{action} on {resource}",
    )
    db.add(perm)
    await db.flush()
    return perm


async def init_default_roles(db: AsyncSession, tenant_id: str) -> None:
    """Create default roles with permissions for a tenant.

    Idempotent: skips roles that already exist for the tenant.
    """
    for role_name, role_def in DEFAULT_ROLES.items():
        # Check if role already exists
        stmt = select(RoleModel).where(
            RoleModel.tenant_id == tenant_id,
            RoleModel.name == role_name,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue

        # Create role
        role = RoleModel(
            tenant_id=tenant_id,
            name=role_name,
            code=role_name.lower(),
            description=role_def["description"],
            is_system=role_def["is_system"],
        )
        db.add(role)
        await db.flush()

        # Create permissions and role-permission links
        for perm_str in role_def["permissions"]:
            resource, action = perm_str.split(":", 1)
            perm = await _get_or_create_permission(db, resource, action)
            rp = RolePermissionModel(role_id=role.id, permission_id=perm.id)
            db.add(rp)

        await db.flush()


def _cache_key(tenant_id: str, user_id: str) -> str:
    """Build the Redis cache key for a user's permission set."""
    return f"{_CACHE_PREFIX}:{tenant_id}:{user_id}"


async def get_user_permissions(
    user_id: str,
    tenant_id: str,
    db: AsyncSession,
) -> Set[str]:
    """Return the set of 'resource:action' permission strings for a user.

    Looks up the user's role, then resolves all associated permissions.
    Falls back to the legacy `role` string field if no RBAC role is found.

    Results are cached in Redis for 5 minutes.  If Redis is unavailable the
    function falls back to a direct database query without interruption.
    """
    # --- Try Redis cache first ---
    key = _cache_key(tenant_id, user_id)
    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        cached = await redis.get(key)
        if cached is not None:
            return set(json.loads(cached))
    except Exception:
        logger.debug("RBAC cache read failed, falling back to DB", exc_info=True)

    # --- Cache miss: query DB ---
    perms = await _query_user_permissions(user_id, tenant_id, db)

    # --- Populate cache (best-effort) ---
    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.set(key, json.dumps(sorted(perms)), ex=_CACHE_TTL)
    except Exception:
        logger.debug("RBAC cache write failed", exc_info=True)

    return perms


async def _query_user_permissions(
    user_id: str,
    tenant_id: str,
    db: AsyncSession,
) -> Set[str]:
    """Database query for user permissions (the original logic)."""
    # Get user to find their role name
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return set()

    # Try to find an RBAC role matching the user's role name
    stmt = (
        select(RoleModel)
        .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
        .where(
            RoleModel.tenant_id == tenant_id,
            RoleModel.name == user.role,
        )
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role:
        return {
            f"{rp.permission.resource}:{rp.permission.action}"
            for rp in role.role_permissions
        }

    # Fallback: if user.role is "admin", grant all permissions
    if user.role == "admin":
        return {
            f"{res}:{act}"
            for res, actions in PERMISSIONS.items()
            for act in actions
        }

    return set()


async def invalidate_user_permissions(user_id: str, tenant_id: str) -> None:
    """Invalidate the cached permission set for a user.

    Call this when a user's role or permissions are modified so that the next
    ``get_user_permissions`` call fetches fresh data from the database.
    """
    key = _cache_key(tenant_id, user_id)
    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.delete(key)
    except Exception:
        logger.debug("RBAC cache invalidation failed", exc_info=True)


async def check_permission(
    user_id: str,
    tenant_id: str,
    resource: str,
    action: str,
    db: AsyncSession,
) -> bool:
    """Check whether a user has a specific permission."""
    perms = await get_user_permissions(user_id, tenant_id, db)
    return f"{resource}:{action}" in perms


def _require_permission_factory(resource: str, action: str):
    """Create a FastAPI dependency that enforces a specific permission."""

    async def _check(
        user: dict,  # injected by the caller via get_current_user_with_permissions
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        has_perm = await check_permission(
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            resource=resource,
            action=action,
            db=db,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}:{action}",
            )
        return user

    return _check


def require_permission(resource: str, action: str):
    """FastAPI dependency that raises 403 if the user lacks the permission.

    Usage::

        @router.post("/agents")
        async def create_agent(user=Depends(require_permission("agent", "create"))):
            ...
    """
    from app.core.auth import get_current_user_with_permissions

    async def _dep(
        user: dict = Depends(get_current_user_with_permissions),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        has_perm = await check_permission(
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            resource=resource,
            action=action,
            db=db,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}:{action}",
            )
        return user

    return _dep

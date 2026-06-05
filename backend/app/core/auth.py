"""Authentication and authorization dependencies."""
import hashlib
import logging
from datetime import UTC, datetime
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.base import ApiTokenModel, UserModel

security_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# JWT Token Blacklist (Redis-based)
# ---------------------------------------------------------------------------

async def revoke_token(token_jti: str, ttl: Optional[int] = None) -> None:
    """Add a token JTI to the Redis blacklist.

    Args:
        token_jti: JWT ID (JTI) claim to blacklist
        ttl: Time-to-live in seconds (defaults to token expiration time)
    """
    redis = await get_redis()
    key = f"token_blacklist:{token_jti}"
    if ttl is None:
        # Default to ACCESS_TOKEN_EXPIRE_MINUTES
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await redis.setex(key, ttl, "1")


async def is_token_revoked(token_jti: str) -> bool:
    """Check if a token JTI is in the blacklist.

    Returns True if the token has been revoked.
    """
    try:
        redis = await get_redis()
        key = f"token_blacklist:{token_jti}"
        return await redis.exists(key) > 0
    except Exception:
        # Fail closed: if Redis is unavailable, treat token as revoked
        # to prevent unauthorized access when security infrastructure is down
        logger.exception("Redis unavailable during token revocation check; rejecting token")
        return True


async def revoke_all_user_tokens(user_id: str, ttl: Optional[int] = None) -> int:
    """Revoke all tokens for a user by adding their user-specific marker.

    This works by setting a user-specific blacklist entry that is checked
    during authentication. All new JWTs will include a user_version claim
    that increments when this is called.

    Args:
        user_id: User ID whose tokens should be revoked
        ttl: Time-to-live in seconds

    Returns:
        Number of tokens revoked (for reporting)
    """
    redis = await get_redis()
    key = f"user_token_version:{user_id}"
    if ttl is None:
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    # Increment the user's token version
    # New tokens will include this version, old tokens will be rejected
    new_version = await redis.incr(key)
    if ttl > 0:
        await redis.expire(key, ttl)
    return new_version


async def get_user_token_version(user_id: str) -> int:
    """Get the current token version for a user.

    Returns 0 if no version is set (first-time user).
    """
    try:
        redis = await get_redis()
        key = f"user_token_version:{user_id}"
        version = await redis.get(key)
        return int(version) if version else 0
    except Exception:
        return 0


async def _authenticate_token(
    credentials: HTTPAuthorizationCredentials,
    db: AsyncSession,
) -> dict:
    """Authenticate a bearer token — try JWT first, then API token fallback.

    Returns a user info dict on success; raises HTTPException on failure.
    """
    token_str = credentials.credentials

    # --- Attempt 1: JWT decode ---
    try:
        payload = decode_token(token_str)
        user_id = payload.get("sub")
        token_jti = payload.get("jti")

        # Check token blacklist
        if token_jti and await is_token_revoked(token_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        # FW-C03: validate that sub is a non-empty string
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
            )

        # Check token version to support logout-all
        token_version = payload.get("tv", 0)
        current_version = await get_user_token_version(user_id)
        if current_version > 0 and token_version < current_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been superseded by logout-all",
            )

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.status == "active":
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tenant_id": user.tenant_id,
                "department_id": user.department_id,
                "status": user.status,
                "_auth_method": "jwt",
                "_token_jti": token_jti,
            }
    except HTTPException:
        raise  # Re-raise HTTPException (including revoked token error)
    except JWTError:
        pass  # Expected: fall through to API token lookup

    # --- Attempt 2: API token lookup ---
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    stmt = (
        select(ApiTokenModel)
        .where(
            ApiTokenModel.token_hash == token_hash,
            ApiTokenModel.status == "active",
        )
    )
    result = await db.execute(stmt)
    api_token = result.scalar_one_or_none()

    if api_token:
        # Check expiry
        if api_token.expires_at and api_token.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API token has expired",
            )

        # Load the owning user
        stmt = select(UserModel).where(UserModel.id == api_token.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.status == "active":
            # Update last_used_at
            api_token.last_used_at = datetime.now(UTC).replace(tzinfo=None)
            await db.flush()

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tenant_id": user.tenant_id,
                "department_id": user.department_id,
                "status": user.status,
                "_auth_method": "api_token",
                "_token_permissions": api_token.permissions or [],
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Decode JWT or API token and return user info dict.

    Also sets ``request.state.user_id`` and ``request.state.tenant_id``
    so downstream middleware (e.g. audit logging) can access them.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user = await _authenticate_token(credentials, db)
    # FW-H01: expose user context to middleware via request.state
    request.state.user_id = user.get("id")
    request.state.tenant_id = user.get("tenant_id")
    return user


async def get_current_user_with_permissions(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Like get_current_user, but also loads RBAC role permissions.

    Adds ``_permissions`` key (set of 'resource:action' strings) to the
    returned dict.  If the auth method is API token, the token's own
    permission scope is intersected with the role permissions.
    """
    user = await get_current_user(request, credentials, db)

    from app.core.rbac import get_user_permissions

    role_perms = await get_user_permissions(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        db=db,
    )

    # If authenticated via API token, intersect with token scope
    if user.get("_auth_method") == "api_token":
        token_scope = set(user.get("_token_permissions", []))
        if token_scope:
            user["_permissions"] = role_perms & token_scope
        else:
            # Empty token scope means no restriction (full role perms)
            user["_permissions"] = role_perms
    else:
        user["_permissions"] = role_perms

    return user


def require_role(*roles: str):
    """Dependency factory: require the current user to have one of the given roles."""

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return user

    return _check


async def get_tenant_id(user: dict = Depends(get_current_user)) -> str:
    """Extract tenant_id from the authenticated user."""
    return user["tenant_id"]


def require_data_scope(scope: str = "tenant"):
    """Dependency factory for data scope filtering.

    Scopes:
    - "tenant": user can see all data in their tenant
    - "department": user can only see data from their department
    - "own": user can only see their own data
    """

    async def _filter(user: dict = Depends(get_current_user)) -> dict:
        """Return user with data scope info for downstream filtering."""
        user["_data_scope"] = scope
        if scope == "department" and not user.get("department_id"):
            # Admin without department sees all tenant data
            user["_data_scope"] = "tenant"
        return user

    return _filter


def apply_data_scope(stmt, model, user: dict):
    """Apply data scope filtering to a SQLAlchemy select statement.

    Args:
        stmt: SQLAlchemy select statement
        model: The ORM model class
        user: User dict with _data_scope, tenant_id, department_id, id
    """
    from sqlalchemy import and_

    scope = user.get("_data_scope", "tenant")
    tenant_id = user["tenant_id"]

    # Always filter by tenant
    conditions = [model.tenant_id == tenant_id]

    if scope == "department" and user.get("department_id"):
        if hasattr(model, "department_id"):
            conditions.append(model.department_id == user["department_id"])
    elif scope == "own" and user.get("id"):
        if hasattr(model, "user_id"):
            conditions.append(model.user_id == user["id"])

    return stmt.where(and_(*conditions))

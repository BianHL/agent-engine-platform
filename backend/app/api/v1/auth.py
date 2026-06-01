import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, revoke_token
from app.core.database import get_db
from app.core.rbac import require_permission
from app.core.security import create_access_token, verify_password
from app.models.base import OAuthProviderModel, UserModel
from app.models.tenant import TenantModel
from app.schemas.api import (
    LoginRequest,
    SSOProviderRequest,
    SSOProviderResponse,
    TokenResponse,
    UserResponse,
)
from app.schemas.auth import LogoutResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# FW-C01: IP-based login rate limiter (in-memory fallback)
# ---------------------------------------------------------------------------

class _LoginRateLimiter:
    """Simple sliding-window rate limiter keyed by client IP.

    Limits to *max_attempts* login requests per *window_seconds* per IP.
    Falls back to an in-memory dict when Redis is unavailable.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # {ip: [timestamp, ...]}
        self._store: dict[str, list[float]] = defaultdict(list)

    async def is_allowed(self, ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        # Try Redis-backed rate limiting first
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            key = f"login_rate_limit:{ip}"
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, cutoff)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()
            return results[2] <= self.max_attempts
        except Exception:
            pass  # fall through to in-memory

        # In-memory fallback
        timestamps = self._store[ip]
        self._store[ip] = [t for t in timestamps if t > cutoff]
        self._store[ip].append(now)
        return len(self._store[ip]) <= self.max_attempts


_login_limiter = _LoginRateLimiter(max_attempts=5, window_seconds=60)


async def login_rate_limit_dependency(request: Request) -> None:
    """Dependency: reject if IP exceeded 5 login attempts per minute."""
    client_ip = request.client.host if request.client else "unknown"
    allowed = await _login_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait and try again later.",
            headers={"Retry-After": "60"},
        )


@router.post("/login", dependencies=[Depends(login_rate_limit_dependency)])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    stmt = select(UserModel).where(UserModel.username == req.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Fetch current token version for the user to embed in JWT
    from app.core.auth import get_user_token_version
    token_version = await get_user_token_version(user.id)

    token = create_access_token(
        {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role, "tv": token_version}
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Logout the current user by adding their token to the blacklist.

    The token is extracted from the Authorization header and its JTI is added
    to the Redis blacklist with the same TTL as the token's expiration.
    """
    from datetime import UTC, datetime
    from jose import JWTError, jwt

    from app.config import settings
    from app.core.security import decode_token

    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Authorization header",
        )

    token_str = auth_header[7:]  # Remove "Bearer " prefix

    try:
        payload = decode_token(token_str)
        token_jti = payload.get("jti")

        if token_jti:
            # Calculate remaining TTL from token expiration
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.now(UTC).timestamp())
                if ttl > 0:
                    await revoke_token(token_jti, ttl=ttl)
                else:
                    # Token already expired, but add to blacklist anyway
                    await revoke_token(token_jti, ttl=60)

        return LogoutResponse(
            message="Successfully logged out",
            revoked_at=datetime.now(UTC).isoformat(),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


@router.post("/logout-all")
async def logout_all(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Revoke all tokens for the current user.

    This invalidates all existing JWTs for the user by incrementing their
    token version counter in Redis. New tokens will include the new version.
    """
    from app.core.auth import revoke_all_user_tokens

    from datetime import UTC, datetime

    new_version = await revoke_all_user_tokens(user["id"])

    return LogoutResponse(
        message=f"Revoked all tokens (version {new_version})",
        revoked_at=datetime.now(UTC).isoformat(),
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return user


# ---------------------------------------------------------------------------
# SSO Provider Configuration
# ---------------------------------------------------------------------------

@router.get("/sso/providers")
async def list_sso_providers(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List configured SSO providers for the current tenant."""
    stmt = (
        select(OAuthProviderModel)
        .where(OAuthProviderModel.tenant_id == user["tenant_id"])
        .order_by(OAuthProviderModel.created_at)
    )
    result = await db.execute(stmt)
    providers = result.scalars().all()

    return [
        {
            "id": p.id,
            "provider_name": p.provider_name,
            "config": p.config or {},
            "enabled": p.enabled,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in providers
    ]


@router.post("/sso/providers", status_code=status.HTTP_201_CREATED)
async def create_sso_provider(
    body: SSOProviderRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("tenant", "manage_features")),
):
    """Create an SSO provider configuration."""
    provider = OAuthProviderModel(
        tenant_id=user["tenant_id"],
        provider_name=body.provider_name,
        config=body.config,
        enabled=body.enabled,
    )
    db.add(provider)
    await db.flush()

    return {
        "id": provider.id,
        "provider_name": provider.provider_name,
        "config": provider.config or {},
        "enabled": provider.enabled,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
        "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
    }


@router.delete("/sso/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sso_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("tenant", "manage_features")),
):
    """Delete an SSO provider configuration."""
    stmt = select(OAuthProviderModel).where(
        OAuthProviderModel.id == provider_id,
        OAuthProviderModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="SSO provider not found")

    await db.delete(provider)
    await db.flush()
    return None


# ---------------------------------------------------------------------------
# WeCom (企业微信) OAuth2 Login
# ---------------------------------------------------------------------------

@router.get("/wecom/login")
async def wecom_login_url():
    """获取企业微信OAuth2登录URL."""
    from app.core.wecom_auth import WeComAuth
    try:
        url = WeComAuth.get_login_url()
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wecom/callback")
async def wecom_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """企业微信OAuth2回调 - 自动登录."""
    from app.core.wecom_auth import WeComAuth

    try:
        user_info = await WeComAuth.get_user_info(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"WeCom auth failed: {e}")

    userid = user_info.get("UserId")
    if not userid:
        raise HTTPException(status_code=400, detail="Invalid WeCom response")

    # Find or create local user
    stmt = select(UserModel).where(UserModel.username == userid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Get user detail from WeCom
        try:
            detail = await WeComAuth.get_user_detail(userid)
        except Exception:
            detail = {}

        # Find first available tenant
        tenant_stmt = select(TenantModel).limit(1)
        tenant_result = await db.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(status_code=500, detail="No tenant available")

        user = UserModel(
            username=userid,
            email=detail.get("email", ""),
            hashed_password="",
            role="Viewer",
            tenant_id=tenant.id,
            department_id=None,
            status="active",
        )
        db.add(user)
        await db.flush()

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Generate JWT
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id})
    return {"access_token": token, "token_type": "bearer"}

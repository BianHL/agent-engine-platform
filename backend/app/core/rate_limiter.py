"""Application-level rate limiter using Redis."""
import time
from typing import Optional

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Sliding window rate limiter backed by Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Return True if request is allowed, False if rate limited (RPM)."""
        if not self.redis:
            return True

        now = time.time()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        request_count = results[2]
        return request_count <= max_requests

    async def check_tokens(self, key: str, token_count: int, max_tokens: int, window_seconds: int) -> bool:
        """Check TPM (tokens per minute) limit. Returns True if allowed."""
        if not self.redis:
            return True

        now = time.time()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        # Use score as token count, member as unique ID
        pipe.zadd(key, {f"{now}:{id(token_count)}": token_count})
        # Sum all scores in window = total tokens
        pipe.zrange(key, 0, -1, withscores=True)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        total_tokens = sum(score for _, score in results[2])
        return total_tokens <= max_tokens

    async def record_tokens(self, key: str, token_count: int, window_seconds: int):
        """Record token usage for TPM tracking."""
        if not self.redis:
            return
        now = time.time()
        pipe = self.redis.pipeline()
        pipe.zadd(key, {f"{now}:{id(token_count)}": token_count})
        pipe.expire(key, window_seconds)
        await pipe.execute()


_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter


def set_rate_limiter_redis(redis_client):
    global _limiter
    _limiter = RateLimiter(redis_client)


async def rate_limit_dependency(request: Request):
    """FastAPI dependency: 100 requests per minute per tenant.

    FW-H05: reads tenant_id from request.state (set by auth middleware)
    instead of redundantly decoding the JWT a second time.
    Falls back to ``"global"`` for unauthenticated or anonymous requests.
    """
    limiter = get_rate_limiter()
    tenant_id = getattr(request.state, "tenant_id", None) or "global"

    key = f"rate_limit:{tenant_id}"
    allowed = await limiter.check(key, max_requests=100, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

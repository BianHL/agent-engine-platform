"""Unit tests for Rate Limiter"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.rate_limiter import RateLimiter


def _make_mock_redis(count: int):
    """Create a mock Redis with pipeline returning the given count."""
    pipeline = MagicMock()
    pipeline.zremrangebyscore = MagicMock()
    pipeline.zadd = MagicMock()
    pipeline.zcard = MagicMock()
    pipeline.expire = MagicMock()
    pipeline.execute = AsyncMock(return_value=[0, True, count, True])
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = pipeline
    return mock_redis


@pytest.mark.asyncio
async def test_rate_limiter_no_redis():
    """Without Redis, all requests are allowed."""
    limiter = RateLimiter(redis_client=None)
    assert await limiter.check("key", 10, 60) is True


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """Requests within limit should be allowed."""
    limiter = RateLimiter(redis_client=_make_mock_redis(5))
    assert await limiter.check("key", 10, 60) is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    """Requests over limit should be blocked."""
    limiter = RateLimiter(redis_client=_make_mock_redis(101))
    assert await limiter.check("key", 100, 60) is False


@pytest.mark.asyncio
async def test_rate_limiter_exactly_at_limit():
    """Exactly at limit should still be allowed."""
    limiter = RateLimiter(redis_client=_make_mock_redis(10))
    assert await limiter.check("key", 10, 60) is True


def _make_mock_redis_for_tpm(total_tokens: int):
    """Create mock Redis for TPM testing."""
    pipeline = MagicMock()
    pipeline.zremrangebyscore = MagicMock()
    pipeline.zadd = MagicMock()
    pipeline.zrange = MagicMock(return_value=[(f"t{i}", 100) for i in range(total_tokens // 100)])
    pipeline.expire = MagicMock()
    pipeline.execute = AsyncMock(return_value=[
        0, True,
        [(f"t{i}", 100) for i in range(total_tokens // 100)],
        True,
    ])
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = pipeline
    return mock_redis


@pytest.mark.asyncio
async def test_tpm_no_redis():
    """Without Redis, token checks pass."""
    limiter = RateLimiter(redis_client=None)
    assert await limiter.check_tokens("key", 1000, 10000, 60) is True


@pytest.mark.asyncio
async def test_tpm_within_limit():
    """Token usage within TPM limit."""
    limiter = RateLimiter(redis_client=_make_mock_redis_for_tpm(5000))
    assert await limiter.check_tokens("key", 1000, 10000, 60) is True


@pytest.mark.asyncio
async def test_tpm_over_limit():
    """Token usage over TPM limit."""
    limiter = RateLimiter(redis_client=_make_mock_redis_for_tpm(15000))
    assert await limiter.check_tokens("key", 1000, 10000, 60) is False


@pytest.mark.asyncio
async def test_record_tokens_no_redis():
    """Recording tokens without Redis is a no-op."""
    limiter = RateLimiter(redis_client=None)
    await limiter.record_tokens("key", 1000, 60)  # Should not raise

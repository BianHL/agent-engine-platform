"""Tests for VectorSemanticCache."""
import asyncio
import time
from unittest.mock import AsyncMock

import numpy as np
import pytest

from app.engines.model_engine.cache import SemanticCache, VectorSemanticCache


@pytest.fixture
def mock_embedder():
    """Create a deterministic mock embedder."""
    async def embed(text: str) -> list[float]:
        vectors = {
            "what is python": [1.0, 0.0, 0.0],
            "what is python programming": [0.95, 0.3, 0.0],
            "tell me about snakes": [0.0, 0.0, 1.0],
            "how do i cook pasta": [0.0, 1.0, 0.0],
        }
        return vectors.get(text, [0.5, 0.5, 0.5])
    return embed


@pytest.fixture
def cache(mock_embedder):
    c = VectorSemanticCache(threshold=0.92, ttl=3600)
    c.set_embedder(mock_embedder)
    return c


@pytest.mark.unit
class TestVectorSemanticCache:
    @pytest.mark.asyncio
    async def test_similarity_match(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Python is a language"}}]}

        await cache.set(messages, response)
        result = await cache.get([{"role": "user", "content": "what is python programming"}])
        assert result == response

    @pytest.mark.asyncio
    async def test_exact_match(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Python is a language"}}]}

        await cache.set(messages, response)
        result = await cache.get([{"role": "user", "content": "what is python"}])
        assert result == response

    @pytest.mark.asyncio
    async def test_threshold_miss(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Python is a language"}}]}

        await cache.set(messages, response)
        result = await cache.get([{"role": "user", "content": "how do i cook pasta"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_no_match_empty_cache(self, cache):
        result = await cache.get([{"role": "user", "content": "what is python"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, mock_embedder):
        cache = VectorSemanticCache(threshold=0.92, ttl=1)
        cache.set_embedder(mock_embedder)

        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Python is a language"}}]}

        await cache.set(messages, response)
        cache._entries[0]["timestamp"] = time.time() - 2

        result = await cache.get([{"role": "user", "content": "what is python"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response_t1 = {"choices": [{"message": {"content": "Response for tenant 1"}}]}
        response_t2 = {"choices": [{"message": {"content": "Response for tenant 2"}}]}

        await cache.set(messages, response_t1, tenant_id="tenant-1")
        await cache.set(messages, response_t2, tenant_id="tenant-2")

        result_t1 = await cache.get(messages, tenant_id="tenant-1")
        result_t2 = await cache.get(messages, tenant_id="tenant-2")

        assert result_t1 == response_t1
        assert result_t2 == response_t2

    @pytest.mark.asyncio
    async def test_tenant_no_match_wrong_tenant(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Response"}}]}

        await cache.set(messages, response, tenant_id="tenant-1")
        result = await cache.get(messages, tenant_id="tenant-2")
        assert result is None

    @pytest.mark.asyncio
    async def test_eviction(self, mock_embedder):
        cache = VectorSemanticCache(threshold=0.92, ttl=3600)
        cache.set_embedder(mock_embedder)

        for i in range(1001):
            await cache.set(
                [{"role": "user", "content": "what is python"}],
                {"index": i},
            )

        assert len(cache._entries) == 500
        assert cache._entries[0]["response"] == {"index": 501}

    @pytest.mark.asyncio
    async def test_clear_all(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Response"}}]}

        await cache.set(messages, response, tenant_id="t1")
        await cache.set(messages, response, tenant_id="t2")
        assert len(cache._entries) == 2

        await cache.clear()
        assert len(cache._entries) == 0

    @pytest.mark.asyncio
    async def test_clear_by_tenant(self, cache):
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Response"}}]}

        await cache.set(messages, response, tenant_id="t1")
        await cache.set(messages, response, tenant_id="t2")
        assert len(cache._entries) == 2

        await cache.clear(tenant_id="t1")
        assert len(cache._entries) == 1
        assert cache._entries[0]["tenant_id"] == "t2"

    @pytest.mark.asyncio
    async def test_no_embedder_returns_none(self):
        cache = VectorSemanticCache()
        result = await cache.get([{"role": "user", "content": "test"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_no_user_message_returns_none(self, cache):
        result = await cache.get([{"role": "system", "content": "test"}])
        assert result is None

    @pytest.mark.asyncio
    async def test_no_user_message_set_noop(self, cache):
        await cache.set([{"role": "system", "content": "test"}], {"data": 1})
        assert len(cache._entries) == 0

    def test_cosine_sim_identical(self):
        a = np.array([1.0, 0.0, 0.0])
        assert VectorSemanticCache._cosine_sim(a, a) == pytest.approx(1.0)

    def test_cosine_sim_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert VectorSemanticCache._cosine_sim(a, b) == pytest.approx(0.0)

    def test_cosine_sim_zero_vector(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        assert VectorSemanticCache._cosine_sim(a, b) == 0.0

    @pytest.mark.asyncio
    async def test_exact_cache_fallback(self):
        exact = SemanticCache(ttl=3600)
        messages = [{"role": "user", "content": "what is python"}]
        response = {"choices": [{"message": {"content": "Python"}}]}

        await exact.set(messages, response)
        result = await exact.get([{"role": "user", "content": "what is python"}])
        assert result == response

        result = await exact.get([{"role": "user", "content": "what is python programming"}])
        assert result is None

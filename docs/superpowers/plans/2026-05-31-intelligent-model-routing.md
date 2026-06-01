# Intelligent Model Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance ModelRouter with complexity-based routing, semantic caching, and budget control.

**Architecture:** Add three new components (ComplexityEstimator, SemanticCache, BudgetTracker) and wire them into a new `intelligent_route()` method on ModelRouter. SemanticCache uses Redis with in-memory fallback. BudgetTracker is in-memory. ComplexityEstimator uses heuristic scoring on message features.

**Tech Stack:** Python 3.11+, asyncio, hashlib, redis.asyncio (optional), pydantic

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/engines/model_engine/router.py` | Modify | Add TaskComplexity enum, ComplexityEstimator, BudgetTracker, intelligent_route() |
| `backend/app/engines/model_engine/cache.py` | Create | SemanticCache class (Redis + in-memory fallback) |
| `backend/tests/unit/engines/model_engine/test_intelligent_routing.py` | Create | Unit tests for all new components |

---

### Task 1: Add TaskComplexity Enum and ComplexityEstimator to router.py

**Files:**
- Modify: `backend/app/engines/model_engine/router.py`
- Test: `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`:

```python
import pytest
from app.engines.model_engine.router import TaskComplexity, ComplexityEstimator


class TestTaskComplexity:
    def test_enum_values(self):
        assert TaskComplexity.LOW.value == "low"
        assert TaskComplexity.MEDIUM.value == "medium"
        assert TaskComplexity.HIGH.value == "high"


class TestComplexityEstimator:
    def setup_method(self):
        self.estimator = ComplexityEstimator()

    def test_low_complexity_short_message(self):
        messages = [{"role": "user", "content": "你好"}]
        score = self.estimator.estimate_score(messages)
        assert score < 0.3
        assert self.estimator.estimate(messages) == TaskComplexity.LOW

    def test_medium_complexity_with_reasoning_keywords(self):
        messages = [
            {"role": "user", "content": "请分析一下这个方案的优缺点，并比较两种技术路线的差异"}
        ]
        score = self.estimator.estimate_score(messages)
        assert 0.3 <= score <= 0.7
        assert self.estimator.estimate(messages) == TaskComplexity.MEDIUM

    def test_high_complexity_with_code_and_reasoning(self):
        code_content = "请分析以下代码的性能问题：\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```\n请评估为什么这段代码效率低，如何优化？"
        messages = [{"role": "user", "content": code_content}]
        score = self.estimator.estimate_score(messages)
        assert score > 0.7
        assert self.estimator.estimate(messages) == TaskComplexity.HIGH

    def test_multi_turn_conversation(self):
        messages = [
            {"role": "user", "content": "我想学习Python"},
            {"role": "assistant", "content": "好的，Python是一个很好的选择。"},
            {"role": "user", "content": "请比较Python和Java的优缺点，分析在什么场景下应该选择哪种语言"},
        ]
        score = self.estimator.estimate_score(messages)
        assert score > 0.3

    def test_empty_messages(self):
        messages = []
        score = self.estimator.estimate_score(messages)
        assert score < 0.3

    def test_has_code_detection(self):
        messages = [{"role": "user", "content": "请帮我写一个函数\n```\ndef hello():\n    print('hello')\n```"}]
        score = self.estimator.estimate_score(messages)
        assert score > 0.2  # code should add to score
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py -v`
Expected: FAIL with import errors (TaskComplexity, ComplexityEstimator don't exist yet)

- [ ] **Step 3: Write the implementation**

Add to `backend/app/engines/model_engine/router.py` (before the ModelRouter class):

```python
import hashlib
import re
from enum import Enum


class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplexityEstimator:
    """Estimates task complexity from message features."""

    REASONING_KEYWORDS = ["分析", "推理", "比较", "评估", "为什么", "如何", "解释", "论证", "对比", "优化"]
    CODE_PATTERN = re.compile(r"```[\s\S]*?```")

    def estimate_score(self, messages: list[dict]) -> float:
        """Calculate weighted complexity score (0-1)."""
        if not messages:
            return 0.0

        total_length = 0
        has_code = False
        reasoning_keyword_count = 0
        turn_count = len(messages)

        for msg in messages:
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            total_length += len(content)
            if self.CODE_PATTERN.search(content):
                has_code = True
            for kw in self.REASONING_KEYWORDS:
                if kw in content:
                    reasoning_keyword_count += 1

        length_score = min(total_length / 2000.0, 1.0)
        turn_score = min(turn_count / 10.0, 1.0)
        code_score = 1.0 if has_code else 0.0
        reasoning_score = min(reasoning_keyword_count / 3.0, 1.0)

        score = (
            length_score * 0.2
            + turn_score * 0.15
            + code_score * 0.3
            + reasoning_score * 0.35
        )
        return min(score, 1.0)

    def estimate(self, messages: list[dict]) -> TaskComplexity:
        """Return TaskComplexity enum based on estimated score."""
        score = self.estimate_score(messages)
        if score < 0.3:
            return TaskComplexity.LOW
        elif score < 0.7:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.HIGH
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestTaskComplexity tests/unit/engines/model_engine/test_intelligent_routing.py::TestComplexityEstimator -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engines/model_engine/router.py backend/tests/unit/engines/model_engine/test_intelligent_routing.py
git commit -m "feat(model-engine): add TaskComplexity enum and ComplexityEstimator"
```

---

### Task 2: Create SemanticCache

**Files:**
- Create: `backend/app/engines/model_engine/cache.py`
- Test: `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`:

```python
import pytest
import asyncio
from app.engines.model_engine.cache import SemanticCache


class TestSemanticCache:
    def setup_method(self):
        self.cache = SemanticCache()

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        messages = [{"role": "user", "content": "什么是机器学习？"}]
        response = {"model": "gpt-4o", "content": "机器学习是..."}
        await self.cache.set(messages, response)
        result = await self.cache.get(messages)
        assert result is not None
        assert result["model"] == "gpt-4o"
        assert result["content"] == "机器学习是..."

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        messages = [{"role": "user", "content": "不存在的问题"}]
        result = await self.cache.get(messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_different_messages_different_keys(self):
        messages1 = [{"role": "user", "content": "问题A"}]
        messages2 = [{"role": "user", "content": "问题B"}]
        await self.cache.set(messages1, {"model": "gpt-4o", "content": "回答A"})
        result = await self.cache.get(messages2)
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_all(self):
        messages = [{"role": "user", "content": "测试清除"}]
        await self.cache.set(messages, {"model": "gpt-4o", "content": "回答"})
        await self.cache.clear()
        result = await self.cache.get(messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_by_tenant(self):
        messages = [{"role": "user", "content": "租户测试"}]
        await self.cache.set(messages, {"model": "gpt-4o", "content": "回答"}, tenant_id="tenant1")
        await self.cache.clear(tenant_id="tenant1")
        result = await self.cache.get(messages, tenant_id="tenant1")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_messages_returns_none(self):
        result = await self.cache.get([])
        assert result is None

    @pytest.mark.asyncio
    async def test_non_string_content_ignored(self):
        messages = [{"role": "user", "content": None}]
        result = await self.cache.get(messages)
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestSemanticCache -v`
Expected: FAIL with import error (SemanticCache doesn't exist yet)

- [ ] **Step 3: Create cache.py**

Create `backend/app/engines/model_engine/cache.py`:

```python
"""Semantic cache for model routing responses."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SemanticCache:
    """Cache for LLM responses keyed by message content hash.

    Uses Redis if available, falls back to in-memory dict.
    """

    def __init__(self, default_ttl: int = 3600):
        self._default_ttl = default_ttl
        self._memory_cache: dict[str, tuple[dict, float]] = {}
        self._redis = None
        self._redis_attempted = False

    async def _get_redis(self):
        """Lazy-init Redis connection."""
        if self._redis_attempted:
            return self._redis
        self._redis_attempted = True
        try:
            from app.core.redis import get_redis
            self._redis = await get_redis()
            logger.info("SemanticCache: using Redis backend")
        except Exception:
            logger.info("SemanticCache: Redis unavailable, using in-memory cache")
            self._redis = None
        return self._redis

    def _build_key(self, messages: list[dict], tenant_id: str = "") -> Optional[str]:
        """Build cache key from last user message content."""
        if not messages:
            return None
        last_user_msg = ""
        for msg in reversed(messages):
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                last_user_msg = content
                break
        if not last_user_msg:
            return None
        key_raw = f"{tenant_id}:{last_user_msg}"
        return "model_cache:" + hashlib.sha256(key_raw.encode()).hexdigest()

    async def get(self, messages: list[dict], tenant_id: str = "") -> Optional[dict]:
        """Get cached response for messages."""
        key = self._build_key(messages, tenant_id)
        if not key:
            return None

        redis = await self._get_redis()
        if redis:
            try:
                data = await redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        else:
            import time
            entry = self._memory_cache.get(key)
            if entry:
                value, expire_at = entry
                if expire_at > time.time():
                    return value
                del self._memory_cache[key]
        return None

    async def set(
        self,
        messages: list[dict],
        response: dict,
        ttl: int = 0,
        tenant_id: str = "",
    ) -> None:
        """Cache a response for messages."""
        key = self._build_key(messages, tenant_id)
        if not key:
            return
        ttl = ttl or self._default_ttl

        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(key, json.dumps(response, ensure_ascii=False), ex=ttl)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        else:
            import time
            self._memory_cache[key] = (response, time.time() + ttl)

    async def clear(self, tenant_id: str = "") -> None:
        """Clear cache entries. If tenant_id provided, clear only that tenant's entries."""
        redis = await self._get_redis()
        if redis:
            try:
                if tenant_id:
                    pattern = f"model_cache:*"
                    async for key in redis.scan_iter(match=pattern):
                        data = await redis.get(key)
                        if data:
                            try:
                                val = json.loads(data)
                                if val.get("_tenant_id") == tenant_id:
                                    await redis.delete(key)
                            except Exception:
                                pass
                else:
                    pattern = "model_cache:*"
                    async for key in redis.scan_iter(match=pattern):
                        await redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache clear failed: {e}")
        else:
            if tenant_id:
                keys_to_delete = [
                    k for k in self._memory_cache
                    if k.startswith(f"model_cache:")
                ]
                for k in keys_to_delete:
                    del self._memory_cache[k]
            else:
                self._memory_cache.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestSemanticCache -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engines/model_engine/cache.py backend/tests/unit/engines/model_engine/test_intelligent_routing.py
git commit -m "feat(model-engine): add SemanticCache with Redis + in-memory fallback"
```

---

### Task 3: Add BudgetTracker

**Files:**
- Modify: `backend/app/engines/model_engine/router.py`
- Test: `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`:

```python
from app.engines.model_engine.router import BudgetTracker


class TestBudgetTracker:
    def setup_method(self):
        self.tracker = BudgetTracker()

    def test_check_budget_no_usage(self):
        assert self.tracker.check_budget("tenant1") is True

    def test_record_and_check_budget(self):
        self.tracker.record_usage("tenant1", input_tokens=1000, output_tokens=500, cost_usd=0.05)
        assert self.tracker.check_budget("tenant1") is True

    def test_over_budget(self):
        self.tracker._budgets["tenant1"] = 1.0  # $1 budget
        self.tracker.record_usage("tenant1", input_tokens=100000, output_tokens=50000, cost_usd=1.5)
        assert self.tracker.check_budget("tenant1") is False

    def test_get_usage(self):
        self.tracker.record_usage("tenant1", input_tokens=1000, output_tokens=500, cost_usd=0.05)
        self.tracker.record_usage("tenant1", input_tokens=2000, output_tokens=1000, cost_usd=0.10)
        usage = self.tracker.get_usage("tenant1")
        assert usage["token_count"] == 4500  # 1000+500+2000+1000
        assert usage["cost_usd"] == pytest.approx(0.15)

    def test_get_usage_no_records(self):
        usage = self.tracker.get_usage("nonexistent")
        assert usage["token_count"] == 0
        assert usage["cost_usd"] == 0.0

    def test_separate_tenants(self):
        self.tracker.record_usage("tenant1", input_tokens=1000, output_tokens=0, cost_usd=0.01)
        self.tracker.record_usage("tenant2", input_tokens=2000, output_tokens=0, cost_usd=0.02)
        usage1 = self.tracker.get_usage("tenant1")
        usage2 = self.tracker.get_usage("tenant2")
        assert usage1["token_count"] == 1000
        assert usage2["token_count"] == 2000

    def test_custom_budget(self):
        self.tracker.set_budget("tenant1", 50.0)
        self.tracker.record_usage("tenant1", input_tokens=0, output_tokens=0, cost_usd=49.0)
        assert self.tracker.check_budget("tenant1") is True
        self.tracker.record_usage("tenant1", input_tokens=0, output_tokens=0, cost_usd=2.0)
        assert self.tracker.check_budget("tenant1") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestBudgetTracker -v`
Expected: FAIL (BudgetTracker doesn't exist yet)

- [ ] **Step 3: Write the implementation**

Add to `backend/app/engines/model_engine/router.py` (after ComplexityEstimator, before ModelRouter):

```python
class BudgetTracker:
    """Simple in-memory budget tracking per tenant."""

    DEFAULT_MONTHLY_BUDGET = 100.0  # USD

    def __init__(self):
        self._usage: dict[str, dict] = {}  # tenant_id -> {token_count, cost_usd}
        self._budgets: dict[str, float] = {}  # tenant_id -> budget_usd

    def set_budget(self, tenant_id: str, budget_usd: float):
        self._budgets[tenant_id] = budget_usd

    def get_budget(self, tenant_id: str) -> float:
        return self._budgets.get(tenant_id, self.DEFAULT_MONTHLY_BUDGET)

    def check_budget(self, tenant_id: str) -> bool:
        """Return True if tenant is within budget."""
        usage = self._usage.get(tenant_id)
        if not usage:
            return True
        budget = self.get_budget(tenant_id)
        return usage["cost_usd"] < budget

    def record_usage(self, tenant_id: str, input_tokens: int, output_tokens: int, cost_usd: float):
        if tenant_id not in self._usage:
            self._usage[tenant_id] = {"token_count": 0, "cost_usd": 0.0}
        self._usage[tenant_id]["token_count"] += input_tokens + output_tokens
        self._usage[tenant_id]["cost_usd"] += cost_usd

    def get_usage(self, tenant_id: str, period: str = "monthly") -> dict:
        """Get usage stats for a tenant."""
        usage = self._usage.get(tenant_id)
        if not usage:
            return {"token_count": 0, "cost_usd": 0.0}
        return dict(usage)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestBudgetTracker -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engines/model_engine/router.py backend/tests/unit/engines/model_engine/test_intelligent_routing.py
git commit -m "feat(model-engine): add BudgetTracker for tenant cost control"
```

---

### Task 4: Add intelligent_route() to ModelRouter

**Files:**
- Modify: `backend/app/engines/model_engine/router.py`
- Test: `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.engines.model_engine.router import ModelRouter, TaskComplexity
from app.schemas.common import ProviderEndpoint


class TestIntelligentRoute:
    def setup_method(self):
        self.router = ModelRouter()
        # Register endpoints for different model tiers
        self.router.register_endpoint("gpt-3.5-turbo", ProviderEndpoint(
            provider_id="openai", model_name="gpt-3.5-turbo", healthy=True
        ))
        self.router.register_endpoint("gpt-4o-mini", ProviderEndpoint(
            provider_id="openai", model_name="gpt-4o-mini", healthy=True
        ))
        self.router.register_endpoint("gpt-4o", ProviderEndpoint(
            provider_id="openai", model_name="gpt-4o", healthy=True
        ))

    @pytest.mark.asyncio
    async def test_model_hint_skips_routing(self):
        endpoint, model = await self.router.intelligent_route(
            messages=[{"role": "user", "content": "hello"}],
            model_hint="claude-sonnet-4-20250514"
        )
        assert model == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_low_complexity_selects_cheap_model(self):
        endpoint, model = await self.router.intelligent_route(
            messages=[{"role": "user", "content": "你好"}]
        )
        assert model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_high_complexity_selects_powerful_model(self):
        messages = [{"role": "user", "content": "请分析以下代码的性能瓶颈并评估优化方案：\n```python\nfor i in range(1000000):\n    pass\n```\n为什么这段代码效率低？如何优化？"}]
        endpoint, model = await self.router.intelligent_route(messages=messages)
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_budget_overrides_to_cheap_model(self):
        self.router._budget_tracker._budgets["tenant1"] = 0.01
        self.router._budget_tracker.record_usage("tenant1", input_tokens=0, output_tokens=0, cost_usd=0.02)
        messages = [{"role": "user", "content": "请分析推理比较评估为什么如何优化这段代码\n```\nprint('hello')\n```"}]
        endpoint, model = await self.router.intelligent_route(
            messages=messages,
            tenant_id="tenant1"
        )
        assert model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self):
        messages = [{"role": "user", "content": "什么是AI？"}]
        cached = {"model": "gpt-4o", "content": "AI是人工智能"}
        await self.router._cache.set(messages, cached)
        endpoint, model = await self.router.intelligent_route(messages=messages)
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_no_healthy_endpoints_raises(self):
        router = ModelRouter()
        router.register_endpoint("gpt-3.5-turbo", ProviderEndpoint(
            provider_id="openai", model_name="gpt-3.5-turbo", healthy=False
        ))
        with pytest.raises(Exception):
            await router.intelligent_route(
                messages=[{"role": "user", "content": "你好"}]
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py::TestIntelligentRoute -v`
Expected: FAIL (intelligent_route method doesn't exist)

- [ ] **Step 3: Write the implementation**

Add the `intelligent_route()` method to the `ModelRouter` class in `router.py`. Also update `__init__`:

Replace the `__init__` method of ModelRouter:

```python
class ModelRouter:
    COMPLEXITY_MODEL_MAP = {
        TaskComplexity.LOW: "gpt-3.5-turbo",
        TaskComplexity.MEDIUM: "gpt-4o-mini",
        TaskComplexity.HIGH: "gpt-4o",
    }

    def __init__(self):
        self._endpoints: dict[str, list[ProviderEndpoint]] = {}
        self._adapters: dict[str, BaseLLMAdapter] = {}
        self._rr_index: dict[str, int] = {}
        self._rr_lock = asyncio.Lock()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._complexity_estimator = ComplexityEstimator()
        self._cache = SemanticCache()
        self._budget_tracker = BudgetTracker()
```

Add after the `record_failure` method:

```python
    async def intelligent_route(
        self,
        messages: list[dict],
        task_type: str = "chat",
        tenant_id: str = None,
        model_hint: str = "",
    ) -> tuple[ProviderEndpoint, str]:
        """Intelligently route to a model based on complexity, cache, and budget."""
        # 1. If model_hint provided, use it directly
        if model_hint:
            endpoint = await self.select_provider(model_hint)
            return endpoint, model_hint

        # 2. Check semantic cache
        cached = await self._cache.get(messages, tenant_id=tenant_id or "")
        if cached and "model" in cached:
            model_name = cached["model"]
            if model_name in self._endpoints:
                endpoint = await self.select_provider(model_name)
                return endpoint, model_name

        # 3. Estimate complexity
        complexity = self._complexity_estimator.estimate(messages)

        # 4. Check budget - downgrade if over budget
        if tenant_id and not self._budget_tracker.check_budget(tenant_id):
            complexity = TaskComplexity.LOW

        # 5. Select model based on complexity
        model_name = self.COMPLEXITY_MODEL_MAP.get(complexity, "gpt-3.5-turbo")

        # 6. Fallback: if selected model has no endpoints, try cheaper tier
        fallback_order = [TaskComplexity.HIGH, TaskComplexity.MEDIUM, TaskComplexity.LOW]
        for tier in fallback_order:
            candidate = self.COMPLEXITY_MODEL_MAP[tier]
            if candidate in self._endpoints:
                healthy = await self._get_healthy_endpoints(candidate)
                if healthy:
                    model_name = candidate
                    break
        else:
            from app.core.exceptions import AllProvidersUnavailableError
            raise AllProvidersUnavailableError("No healthy endpoints available")

        endpoint = await self.select_provider(model_name)
        return endpoint, model_name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engines/model_engine/router.py backend/tests/unit/engines/model_engine/test_intelligent_routing.py
git commit -m "feat(model-engine): add intelligent_route() with complexity-based routing"
```

---

### Task 5: Final Integration Test and Cleanup

**Files:**
- Modify: `backend/tests/unit/engines/model_engine/test_intelligent_routing.py`

- [ ] **Step 1: Add integration-style test**

Append to test file:

```python
class TestIntelligentRoutingIntegration:
    """End-to-end tests for the intelligent routing pipeline."""

    def setup_method(self):
        self.router = ModelRouter()
        self.router.register_endpoint("gpt-3.5-turbo", ProviderEndpoint(
            provider_id="openai", model_name="gpt-3.5-turbo", healthy=True
        ))
        self.router.register_endpoint("gpt-4o-mini", ProviderEndpoint(
            provider_id="openai", model_name="gpt-4o-mini", healthy=True
        ))
        self.router.register_endpoint("gpt-4o", ProviderEndpoint(
            provider_id="openai", model_name="gpt-4o", healthy=True
        ))

    @pytest.mark.asyncio
    async def test_full_pipeline_low_complexity(self):
        messages = [{"role": "user", "content": "hi"}]
        endpoint, model = await self.router.intelligent_route(messages=messages, tenant_id="t1")
        assert model == "gpt-3.5-turbo"
        assert endpoint.provider_id == "openai"

    @pytest.mark.asyncio
    async def test_full_pipeline_medium_complexity(self):
        messages = [{"role": "user", "content": "请分析一下这两种方案的差异，并比较它们的优缺点"}]
        endpoint, model = await self.router.intelligent_route(messages=messages, tenant_id="t1")
        assert model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_full_pipeline_high_complexity(self):
        messages = [{"role": "user", "content": "请分析以下代码为什么效率低，评估各种优化方案，推理出最优解：\n```python\ndef fib(n): return fib(n-1)+fib(n-2) if n>1 else n\n```"}]
        endpoint, model = await self.router.intelligent_route(messages=messages, tenant_id="t1")
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_full_pipeline_budget_downgrade(self):
        # Set very low budget
        self.router._budget_tracker.set_budget("poor_tenant", 0.001)
        self.router._budget_tracker.record_usage("poor_tenant", 0, 0, 0.01)
        # High complexity request should be downgraded
        messages = [{"role": "user", "content": "请分析推理评估为什么如何优化\n```\ncode\n```"}]
        endpoint, model = await self.router.intelligent_route(messages=messages, tenant_id="poor_tenant")
        assert model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_full_pipeline_cache_roundtrip(self):
        messages = [{"role": "user", "content": "缓存测试问题"}]
        # First call - no cache
        _, model1 = await self.router.intelligent_route(messages=messages, tenant_id="t1")
        # Manually set cache
        await self.router._cache.set(messages, {"model": "gpt-4o", "content": "cached"}, tenant_id="t1")
        # Second call should hit cache
        _, model2 = await self.router.intelligent_route(messages=messages, tenant_id="t1")
        assert model2 == "gpt-4o"
```

- [ ] **Step 2: Run all tests**

Run: `cd backend && python -m pytest tests/unit/engines/model_engine/test_intelligent_routing.py -v`
Expected: ALL PASS

- [ ] **Step 3: Verify no existing tests broken**

Run: `cd backend && python -m pytest tests/ -v --timeout=30 2>&1 | head -50`
Expected: No regressions

- [ ] **Step 4: Final commit**

```bash
git add backend/tests/unit/engines/model_engine/test_intelligent_routing.py
git commit -m "test(model-engine): add integration tests for intelligent routing"
```

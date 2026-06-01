import pytest
from app.engines.model_engine.router import (
    ModelRouter, TaskComplexity, ComplexityEstimator, BudgetTracker, CircuitBreaker,
)
from app.engines.model_engine.cache import SemanticCache
from app.schemas.common import ProviderEndpoint


@pytest.fixture
def estimator():
    return ComplexityEstimator()


@pytest.fixture
def cache():
    return SemanticCache(ttl=3600)


@pytest.fixture
def budget():
    return BudgetTracker(monthly_limit_usd=10.0)


@pytest.fixture
def router():
    r = ModelRouter()
    for model in ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini", "deepseek-chat", "claude-sonnet-4-20250514"]:
        ep = ProviderEndpoint(
            provider_id="test", model_name=model, weight=1, healthy=True,
        )
        r.register_endpoint(model, ep)
    return r


class TestComplexityEstimator:
    @pytest.mark.asyncio
    async def test_low_complexity(self, estimator):
        msgs = [{"role": "user", "content": "hello"}]
        assert await estimator.estimate(msgs) == TaskComplexity.LOW

    @pytest.mark.asyncio
    async def test_medium_complexity(self, estimator):
        msgs = [{"role": "user", "content": "请分析这段代码"}] * 4
        c = await estimator.estimate(msgs)
        assert c in (TaskComplexity.LOW, TaskComplexity.MEDIUM)

    @pytest.mark.asyncio
    async def test_high_complexity_code(self, estimator):
        msgs = [
            {"role": "user", "content": "请分析这段代码的性能问题\n```python\nprint(1)\n```"},
            {"role": "assistant", "content": "分析结果..."},
        ] * 3
        c = await estimator.estimate(msgs)
        assert c in (TaskComplexity.MEDIUM, TaskComplexity.HIGH)


class TestSemanticCache:
    @pytest.mark.asyncio
    async def test_set_get(self, cache):
        msgs = [{"role": "user", "content": "hello"}]
        resp = {"model": "gpt-4o", "content": "hi"}
        await cache.set(msgs, resp)
        assert await cache.get(msgs) == resp

    @pytest.mark.asyncio
    async def test_miss(self, cache):
        assert await cache.get([{"role": "user", "content": "nope"}]) is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set([{"role": "user", "content": "x"}], {"model": "m"})
        await cache.clear()
        assert await cache.get([{"role": "user", "content": "x"}]) is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, cache):
        msgs = [{"role": "user", "content": "hello"}]
        await cache.set(msgs, {"model": "m"}, tenant_id="t1")
        assert await cache.get(msgs, tenant_id="t2") is None
        assert await cache.get(msgs, tenant_id="t1") == {"model": "m"}


class TestBudgetTracker:
    @pytest.mark.asyncio
    async def test_under_budget(self, budget):
        assert await budget.check_budget("t1") is True

    @pytest.mark.asyncio
    async def test_over_budget(self, budget):
        await budget.record_cost("t1", 15.0)
        assert await budget.check_budget("t1") is False

    @pytest.mark.asyncio
    async def test_get_usage(self, budget):
        await budget.record_cost("t1", 5.0)
        u = await budget.get_usage("t1")
        assert u["cost_usd"] == 5.0


class TestIntelligentRoute:
    @pytest.mark.asyncio
    async def test_with_hint(self, router):
        ep, model = await router.intelligent_route(
            messages=[{"role": "user", "content": "hi"}],
            model_hint="gpt-4o",
        )
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_low_complexity(self, router):
        ep, model = await router.intelligent_route(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert model in ("gpt-3.5-turbo", "deepseek-chat")

    @pytest.mark.asyncio
    async def test_cache_hit(self, router, cache):
        msgs = [{"role": "user", "content": "cached query"}]
        await cache.set(msgs, {"model": "gpt-4o"})
        ep, model = await router.intelligent_route(messages=msgs, cache=cache)
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_budget_downgrade(self, router, budget):
        await budget.record_cost("t1", 15.0)
        ep, model = await router.intelligent_route(
            messages=[{"role": "user", "content": "分析代码\n```python\nx=1\n```"}] * 5,
            tenant_id="t1",
            budget_tracker=budget,
        )
        assert model in ("gpt-3.5-turbo", "deepseek-chat")

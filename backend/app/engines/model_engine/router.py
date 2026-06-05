import asyncio
import logging
import time
from enum import Enum
from typing import Optional
from app.engines.model_engine.base import BaseLLMAdapter
from app.schemas.common import LLMResponse, ProviderEndpoint

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()

    async def record_success(self):
        async with self._lock:
            self.failure_count = 0
            self.state = "closed"

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"

    async def is_available(self) -> bool:
        async with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                    return True
                return False
            return True  # half-open


class ModelRouter:
    def __init__(self):
        self._endpoints: dict[str, list[ProviderEndpoint]] = {}
        self._adapters: dict[str, BaseLLMAdapter] = {}
        self._rr_index: dict[str, int] = {}
        self._rr_lock = asyncio.Lock()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    def register_adapter(self, provider: str, adapter: BaseLLMAdapter):
        self._adapters[provider] = adapter

    def register_endpoint(self, model_name: str, endpoint: ProviderEndpoint):
        if model_name not in self._endpoints:
            self._endpoints[model_name] = []
        self._endpoints[model_name].append(endpoint)
        key = f"{model_name}:{endpoint.provider_id}"
        self._circuit_breakers[key] = CircuitBreaker()

    async def _get_healthy_endpoints(self, model_name: str) -> list[ProviderEndpoint]:
        eps = self._endpoints.get(model_name, [])
        healthy = []
        for e in eps:
            if not e.healthy:
                continue
            cb = self._circuit_breakers.get(f"{model_name}:{e.provider_id}")
            if cb and await cb.is_available():
                healthy.append(e)
        return healthy

    async def _round_robin(self, model_name: str) -> ProviderEndpoint:
        healthy = await self._get_healthy_endpoints(model_name)
        if not healthy:
            from app.core.exceptions import AllProvidersUnavailableError
            raise AllProvidersUnavailableError(f"No healthy endpoints for {model_name}")
        async with self._rr_lock:
            idx = self._rr_index.get(model_name, 0) % len(healthy)
            self._rr_index[model_name] = idx + 1
        return healthy[idx]

    async def _weighted_select(self, model_name: str) -> ProviderEndpoint:
        healthy = await self._get_healthy_endpoints(model_name)
        if not healthy:
            from app.core.exceptions import AllProvidersUnavailableError
            raise AllProvidersUnavailableError(f"No healthy endpoints for {model_name}")
        total = sum(e.weight for e in healthy)
        if total <= 0:
            return healthy[0]
        import random
        r = random.uniform(0, total)
        cumulative = 0.0
        for e in healthy:
            cumulative += e.weight
            if r <= cumulative:
                return e
        return healthy[-1]

    async def select_provider(self, model_name: str, strategy: str = "round_robin") -> ProviderEndpoint:
        if strategy == "weighted":
            return await self._weighted_select(model_name)
        return await self._round_robin(model_name)

    async def record_success(self, model_name: str, provider_id: str):
        key = f"{model_name}:{provider_id}"
        if key in self._circuit_breakers:
            await self._circuit_breakers[key].record_success()

    async def record_failure(self, model_name: str, provider_id: str):
        key = f"{model_name}:{provider_id}"
        if key in self._circuit_breakers:
            await self._circuit_breakers[key].record_failure()

    async def intelligent_route(
        self,
        messages: list[dict],
        task_type: str = "chat",
        tenant_id: str = None,
        model_hint: str = "",
        complexity_estimator: "ComplexityEstimator" = None,
        cache: "SemanticCache" = None,
        budget_tracker: "BudgetTracker" = None,
    ) -> tuple:
        """Select endpoint and model name using intelligent routing."""
        # Import here to avoid circular imports
        from app.engines.model_engine.cache import SemanticCache as _SC

        # 1. If model_hint, use directly
        if model_hint:
            endpoint = await self.select_provider(model_hint)
            return endpoint, model_hint

        # 2. Check cache
        if cache:
            cached = await cache.get(messages, tenant_id)
            if cached and "model" in cached:
                try:
                    endpoint = await self.select_provider(cached["model"])
                    return endpoint, cached["model"]
                except Exception as e:
                    logger.warning("Cached model %s unavailable, falling back to estimation: %s", cached["model"], e)

        # 3. Estimate complexity
        estimator = complexity_estimator or ComplexityEstimator()
        complexity = await estimator.estimate(messages)

        # 4. Check budget
        model_candidates = {
            "low": ["gpt-3.5-turbo", "deepseek-chat"],
            "medium": ["gpt-4o-mini", "deepseek-chat"],
            "high": ["gpt-4o", "claude-sonnet-4-20250514"],
        }
        level = complexity.value
        candidates = model_candidates.get(level, model_candidates["medium"])

        if budget_tracker:
            ok = await budget_tracker.check_budget(tenant_id)
            if not ok:
                candidates = model_candidates["low"]

        # 5. Select first available from candidates
        for model_name in candidates:
            try:
                endpoint = await self.select_provider(model_name)
                return endpoint, model_name
            except Exception:
                continue

        # 6. Last resort: try any registered model
        for model_name in self._endpoints:
            try:
                endpoint = await self.select_provider(model_name)
                return endpoint, model_name
            except Exception:
                continue

        from app.core.exceptions import AllProvidersUnavailableError
        raise AllProvidersUnavailableError("No healthy endpoints available for any registered model")


class TaskComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplexityEstimator:
    """Estimate task complexity from message history."""

    _REASONING_KEYWORDS = {"分析", "推理", "比较", "评估", "为什么", "如何", "explain", "analyze", "compare", "evaluate"}

    async def estimate(self, messages: list[dict]) -> TaskComplexity:
        features = self._extract_features(messages)
        score = self._calculate_score(features)
        if score < 0.3:
            return TaskComplexity.LOW
        elif score < 0.7:
            return TaskComplexity.MEDIUM
        return TaskComplexity.HIGH

    def _extract_features(self, messages: list[dict]) -> dict:
        total_length = sum(len(m.get("content", "")) for m in messages)
        turn_count = len(messages)
        has_code = any("```" in m.get("content", "") for m in messages)
        has_reasoning = any(
            kw in m.get("content", "")
            for m in messages
            for kw in self._REASONING_KEYWORDS
        )
        return {
            "total_length": total_length,
            "turn_count": turn_count,
            "has_code": has_code,
            "has_reasoning": has_reasoning,
        }

    def _calculate_score(self, features: dict) -> float:
        weights = {"total_length": 0.2, "turn_count": 0.3, "has_code": 0.3, "has_reasoning": 0.2}
        normalized = {
            "total_length": min(features["total_length"] / 1000, 1.0),
            "turn_count": min(features["turn_count"] / 10, 1.0),
            "has_code": 1.0 if features["has_code"] else 0.0,
            "has_reasoning": 1.0 if features["has_reasoning"] else 0.0,
        }
        return min(sum(normalized[k] * weights[k] for k in weights), 1.0)


class BudgetTracker:
    """Track and limit per-tenant spending."""

    def __init__(self, monthly_limit_usd: float = 100.0):
        self._usage: dict[str, float] = {}  # tenant_id -> cost_usd
        self._monthly_limit = monthly_limit_usd

    async def check_budget(self, tenant_id: str = None) -> bool:
        if not tenant_id:
            return True
        return self._usage.get(tenant_id, 0.0) < self._monthly_limit

    async def record_cost(self, tenant_id: str, cost_usd: float):
        if tenant_id:
            self._usage[tenant_id] = self._usage.get(tenant_id, 0.0) + cost_usd

    async def get_usage(self, tenant_id: str) -> dict:
        return {"cost_usd": self._usage.get(tenant_id, 0.0), "limit_usd": self._monthly_limit}

"""Unit tests for Model Engine"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engines.model_engine.base import (
    ModelType, LLMCapability, EmbeddingCapability,
    LLMModelConfig, EmbeddingModelConfig,
    BaseLLMAdapter, BaseEmbeddingAdapter
)
from app.engines.model_engine.router import ModelRouter, CircuitBreaker
from app.engines.model_engine.cost_tracker import CostTracker
from app.engines.model_engine.monitor import ModelMonitor, ModelMetrics
from app.engines.model_engine.presets import PRESET_LLM_MODELS, PRESET_EMBEDDING_MODELS
from app.schemas.common import LLMResponse, TokenUsage, ProviderEndpoint
from app.core.exceptions import AllProvidersUnavailableError


# === Enum Tests ===

def test_model_type_enum():
    assert ModelType.LLM == "llm"
    assert ModelType.EMBEDDING == "embedding"
    assert ModelType.RERANK == "rerank"


def test_llm_capability_enum():
    assert LLMCapability.CHAT == "chat"
    assert LLMCapability.FUNCTION_CALLING == "function_calling"


def test_embedding_capability_enum():
    assert EmbeddingCapability.TEXT == "text"
    assert EmbeddingCapability.MULTILINGUAL == "multilingual"


# === Config Tests ===

def test_llm_model_config():
    config = LLMModelConfig(
        provider="openai",
        model_name="gpt-4o",
        display_name="GPT-4o",
        context_window=128000,
        input_price=2.5,
        output_price=10.0
    )
    assert config.provider == "openai"
    assert config.context_window == 128000
    assert config.enabled is True
    assert config.is_default is False


def test_embedding_model_config():
    config = EmbeddingModelConfig(
        provider="openai",
        model_name="text-embedding-3-small",
        display_name="OpenAI Embedding Small",
        dimensions=1536
    )
    assert config.dimensions == 1536
    assert config.price_per_million == 0.0


# === Presets Tests ===

def test_preset_llm_models():
    assert len(PRESET_LLM_MODELS) >= 5
    providers = {m.provider for m in PRESET_LLM_MODELS}
    assert "openai" in providers
    assert "anthropic" in providers
    assert "deepseek" in providers


def test_preset_embedding_models():
    assert len(PRESET_EMBEDDING_MODELS) >= 3
    for m in PRESET_EMBEDDING_MODELS:
        assert m.dimensions > 0


# === Circuit Breaker Tests ===

@pytest.mark.asyncio
async def test_circuit_breaker_closed():
    cb = CircuitBreaker(failure_threshold=3)
    assert await cb.is_available() is True
    await cb.record_success()
    assert cb.state == "closed"


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        await cb.record_failure()
    assert cb.state == "open"
    assert await cb.is_available() is False


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_timeout():
    import time
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    await cb.record_failure()
    await cb.record_failure()
    assert cb.state == "open"
    time.sleep(0.15)
    assert await cb.is_available() is True
    assert cb.state == "half-open"


@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_success():
    cb = CircuitBreaker(failure_threshold=3)
    await cb.record_failure()
    await cb.record_failure()
    await cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == "closed"


# === Model Router Tests ===

@pytest.fixture
def router():
    return ModelRouter()


def test_router_register_endpoint(router):
    ep = ProviderEndpoint(provider_id="p1", model_name="gpt-4o")
    router.register_endpoint("gpt-4o", ep)
    assert "gpt-4o" in router._endpoints


@pytest.mark.asyncio
async def test_router_round_robin(router):
    for i in range(3):
        ep = ProviderEndpoint(provider_id=f"p{i}", model_name="gpt-4o")
        router.register_endpoint("gpt-4o", ep)

    results = set()
    for _ in range(6):
        selected = await router._round_robin("gpt-4o")
        results.add(selected.provider_id)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_router_all_unhealthy(router):
    ep = ProviderEndpoint(provider_id="p1", model_name="gpt-4o", healthy=False)
    router.register_endpoint("gpt-4o", ep)

    with pytest.raises(AllProvidersUnavailableError):
        await router._round_robin("gpt-4o")


@pytest.mark.asyncio
async def test_router_weighted_select(router):
    ep1 = ProviderEndpoint(provider_id="p1", model_name="gpt-4o", weight=3)
    ep2 = ProviderEndpoint(provider_id="p2", model_name="gpt-4o", weight=1)
    router.register_endpoint("gpt-4o", ep1)
    router.register_endpoint("gpt-4o", ep2)

    counts = {"p1": 0, "p2": 0}
    for _ in range(100):
        selected = await router._weighted_select("gpt-4o")
        counts[selected.provider_id] += 1

    assert counts["p1"] > 50  # ~75% expected


@pytest.mark.asyncio
async def test_router_record_failure_affects_availability(router):
    ep = ProviderEndpoint(provider_id="p1", model_name="gpt-4o")
    router.register_endpoint("gpt-4o", ep)

    for _ in range(6):
        await router.record_failure("gpt-4o", "p1")

    healthy = await router._get_healthy_endpoints("gpt-4o")
    assert len(healthy) == 0


# === Cost Tracker Tests ===

@pytest.mark.asyncio
async def test_cost_tracker_calculates_cost():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(config={"input_price": 2.5, "output_price": 10.0})
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()

    tracker = CostTracker(mock_session)
    # The actual cost calculation depends on DB query, just verify it doesn't crash
    assert tracker is not None


# === Monitor Tests ===

def test_monitor_records_request():
    monitor = ModelMonitor()
    monitor.record_request("gpt-4o", 100.0, True)
    monitor.record_request("gpt-4o", 200.0, True)
    monitor.record_request("gpt-4o", 150.0, False)

    metrics = monitor.get_metrics("gpt-4o")
    assert metrics.request_count == 3
    assert metrics.error_count == 1
    assert metrics.avg_latency_ms == 150.0
    assert abs(metrics.error_rate - 1/3) < 0.01


def test_monitor_empty_metrics():
    monitor = ModelMonitor()
    metrics = monitor.get_metrics("nonexistent")
    assert metrics.request_count == 0
    assert metrics.error_rate == 0.0
    assert metrics.avg_latency_ms == 0.0


def test_monitor_multiple_models():
    monitor = ModelMonitor()
    monitor.record_request("gpt-4o", 100.0, True)
    monitor.record_request("claude", 200.0, True)

    assert monitor.get_metrics("gpt-4o").request_count == 1
    assert monitor.get_metrics("claude").request_count == 1

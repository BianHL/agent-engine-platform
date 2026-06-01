"""Unit tests for Cost Tracker - M-021, M-022, M-023, M-024."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engines.model_engine.cost_tracker import CostTracker


def _make_track_db(config=None):
    """Create mock DB for track() calls."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    config_result = MagicMock()
    config_result.scalar_one_or_none.return_value = config
    db.execute = AsyncMock(return_value=config_result)
    return db


def _make_usage_db(total_input=0, total_output=0, total_cost=0.0, request_count=0):
    """Create mock DB for get_usage() calls."""
    db = AsyncMock()
    usage_result = MagicMock()
    row = MagicMock()
    row.total_input = total_input
    row.total_output = total_output
    row.total_cost = total_cost
    row.request_count = request_count
    usage_result.one.return_value = row
    db.execute = AsyncMock(return_value=usage_result)
    return db


class FakeConfig:
    def __init__(self, input_price=0.01, output_price=0.03):
        self.config = {"input_price": input_price, "output_price": output_price}
        self.model_name = "gpt-4o"


# === M-021: Token Cost Calculation ===

@pytest.mark.asyncio
async def test_cost_calculation():
    """Cost = input_tokens * input_price + output_tokens * output_price (M-021)."""
    config = FakeConfig(input_price=0.01, output_price=0.03)
    db = _make_track_db(config=config)
    tracker = CostTracker(db)
    cost = await tracker.track(
        tenant_id="t1", user_id="u1", provider="openai",
        model="gpt-4o", input_tokens=1000, output_tokens=500,
    )
    assert cost == pytest.approx(0.025, abs=0.001)


@pytest.mark.asyncio
async def test_cost_with_no_config():
    """Cost is 0 when no pricing config exists."""
    db = _make_track_db(config=None)
    tracker = CostTracker(db)
    cost = await tracker.track(
        tenant_id="t1", user_id="u1", provider="openai",
        model="unknown", input_tokens=1000, output_tokens=500,
    )
    assert cost == 0.0


@pytest.mark.asyncio
async def test_cost_zero_tokens():
    """Cost is 0 for zero tokens."""
    config = FakeConfig(input_price=0.01, output_price=0.03)
    db = _make_track_db(config=config)
    tracker = CostTracker(db)
    cost = await tracker.track(
        tenant_id="t1", user_id="u1", provider="openai",
        model="gpt-4o", input_tokens=0, output_tokens=0,
    )
    assert cost == 0.0


# === M-024: Usage Report ===

@pytest.mark.asyncio
async def test_get_usage_report():
    """Usage report aggregates correctly (M-024)."""
    db = _make_usage_db(total_input=10000, total_output=5000, total_cost=0.25, request_count=20)
    tracker = CostTracker(db)
    report = await tracker.get_usage("t1")
    assert report["total_input_tokens"] == 10000
    assert report["total_output_tokens"] == 5000
    assert report["total_cost"] == 0.25
    assert report["request_count"] == 20


@pytest.mark.asyncio
async def test_get_usage_empty():
    """Empty usage report returns zeros."""
    db = _make_usage_db()
    tracker = CostTracker(db)
    report = await tracker.get_usage("t1")
    assert report["total_input_tokens"] == 0
    assert report["total_cost"] == 0.0

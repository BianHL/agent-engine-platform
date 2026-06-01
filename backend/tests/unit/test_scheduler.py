"""Unit tests for Scheduler Service."""
import pytest
from datetime import datetime, timezone

from app.core.scheduler import (
    parse_cron_field,
    cron_matches,
    SchedulerService,
)


# ---------------------------------------------------------------------------
# Cron parsing
# ---------------------------------------------------------------------------

def test_parse_cron_field_wildcard():
    result = parse_cron_field("*", 0, 59)
    assert len(result) == 60
    assert 0 in result
    assert 59 in result


def test_parse_cron_field_step():
    result = parse_cron_field("*/5", 0, 59)
    assert result == {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}


def test_parse_cron_field_range():
    result = parse_cron_field("1-5", 0, 59)
    assert result == {1, 2, 3, 4, 5}


def test_parse_cron_field_list():
    result = parse_cron_field("1,3,5", 0, 59)
    assert result == {1, 3, 5}


def test_parse_cron_field_single():
    result = parse_cron_field("30", 0, 59)
    assert result == {30}


def test_parse_cron_field_mixed():
    result = parse_cron_field("1,5-7,*/10", 0, 59)
    assert 1 in result
    assert 5 in result
    assert 6 in result
    assert 7 in result
    assert 0 in result
    assert 10 in result


# ---------------------------------------------------------------------------
# Cron matching
# ---------------------------------------------------------------------------

def test_cron_matches_every_minute():
    dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    assert cron_matches("* * * * *", dt) is True


def test_cron_matches_specific_time():
    dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    assert cron_matches("30 10 * * *", dt) is True
    assert cron_matches("31 10 * * *", dt) is False


def test_cron_matches_step():
    dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    assert cron_matches("*/10 * * * *", dt) is True  # 30 is divisible by 10
    assert cron_matches("*/7 * * * *", dt) is False  # 30 is not divisible by 7


def test_cron_matches_day_of_week():
    # 2025-01-15 is a Wednesday (weekday=2)
    dt = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    assert cron_matches("* * * * 2", dt) is True
    assert cron_matches("* * * * 0", dt) is False  # not Sunday


def test_cron_matches_month():
    dt = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    assert cron_matches("* * * 6 *", dt) is True
    assert cron_matches("* * * 1 *", dt) is False


def test_cron_matches_range():
    dt = datetime(2025, 1, 15, 10, 15, 0, tzinfo=timezone.utc)
    assert cron_matches("10-20 * * * *", dt) is True
    assert cron_matches("0-5 * * * *", dt) is False


def test_cron_matches_invalid_expression():
    with pytest.raises(ValueError, match="Invalid cron expression"):
        cron_matches("* * *")


# ---------------------------------------------------------------------------
# SchedulerService
# ---------------------------------------------------------------------------

def test_scheduler_singleton():
    """SchedulerService is a singleton."""
    s1 = SchedulerService()
    s2 = SchedulerService()
    assert s1 is s2


def test_scheduler_add_cron_trigger():
    scheduler = SchedulerService()
    scheduler._cron_triggers.clear()

    mock_trigger = type("Trigger", (), {
        "id": "t1",
        "workflow_id": "w1",
        "trigger_type": "cron",
        "config": {"cron_expression": "*/5 * * * *"},
    })()

    scheduler.add_cron_trigger(mock_trigger)
    assert "t1" in scheduler._cron_triggers
    assert scheduler._cron_triggers["t1"]["cron_expression"] == "*/5 * * * *"


def test_scheduler_remove_cron_trigger():
    scheduler = SchedulerService()
    scheduler._cron_triggers.clear()

    mock_trigger = type("Trigger", (), {
        "id": "t1",
        "workflow_id": "w1",
        "trigger_type": "cron",
        "config": {"cron_expression": "*/5 * * * *"},
    })()

    scheduler.add_cron_trigger(mock_trigger)
    assert "t1" in scheduler._cron_triggers

    scheduler.remove_cron_trigger("t1")
    assert "t1" not in scheduler._cron_triggers


def test_scheduler_event_trigger():
    scheduler = SchedulerService()
    scheduler._event_triggers.clear()

    mock_trigger = type("Trigger", (), {
        "id": "t2",
        "workflow_id": "w2",
        "trigger_type": "event",
        "config": {"event_type": "user_signup"},
    })()

    scheduler.add_cron_trigger(mock_trigger)
    assert "user_signup" in scheduler._event_triggers
    assert len(scheduler._event_triggers["user_signup"]) == 1


def test_scheduler_remove_also_cleans_event_triggers():
    scheduler = SchedulerService()
    scheduler._event_triggers.clear()
    scheduler._cron_triggers.clear()

    mock_trigger = type("Trigger", (), {
        "id": "t3",
        "workflow_id": "w3",
        "trigger_type": "event",
        "config": {"event_type": "order_created"},
    })()

    scheduler.add_cron_trigger(mock_trigger)
    assert "order_created" in scheduler._event_triggers

    scheduler.remove_cron_trigger("t3")
    assert "order_created" not in scheduler._event_triggers

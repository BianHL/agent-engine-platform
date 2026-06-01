import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.core.alerting import Alert, AlertManager, AlertRule, AlertSeverity


@pytest.fixture
def manager():
    return AlertManager()


@pytest.fixture
def rule():
    return AlertRule(
        name="high_error_rate",
        metric="llm.error_rate",
        condition="> 0.05",
        severity=AlertSeverity.CRITICAL,
        description="LLM error rate exceeds 5%",
    )


@pytest.mark.unit
class TestAlertRule:
    def test_default_cooldown(self):
        rule = AlertRule(
            name="test", metric="m", condition="> 0", severity=AlertSeverity.INFO
        )
        assert rule.cooldown_seconds == 300

    def test_custom_cooldown(self):
        rule = AlertRule(
            name="test", metric="m", condition="> 0", severity=AlertSeverity.INFO, cooldown_seconds=60
        )
        assert rule.cooldown_seconds == 60


@pytest.mark.unit
class TestAlert:
    def test_default_fired_count(self):
        alert = Alert(
            rule_name="test",
            severity=AlertSeverity.INFO,
            metric="m",
            value=1.0,
            threshold="> 0",
            message="msg",
            timestamp=0.0,
        )
        assert alert.fired_count == 0

    def test_custom_fired_count(self):
        alert = Alert(
            rule_name="test",
            severity=AlertSeverity.INFO,
            metric="m",
            value=1.0,
            threshold="> 0",
            message="msg",
            timestamp=0.0,
            fired_count=5,
        )
        assert alert.fired_count == 5


@pytest.mark.unit
class TestAlertManagerCooldown:
    @pytest.mark.asyncio
    async def test_cooldown_prevents_refiring(self, manager, rule):
        rule.cooldown_seconds = 10
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()
        assert handler.call_count == 1

        await manager.check_alerts()
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_cooldown_expires_allows_refiring(self, manager, rule):
        rule.cooldown_seconds = 1
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()
        assert handler.call_count == 1

        manager._last_fired[rule.name] = time.time() - 2
        await manager.check_alerts()
        assert handler.call_count == 2


@pytest.mark.unit
class TestAlertManagerSilence:
    @pytest.mark.asyncio
    async def test_silence_rule(self, manager, rule):
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        manager.silence_rule(rule.name, duration_seconds=60)
        await manager.check_alerts()
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsilence_rule(self, manager, rule):
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        manager.silence_rule(rule.name, duration_seconds=60)
        await manager.check_alerts()
        handler.assert_not_called()

        manager.unsilence_rule(rule.name)
        await manager.check_alerts()
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_silence_expires(self, manager, rule):
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        manager._silenced_until[rule.name] = time.time() - 1
        await manager.check_alerts()
        assert handler.call_count == 1


@pytest.mark.unit
class TestAlertManagerResetCooldown:
    @pytest.mark.asyncio
    async def test_reset_cooldown(self, manager, rule):
        rule.cooldown_seconds = 3600
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()
        assert handler.call_count == 1

        await manager.check_alerts()
        assert handler.call_count == 1

        manager.reset_cooldown(rule.name)
        await manager.check_alerts()
        assert handler.call_count == 2


@pytest.mark.unit
class TestAlertManagerFiredCount:
    @pytest.mark.asyncio
    async def test_fired_count_increments(self, manager, rule):
        rule.cooldown_seconds = 0
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()
        assert handler.call_args_list[0][0][0].fired_count == 1

        await manager.check_alerts()
        assert handler.call_args_list[1][0][0].fired_count == 2

        await manager.check_alerts()
        assert handler.call_args_list[2][0][0].fired_count == 3

    @pytest.mark.asyncio
    async def test_fired_count_on_alert_object(self, manager, rule):
        rule.cooldown_seconds = 0
        manager.add_rule(rule)
        alerts = []

        async def capture_alert(alert):
            alerts.append(alert)

        manager.add_handler(capture_alert)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()
        await manager.check_alerts()
        assert alerts[0].fired_count == 1
        assert alerts[1].fired_count == 2


@pytest.mark.unit
class TestAlertManagerGetRuleStatus:
    def test_get_rule_status_empty(self, manager):
        assert manager.get_rule_status() == []

    def test_get_rule_status(self, manager, rule):
        manager.add_rule(rule)
        status = manager.get_rule_status()
        assert len(status) == 1
        assert status[0]["name"] == rule.name
        assert status[0]["metric"] == rule.metric
        assert status[0]["severity"] == rule.severity.value
        assert status[0]["fired_count"] == 0
        assert status[0]["last_fired"] == 0
        assert status[0]["silenced"] is False
        assert status[0]["silence_remaining"] == 0
        assert status[0]["cooldown_remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_rule_status_after_fire(self, manager, rule):
        rule.cooldown_seconds = 300
        manager.add_rule(rule)
        handler = AsyncMock()
        manager.add_handler(handler)

        manager.update_metric("llm.error_rate", 0.1)
        await manager.check_alerts()

        status = manager.get_rule_status()
        assert status[0]["fired_count"] == 1
        assert status[0]["last_fired"] > 0
        assert status[0]["cooldown_remaining"] > 0

    def test_get_rule_status_silenced(self, manager, rule):
        manager.add_rule(rule)
        manager.silence_rule(rule.name, duration_seconds=60)

        status = manager.get_rule_status()
        assert status[0]["silenced"] is True
        assert status[0]["silence_remaining"] > 0

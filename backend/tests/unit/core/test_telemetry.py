"""Tests for telemetry and alerting modules."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from app.core.telemetry import TelemetryManager, LLMMonitor, init_telemetry, get_telemetry, get_llm_monitor
from app.core.alerting import AlertManager, AlertRule, AlertSeverity, Alert, DEFAULT_RULES


class TestTelemetryManager:
    def test_disabled_mode(self):
        """Test telemetry in disabled mode initializes gracefully."""
        manager = TelemetryManager(enabled=False)
        manager.initialize()
        assert not manager.is_initialized
        assert manager.tracer is None
        assert manager.meter is None

    def test_default_initialization(self):
        """Test default initialization without otel packages."""
        manager = TelemetryManager(enabled=True)
        # Should handle ImportError gracefully
        manager.initialize()
        # May or may not be initialized depending on packages
        assert isinstance(manager.is_initialized, bool)

    def test_global_instances(self):
        """Test global telemetry instance management."""
        tel = get_telemetry()
        assert tel is not None
        monitor = get_llm_monitor()
        assert monitor is not None


class TestLLMMonitor:
    @pytest.fixture
    def disabled_telemetry(self):
        return TelemetryManager(enabled=False)

    @pytest.fixture
    def enabled_telemetry(self):
        tel = TelemetryManager(enabled=True)
        tel.initialize()
        return tel

    @pytest.mark.asyncio
    async def test_track_request_disabled(self, disabled_telemetry):
        """Test tracking request with disabled telemetry."""
        monitor = LLMMonitor(disabled_telemetry)
        # Should not raise
        await monitor.track_request(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            latency_ms=100
        )

    @pytest.mark.asyncio
    async def test_track_request_with_response(self, disabled_telemetry):
        """Test tracking request with response data."""
        monitor = LLMMonitor(disabled_telemetry)
        await monitor.track_request(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            response={"usage": {"total_tokens": 50, "prompt_tokens": 20, "completion_tokens": 30}},
            latency_ms=150,
            tenant_id="tenant-1"
        )

    @pytest.mark.asyncio
    async def test_track_request_with_error(self, disabled_telemetry):
        """Test tracking request with error."""
        monitor = LLMMonitor(disabled_telemetry)
        await monitor.track_request(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            error="Rate limit exceeded"
        )


class TestAlertManager:
    @pytest.fixture
    def alert_manager(self):
        manager = AlertManager()
        for rule in DEFAULT_RULES:
            manager.add_rule(rule)
        return manager

    @pytest.mark.asyncio
    async def test_no_alerts_when_no_violations(self, alert_manager):
        """Test no alerts when metrics are within thresholds."""
        alert_manager.update_metric("llm.error_rate", 0.02)
        alert_manager.update_metric("llm.avg_latency_ms", 2000)
        
        handler = AsyncMock()
        alert_manager.add_handler(handler)
        
        await alert_manager.check_alerts()
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_alert_triggered(self, alert_manager):
        """Test alert is triggered when threshold exceeded."""
        alert_manager.update_metric("llm.error_rate", 0.1)  # > 0.05
        
        handler = AsyncMock()
        alert_manager.add_handler(handler)
        
        await alert_manager.check_alerts()
        handler.assert_called_once()
        alert = handler.call_args[0][0]
        assert alert.rule_name == "high_error_rate"
        assert alert.severity == AlertSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_multiple_alerts(self, alert_manager):
        """Test multiple alerts triggered."""
        alert_manager.update_metric("llm.error_rate", 0.1)
        alert_manager.update_metric("llm.avg_latency_ms", 6000)
        
        handler = AsyncMock()
        alert_manager.add_handler(handler)
        
        await alert_manager.check_alerts()
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_handler(self, alert_manager):
        """Test synchronous alert handler."""
        alert_manager.update_metric("llm.error_rate", 0.1)
        
        handler = MagicMock()
        alert_manager.add_handler(handler)
        
        await alert_manager.check_alerts()
        handler.assert_called_once()

    def test_evaluate_conditions(self, alert_manager):
        """Test condition evaluation."""
        assert alert_manager._evaluate(10, "> 5") is True
        assert alert_manager._evaluate(3, "> 5") is False
        assert alert_manager._evaluate(3, "< 5") is True
        assert alert_manager._evaluate(10, "< 5") is False
        assert alert_manager._evaluate(5, "== 5") is True
        assert alert_manager._evaluate(6, "== 5") is False

    def test_default_rules(self):
        """Test default rules are properly defined."""
        assert len(DEFAULT_RULES) == 3
        assert DEFAULT_RULES[0].name == "high_error_rate"
        assert DEFAULT_RULES[1].name == "high_latency"
        assert DEFAULT_RULES[2].name == "high_cost"


class TestIntegration:
    @pytest.mark.asyncio
    async def test_init_telemetry(self):
        """Test init_telemetry function."""
        tel = init_telemetry(enabled=False)
        assert tel is not None
        assert not tel.is_initialized

"""Alert management for monitoring thresholds."""
import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule(BaseModel):
    name: str
    metric: str
    condition: str  # e.g., "> 0.05", "< 100"
    severity: AlertSeverity
    description: str = ""
    cooldown_seconds: int = 300


class Alert(BaseModel):
    rule_name: str
    severity: AlertSeverity
    metric: str
    value: float
    threshold: str
    message: str
    timestamp: float
    fired_count: int = 0


class AlertManager:
    def __init__(self):
        self._rules: list[AlertRule] = []
        self._handlers: list[Callable] = []
        self._values: dict[str, float] = {}
        self._last_fired: dict[str, float] = {}
        self._silenced_until: dict[str, float] = {}
        self._fired_count: dict[str, int] = {}

    def add_rule(self, rule: AlertRule):
        self._rules.append(rule)

    def add_handler(self, handler: Callable):
        self._handlers.append(handler)

    def update_metric(self, name: str, value: float):
        self._values[name] = value

    async def check_alerts(self):
        now = time.time()
        for rule in self._rules:
            if rule.name in self._silenced_until and now < self._silenced_until[rule.name]:
                continue

            last_fired = self._last_fired.get(rule.name, 0)
            if now - last_fired < rule.cooldown_seconds:
                continue

            value = self._values.get(rule.metric)
            if value is None:
                continue

            if self._evaluate(value, rule.condition):
                self._last_fired[rule.name] = now
                self._fired_count[rule.name] = self._fired_count.get(rule.name, 0) + 1

                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    metric=rule.metric,
                    value=value,
                    threshold=rule.condition,
                    message=f"{rule.description}: {rule.metric}={value} {rule.condition}",
                    timestamp=now,
                    fired_count=self._fired_count[rule.name],
                )
                for handler in self._handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(alert)
                        else:
                            handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")

    def silence_rule(self, rule_name: str, duration_seconds: int = 3600):
        self._silenced_until[rule_name] = time.time() + duration_seconds

    def unsilence_rule(self, rule_name: str):
        self._silenced_until.pop(rule_name, None)

    def reset_cooldown(self, rule_name: str):
        self._last_fired.pop(rule_name, None)

    def get_rule_status(self) -> list[dict]:
        now = time.time()
        result = []
        for rule in self._rules:
            last_fired = self._last_fired.get(rule.name, 0)
            silenced_until = self._silenced_until.get(rule.name, 0)
            result.append({
                "name": rule.name,
                "metric": rule.metric,
                "severity": rule.severity.value,
                "fired_count": self._fired_count.get(rule.name, 0),
                "last_fired": last_fired,
                "cooldown_remaining": max(0, rule.cooldown_seconds - (now - last_fired)),
                "silenced": now < silenced_until,
                "silence_remaining": max(0, silenced_until - now),
            })
        return result

    def _evaluate(self, value: float, condition: str) -> bool:
        condition = condition.strip()
        if condition.startswith(">"):
            return value > float(condition[1:].strip())
        if condition.startswith("<"):
            return value < float(condition[1:].strip())
        if condition.startswith("=="):
            return value == float(condition[2:].strip())
        return False


# Default alert rules
DEFAULT_RULES = [
    AlertRule(name="high_error_rate", metric="llm.error_rate", condition="> 0.05", severity=AlertSeverity.CRITICAL, description="LLM error rate exceeds 5%"),
    AlertRule(name="high_latency", metric="llm.avg_latency_ms", condition="> 5000", severity=AlertSeverity.WARNING, description="LLM latency exceeds 5s"),
    AlertRule(name="high_cost", metric="llm.hourly_cost_usd", condition="> 50", severity=AlertSeverity.WARNING, description="Hourly LLM cost exceeds $50"),
]

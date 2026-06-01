"""Async scheduler service for workflow triggers.

Supports cron, event, and webhook trigger types.
Uses asyncio (no Celery dependency).
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.base import TriggerModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cron expression parser (5-field: min hour dom month dow)
# ---------------------------------------------------------------------------

def parse_cron_field(field_value: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field into a set of matching values."""
    values: set[int] = set()
    for part in field_value.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(min_val, max_val + 1))
        elif part.startswith("*/"):
            step = int(part[2:])
            values.update(range(min_val, max_val + 1, step))
        elif "-" in part:
            start, end = part.split("-", 1)
            values.update(range(int(start), int(end) + 1))
        else:
            values.add(int(part))
    return values


def cron_matches(expression: str, dt: Optional[datetime] = None) -> bool:
    """Check if a 5-field cron expression matches the given datetime.

    Fields: minute hour day-of-month month day-of-week
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Invalid cron expression (expected 5 fields): {expression}")

    checks = [
        (fields[0], dt.minute, 0, 59),
        (fields[1], dt.hour, 0, 23),
        (fields[2], dt.day, 1, 31),
        (fields[3], dt.month, 1, 12),
        (fields[4], dt.weekday(), 0, 6),  # Monday=0
    ]

    for expr, current, min_val, max_val in checks:
        allowed = parse_cron_field(expr, min_val, max_val)
        if current not in allowed:
            return False
    return True


def next_cron_occurrence(expression: str, after: Optional[datetime] = None) -> datetime:
    """Find the next occurrence of a cron expression after the given time.

    Simple brute-force: check minute by minute up to 2 days ahead.
    Uses ``timedelta`` for correct month/year/leap-year boundaries (FW-H09).
    """
    if after is None:
        after = datetime.now(timezone.utc)

    dt = after.replace(second=0, microsecond=0)
    for _ in range(2880):  # 2 days in minutes
        dt = dt + timedelta(minutes=1)
        if cron_matches(expression, dt):
            return dt
    raise ValueError(f"Could not find next occurrence for cron: {expression}")


# ---------------------------------------------------------------------------
# Scheduler Service
# ---------------------------------------------------------------------------

class SchedulerService:
    """Singleton async scheduler for workflow triggers."""

    _instance: Optional["SchedulerService"] = None

    def __new__(cls) -> "SchedulerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._cron_triggers: dict[str, dict[str, Any]] = {}  # trigger_id -> info
        self._event_triggers: dict[str, list[dict[str, Any]]] = {}  # event_type -> [trigger_info]

    async def start(self) -> None:
        """Initialize scheduler: load active triggers from DB and start loop."""
        if self._running:
            return

        logger.info("Starting scheduler service...")
        self._running = True

        # Load active triggers
        try:
            async with async_session() as db:
                stmt = select(TriggerModel).where(TriggerModel.enabled.is_(True))
                result = await db.execute(stmt)
                triggers = result.scalars().all()

                for trigger in triggers:
                    self._register_trigger(trigger)

                logger.info(
                    "Loaded %d cron triggers, %d event triggers",
                    len(self._cron_triggers),
                    sum(len(v) for v in self._event_triggers.values()),
                )
        except Exception as exc:
            logger.warning("Failed to load triggers from DB: %s", exc)

        # Start the polling loop
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Clean up scheduler resources."""
        logger.info("Stopping scheduler service...")
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self._cron_triggers.clear()
        self._event_triggers.clear()

    def _register_trigger(self, trigger: Any) -> None:
        """Register a single trigger in memory."""
        trigger_id = trigger.id
        config = trigger.config or {}

        if trigger.trigger_type == "cron":
            cron_expr = config.get("cron_expression", "")
            if cron_expr:
                self._cron_triggers[trigger_id] = {
                    "id": trigger_id,
                    "workflow_id": trigger.workflow_id,
                    "cron_expression": cron_expr,
                    "config": config,
                }

        elif trigger.trigger_type == "event":
            event_type = config.get("event_type", "")
            if event_type:
                self._event_triggers.setdefault(event_type, []).append({
                    "id": trigger_id,
                    "workflow_id": trigger.workflow_id,
                    "config": config,
                })

    def add_cron_trigger(self, trigger: Any) -> None:
        """Schedule a cron trigger."""
        self._register_trigger(trigger)

    def remove_cron_trigger(self, trigger_id: str) -> None:
        """Remove a cron trigger by ID."""
        self._cron_triggers.pop(trigger_id, None)
        # Also remove from event triggers
        for event_type in list(self._event_triggers):
            self._event_triggers[event_type] = [
                t for t in self._event_triggers[event_type] if t["id"] != trigger_id
            ]
            if not self._event_triggers[event_type]:
                del self._event_triggers[event_type]

    async def fire_trigger(self, trigger_id: str) -> dict[str, Any]:
        """Execute the workflow associated with a trigger."""
        logger.info("Firing trigger %s", trigger_id)

        # Update last_triggered_at
        try:
            async with async_session() as db:
                stmt = select(TriggerModel).where(TriggerModel.id == trigger_id)
                result = await db.execute(stmt)
                trigger = result.scalar_one_or_none()
                if trigger:
                    trigger.last_triggered_at = datetime.now(timezone.utc)
                    await db.commit()

                    # Execute the workflow
                    from app.engines.workflow_engine.workflow import WorkflowEngine
                    from app.models.base import WorkflowModel

                    wf_stmt = select(WorkflowModel).where(WorkflowModel.id == trigger.workflow_id)
                    wf_result = await db.execute(wf_stmt)
                    workflow = wf_result.scalar_one_or_none()
                    if not workflow:
                        return {"status": "error", "message": "Workflow not found"}

                    engine = WorkflowEngine()
                    dag = engine.load_dag_from_config(workflow.dag_config)
                    result_data = await engine.execute(dag)
                    return {"status": "fired", "trigger_id": trigger_id, "workflow_result": result_data}
        except Exception as exc:
            logger.error("Failed to fire trigger %s: %s", trigger_id, exc)
            return {"status": "error", "message": str(exc)}

        return {"status": "error", "message": "Trigger not found"}

    async def process_event(self, event_type: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Check event triggers and fire matching ones."""
        triggers = self._event_triggers.get(event_type, [])
        results: list[dict[str, Any]] = []
        for t in triggers:
            result = await self.fire_trigger(t["id"])
            results.append(result)
        return results

    async def _poll_loop(self) -> None:
        """Main loop: check cron triggers every 30 seconds."""
        logger.info("Scheduler poll loop started")
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                for trigger_id, info in list(self._cron_triggers.items()):
                    try:
                        if cron_matches(info["cron_expression"], now):
                            await self.fire_trigger(trigger_id)
                    except Exception as exc:
                        logger.error("Error checking cron trigger %s: %s", trigger_id, exc)

                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Scheduler poll loop error: %s", exc)
                await asyncio.sleep(5)

        logger.info("Scheduler poll loop stopped")


# Module-level singleton accessor
def get_scheduler() -> SchedulerService:
    return SchedulerService()

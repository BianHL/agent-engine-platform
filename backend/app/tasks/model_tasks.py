"""Model-related tasks: health checks, budget alerts, usage aggregation."""
from datetime import datetime, timedelta, timezone

from celery.utils.log import get_task_logger
from sqlalchemy import func, select

from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.model_tasks.check_budget_alerts")
def check_budget_alerts(tenant_id: str, monthly_budget: float):
    """Check if tenant has exceeded budget thresholds."""
    from sqlalchemy import select, func
    from app.models.base import UsageLogModel
    from app.core.database import async_session
    import asyncio

    async def _check():
        async with async_session() as db:
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            stmt = select(func.sum(UsageLogModel.cost)).where(
                UsageLogModel.tenant_id == tenant_id,
                UsageLogModel.created_at >= month_start,
            )
            result = await db.execute(stmt)
            total_cost = result.scalar() or 0.0

            usage_ratio = total_cost / monthly_budget if monthly_budget > 0 else 0

            if usage_ratio >= 1.0:
                logger.warning(f"Tenant {tenant_id} exceeded budget: {total_cost}/{monthly_budget}")
                return {"status": "exceeded", "total_cost": total_cost, "budget": monthly_budget}
            elif usage_ratio >= 0.8:
                logger.warning(f"Tenant {tenant_id} approaching budget: {total_cost}/{monthly_budget}")
                return {"status": "warning", "total_cost": total_cost, "budget": monthly_budget}

            return {"status": "ok", "total_cost": total_cost, "budget": monthly_budget}

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.model_tasks.check_model_health")
def check_model_health():
    """Check health of all enabled model configs by sending a test prompt."""
    import asyncio
    import time as _time

    from app.models.base import ModelConfigModel, ModelProviderModel
    from app.core.database import async_session

    async def _check():
        results = []
        async with async_session() as db:
            stmt = (
                select(ModelConfigModel, ModelProviderModel)
                .join(ModelProviderModel, ModelConfigModel.provider_id == ModelProviderModel.id)
                .where(ModelConfigModel.enabled.is_(True))
            )
            rows = await db.execute(stmt)
            configs = rows.all()

            for config, provider in configs:
                health = await _probe_model(db, config, provider)
                results.append(health)

        logger.info(f"Health check completed: {len(results)} models checked")
        return {"checked": len(results), "results": results}

    return asyncio.run(_check())


async def _probe_model(db, config, provider) -> dict:
    """Send a lightweight test prompt and record latency."""
    import time as _time

    from app.engines.model_engine.base import BaseLLMAdapter

    result = {
        "model_name": config.model_name,
        "provider": provider.name,
        "healthy": False,
        "latency_ms": 0,
        "error": None,
    }

    try:
        adapter = _build_adapter(provider)
        if adapter is None:
            result["error"] = "no adapter for provider type"
            return result

        start = _time.monotonic()
        await adapter.chat(
            messages=[{"role": "user", "content": "ping"}],
            model=config.model_name,
            temperature=0.0,
            max_tokens=5,
        )
        latency = int((_time.monotonic() - start) * 1000)

        result["healthy"] = True
        result["latency_ms"] = latency

        # 更新 healthy 状态到 config
        config.config = {**(config.config or {}), "healthy": True, "latency_ms": latency}
        await db.flush()

    except Exception as exc:
        result["error"] = str(exc)[:200]
        config.config = {**(config.config or {}), "healthy": False, "latency_ms": 0}
        await db.flush()

    return result


def _build_adapter(provider):
    """Instantiate adapter based on provider type. Returns None if unsupported."""
    # 延迟导入避免循环依赖；实际项目中按 provider_type 分发
    try:
        if provider.provider_type in ("openai", "azure_openai", "zhipu", "qwen"):
            from app.engines.model_engine.router import ModelRouter
            return None  # 由 router 统一管理，这里只做健康标记
    except ImportError:
        pass
    return None


@celery_app.task(name="app.tasks.model_tasks.aggregate_usage_daily")
def aggregate_usage_daily():
    """Aggregate yesterday's usage logs into model_usage_daily summary."""
    import asyncio

    from app.models.base import UsageLogModel, ModelUsageDailyModel
    from app.core.database import async_session

    async def _aggregate():
        async with async_session() as db:
            now = datetime.now(timezone.utc)
            yesterday = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 按 tenant + model 聚合
            stmt = (
                select(
                    UsageLogModel.tenant_id,
                    UsageLogModel.model_provider,
                    UsageLogModel.model_name,
                    func.count(UsageLogModel.id).label("request_count"),
                    func.coalesce(func.sum(UsageLogModel.input_tokens), 0).label("total_input_tokens"),
                    func.coalesce(func.sum(UsageLogModel.output_tokens), 0).label("total_output_tokens"),
                    func.coalesce(func.sum(UsageLogModel.cost), 0.0).label("total_cost"),
                )
                .where(
                    UsageLogModel.created_at >= yesterday,
                    UsageLogModel.created_at < today,
                )
                .group_by(
                    UsageLogModel.tenant_id,
                    UsageLogModel.model_provider,
                    UsageLogModel.model_name,
                )
            )
            rows = await db.execute(stmt)
            aggregates = rows.all()

            upserted = 0
            for agg in aggregates:
                existing = await db.execute(
                    select(ModelUsageDailyModel).where(
                        ModelUsageDailyModel.tenant_id == agg.tenant_id,
                        ModelUsageDailyModel.date == yesterday,
                        ModelUsageDailyModel.model_provider == agg.model_provider,
                        ModelUsageDailyModel.model_name == agg.model_name,
                    )
                )
                daily = existing.scalar_one_or_none()
                if daily:
                    daily.request_count = agg.request_count
                    daily.total_input_tokens = agg.total_input_tokens
                    daily.total_output_tokens = agg.total_output_tokens
                    daily.total_cost = agg.total_cost
                else:
                    daily = ModelUsageDailyModel(
                        tenant_id=agg.tenant_id,
                        date=yesterday,
                        model_provider=agg.model_provider,
                        model_name=agg.model_name,
                        request_count=agg.request_count,
                        total_input_tokens=agg.total_input_tokens,
                        total_output_tokens=agg.total_output_tokens,
                        total_cost=agg.total_cost,
                    )
                    db.add(daily)
                upserted += 1

            await db.flush()
            logger.info(f"Aggregated usage for {upserted} tenant-model pairs")
            return {"upserted": upserted, "date": yesterday.isoformat()}

    return asyncio.run(_aggregate())

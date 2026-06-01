from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class CostTracker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def track(self, tenant_id: str, user_id: str, provider: str, model: str, input_tokens: int, output_tokens: int):
        from app.models.base import UsageLogModel, ModelConfigModel
        # Get pricing with row lock
        stmt = select(ModelConfigModel).where(
            ModelConfigModel.tenant_id == tenant_id,
            ModelConfigModel.model_name == model
        ).with_for_update()
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        input_price = 0.0
        output_price = 0.0
        if config and config.config:
            input_price = config.config.get("input_price", 0.0)
            output_price = config.config.get("output_price", 0.0)

        cost = (input_tokens * input_price + output_tokens * output_price) / 1000.0

        log = UsageLogModel(
            tenant_id=tenant_id,
            user_id=user_id,
            model_provider=provider,
            model_name=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            request_type="chat"
        )
        self.db.add(log)
        await self.db.flush()
        return cost

    async def get_usage(self, tenant_id: str, start_date: datetime = None, end_date: datetime = None):
        from app.models.base import UsageLogModel
        from sqlalchemy import func
        stmt = select(
            func.sum(UsageLogModel.input_tokens).label("total_input"),
            func.sum(UsageLogModel.output_tokens).label("total_output"),
            func.sum(UsageLogModel.cost).label("total_cost"),
            func.count(UsageLogModel.id).label("request_count")
        ).where(UsageLogModel.tenant_id == tenant_id)
        if start_date:
            stmt = stmt.where(UsageLogModel.created_at >= start_date)
        if end_date:
            stmt = stmt.where(UsageLogModel.created_at <= end_date)
        result = await self.db.execute(stmt)
        row = result.one()
        return {
            "total_input_tokens": row.total_input or 0,
            "total_output_tokens": row.total_output or 0,
            "total_cost": row.total_cost or 0.0,
            "request_count": row.request_count or 0
        }

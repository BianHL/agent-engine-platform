"""Organization hierarchy service — 组织架构穿透式权限服务."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import TenantModel

logger = logging.getLogger(__name__)


class OrgService:
    """组织架构穿透式权限服务."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_ancestors(self, tenant_id: str) -> List[str]:
        """获取租户的所有上级租户ID列表（从父到根）."""
        try:
            ancestors = []
            current_id = tenant_id
            visited = set()

            while current_id and current_id not in visited:
                visited.add(current_id)
                q = select(TenantModel.parent_id).where(TenantModel.id == current_id)
                result = await self.db.execute(q)
                parent_id = result.scalar_one_or_none()
                if parent_id:
                    ancestors.append(parent_id)
                current_id = parent_id

            return ancestors
        except Exception as e:
            logger.exception("get_tenant_ancestors failed")
            raise

    async def get_tenant_descendants(self, tenant_id: str) -> List[str]:
        """获取租户的所有下级租户ID列表（BFS遍历）."""
        descendants = []
        queue = [tenant_id]
        visited = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if current != tenant_id:
                descendants.append(current)

            q = select(TenantModel.id).where(TenantModel.parent_id == current)
            result = await self.db.execute(q)
            children = [row[0] for row in result.all()]
            queue.extend(children)

        return descendants

    async def get_visible_tenant_ids(self, tenant_id: str, scope: str = "down") -> List[str]:
        """获取可见的租户ID列表.
        scope: "self" | "down" (self+下级) | "up" (self+上级) | "all"
        """
        try:
            visible = [tenant_id]

            if scope in ("down", "all"):
                visible.extend(await self.get_tenant_descendants(tenant_id))

            if scope in ("up", "all"):
                visible.extend(await self.get_tenant_ancestors(tenant_id))

            return list(set(visible))
        except Exception as e:
            logger.exception("get_visible_tenant_ids failed")
            raise

    async def get_org_tree(self, root_tenant_id: str, asset_counts: Dict[str, int] = None) -> dict:
        """构建组织架构树（含资产数量）."""
        asset_counts = asset_counts or {}

        q = select(TenantModel).where(
            TenantModel.id == root_tenant_id
        )
        result = await self.db.execute(q)
        root = result.scalar_one_or_none()
        if not root:
            return {}

        return await self._build_tree(root, asset_counts)

    async def _build_tree(self, tenant: TenantModel, asset_counts: Dict[str, int]) -> dict:
        """递归构建树节点."""
        children_q = select(TenantModel).where(TenantModel.parent_id == tenant.id)
        children_result = await self.db.execute(children_q)
        children = children_result.scalars().all()

        child_nodes = []
        for child in children:
            child_nodes.append(await self._build_tree(child, asset_counts))

        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "org_level": tenant.org_level,
            "asset_count": asset_counts.get(tenant.id, 0),
            "children": child_nodes,
        }

    async def count_items_by_tenant(self, tenant_id: str) -> int:
        """统计租户的市集资产数量."""
        from app.models.marketplace import MarketplaceItem
        q = select(func.count()).select_from(MarketplaceItem).where(
            MarketplaceItem.tenant_id == tenant_id,
            MarketplaceItem.status.in_(["published", "approved"]),
        )
        result = await self.db.execute(q)
        return result.scalar() or 0

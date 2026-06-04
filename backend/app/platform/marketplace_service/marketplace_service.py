"""Marketplace service — AI市集业务逻辑层."""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import HTTPException

from app.models.marketplace import (
    MarketplaceItem,
    MarketplaceReviewModel,
    MarketplaceRatingModel,
    MarketplaceCloneModel,
    MarketplaceChangeLogModel,
)
from app.models.agent import AgentModel
from app.models.user import UserModel
from app.models.tenant import TenantModel

logger = logging.getLogger(__name__)


class MarketplaceService:
    """AI市集核心业务服务."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== 市集浏览 ==========

    async def list_items(
        self,
        tenant_id: str,
        user_id: str,
        keyword: str = "",
        category: str = "",
        tags: str = "",
        asset_type: str = "",
        sort_by: str = "latest",
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """列出市集资产（带可见范围过滤）."""
        try:
            # Build base query for published items
            conditions = [
                MarketplaceItem.status.in_(["published", "approved"]),
            ]

            # Org hierarchy penetration: show items from self + descendants (for "down" scope)
            from app.platform.org_service.org_service import OrgService
            org_svc = OrgService(self.db)
            visible_tenant_ids = await org_svc.get_visible_tenant_ids(tenant_id, scope="down")

            conditions.append(
                or_(
                    MarketplaceItem.visibility == "public",
                    MarketplaceItem.tenant_id.in_(visible_tenant_ids),
                )
            )

            if keyword:
                conditions.append(
                    or_(
                        MarketplaceItem.title.ilike(f"%{keyword}%"),
                        MarketplaceItem.summary.ilike(f"%{keyword}%"),
                    )
                )
            if category:
                conditions.append(MarketplaceItem.category == category)
            if asset_type:
                conditions.append(MarketplaceItem.asset_type == asset_type)
            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                for tag in tag_list:
                    conditions.append(MarketplaceItem.tags.contains(tag))

            # Count
            count_q = select(func.count()).select_from(MarketplaceItem).where(and_(*conditions))
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            # Sort
            order = desc(MarketplaceItem.published_at)
            if sort_by == "hottest":
                order = desc(MarketplaceItem.usage_count)
            elif sort_by == "rating":
                order = desc(MarketplaceItem.avg_rating)
            elif sort_by == "clones":
                order = desc(MarketplaceItem.clone_count)
            elif sort_by == "latest":
                order = desc(MarketplaceItem.created_at)

            # Query
            q = (
                select(MarketplaceItem)
                .where(and_(*conditions))
                .order_by(order)
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()

            return {
                "items": [self._to_list_dict(item) for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in list_items: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取市集资产详情."""
        try:
            q = select(MarketplaceItem).where(MarketplaceItem.id == item_id)
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                return None
            return self._to_detail_dict(item)
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_featured(self, limit: int = 8) -> List[Dict[str, Any]]:
        """获取精选推荐."""
        try:
            q = (
                select(MarketplaceItem)
                .where(
                    and_(
                        MarketplaceItem.status.in_(["published", "approved"]),
                        MarketplaceItem.featured == True,
                    )
                )
                .order_by(desc(MarketplaceItem.avg_rating))
                .limit(limit)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()
            return [self._to_list_dict(item) for item in items]
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_featured: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_hot(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门排行."""
        try:
            q = (
                select(MarketplaceItem)
                .where(MarketplaceItem.status.in_(["published", "approved"]))
                .order_by(desc(MarketplaceItem.usage_count))
                .limit(limit)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()
            return [self._to_list_dict(item) for item in items]
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_hot: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_categories(self) -> List[str]:
        """获取所有分类."""
        try:
            q = (
                select(MarketplaceItem.category)
                .where(
                    and_(
                        MarketplaceItem.category != "",
                        MarketplaceItem.status.in_(["published", "approved"]),
                    )
                )
                .distinct()
            )
            result = await self.db.execute(q)
            return [row[0] for row in result.all() if row[0]]
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_categories: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 上架申报 ==========

    async def submit_for_review(
        self, tenant_id: str, user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提交上架申请."""
        try:
            # Verify the source asset exists and belongs to the user's tenant
            asset_type = data["asset_type"]
            asset_id = data["asset_id"]

            if asset_type == "agent":
                q = select(AgentModel).where(
                    and_(AgentModel.id == asset_id, AgentModel.tenant_id == tenant_id)
                )
                result = await self.db.execute(q)
                asset = result.scalar_one_or_none()
                if not asset:
                    raise ValueError("Asset not found or access denied")
                # Take a config snapshot
                config_snapshot = {
                    "name": asset.name,
                    "description": asset.description,
                    "model_provider": asset.model_provider,
                    "model_name": asset.model_name,
                    "model_config": asset.model_config,
                    "system_prompt": asset.system_prompt,
                    "tools": asset.tools,
                    "knowledge_base_ids": asset.knowledge_base_ids,
                    "safety_config": asset.safety_config,
                }
            else:
                config_snapshot = {}

            # Create marketplace item
            item = MarketplaceItem(
                tenant_id=tenant_id,
                creator_id=user_id,
                asset_type=asset_type,
                asset_id=asset_id,
                title=data["title"],
                summary=data.get("summary", ""),
                description=data.get("description", ""),
                cover_image=data.get("cover_image"),
                category=data.get("category", ""),
                tags=data.get("tags", []),
                visibility=data.get("visibility", "tenant"),
                status="pending_review",
                config_snapshot=config_snapshot,
            )
            self.db.add(item)
            await self.db.flush()

            # Create review record
            review = MarketplaceReviewModel(
                item_id=item.id,
                tenant_id=tenant_id,
                submitter_id=user_id,
                review_type="publish",
                status="pending",
            )
            self.db.add(review)
            await self.db.flush()

            # Link agent to marketplace item
            if asset_type == "agent":
                asset.marketplace_item_id = item.id
                asset.visibility = data.get("visibility", "tenant")
                await self.db.flush()

            await self._log_change(item.id, tenant_id, user_id, "create", description="提交上架申请")

            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in submit_for_review: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_my_submissions(
        self, tenant_id: str, user_id: str, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """获取我的提交记录."""
        try:
            conditions = [
                MarketplaceItem.tenant_id == tenant_id,
                MarketplaceItem.creator_id == user_id,
            ]

            count_q = (
                select(func.count())
                .select_from(MarketplaceItem)
                .where(and_(*conditions))
            )
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceItem)
                .where(and_(*conditions))
                .order_by(desc(MarketplaceItem.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()

            return {
                "items": [self._to_detail_dict(item) for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_my_submissions: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def cancel_submission(
        self, item_id: str, tenant_id: str, user_id: str
    ) -> Dict[str, Any]:
        """撤回提交."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.creator_id == user_id,
                    MarketplaceItem.status == "pending_review",
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found or cannot be cancelled")

            item.status = "draft"
            await self.db.flush()

            # Update review status
            rq = select(MarketplaceReviewModel).where(
                and_(
                    MarketplaceReviewModel.item_id == item_id,
                    MarketplaceReviewModel.status == "pending",
                )
            )
            rresult = await self.db.execute(rq)
            review = rresult.scalar_one_or_none()
            if review:
                review.status = "rejected"
                review.comment = "Cancelled by submitter"
                review.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
                await self.db.flush()

            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in cancel_submission: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 审核管理 ==========

    async def list_pending_reviews(
        self, tenant_id: str, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """列出待审核项目."""
        try:
            conditions = [
                MarketplaceItem.tenant_id == tenant_id,
                MarketplaceItem.status == "pending_review",
            ]

            count_q = (
                select(func.count())
                .select_from(MarketplaceItem)
                .where(and_(*conditions))
            )
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceItem)
                .where(and_(*conditions))
                .order_by(asc(MarketplaceItem.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()

            return {
                "items": [self._to_detail_dict(item) for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in list_pending_reviews: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def list_pending_promotion_reviews(self, tenant_id: str, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """列出待上级复核的提级申请."""
        try:
            conditions = [
                MarketplaceItem.status == "pending_promotion_review",
            ]

            # Find child tenant IDs
            child_q = select(TenantModel.id).where(TenantModel.parent_id == tenant_id)
            child_result = await self.db.execute(child_q)
            child_ids = [row[0] for row in child_result.all()]

            if not child_ids:
                return {"items": [], "total": 0, "page": page, "size": size}

            conditions.append(MarketplaceItem.tenant_id.in_(child_ids))

            count_q = select(func.count()).select_from(MarketplaceItem).where(and_(*conditions))
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceItem)
                .where(and_(*conditions))
                .order_by(asc(MarketplaceItem.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()

            return {
                "items": [self._to_detail_dict(item) for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in list_pending_promotion_reviews: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def approve_review(
        self, item_id: str, tenant_id: str, reviewer_id: str, comment: str = ""
    ) -> Dict[str, Any]:
        """审核通过（支持本级初审和跨级复核）."""
        try:
            # Determine which status we're approving
            item = None
            old_status = None

            # Try pending_review first (本级初审 — item belongs to this tenant)
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.status == "pending_review",
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if item:
                old_status = "pending_review"
            else:
                # Try pending_promotion_review (跨级复核 — item belongs to a child tenant)
                child_q = select(TenantModel.id).where(TenantModel.parent_id == tenant_id)
                child_result = await self.db.execute(child_q)
                child_ids = [row[0] for row in child_result.all()]

                if child_ids:
                    q2 = select(MarketplaceItem).where(
                        and_(
                            MarketplaceItem.id == item_id,
                            MarketplaceItem.tenant_id.in_(child_ids),
                            MarketplaceItem.status == "pending_promotion_review",
                        )
                    )
                    result2 = await self.db.execute(q2)
                    item = result2.scalar_one_or_none()
                    if item:
                        old_status = "pending_promotion_review"

            if not item:
                raise ValueError("Item not found or not in a reviewable status")

            item.reject_reason = None

            if old_status == "pending_review":
                # 本级审核通过
                if item.visibility == "public":
                    # 需要跨级复核 → 查找上级租户
                    tenant_q = select(TenantModel.parent_id).where(TenantModel.id == tenant_id)
                    tenant_result = await self.db.execute(tenant_q)
                    parent_id = tenant_result.scalar_one_or_none()

                    if parent_id:
                        # 有上级 → 提交上级复核
                        item.status = "pending_promotion_review"
                        review = MarketplaceReviewModel(
                            item_id=item.id,
                            tenant_id=parent_id,
                            submitter_id=reviewer_id,
                            review_type="promote",
                            status="pending",
                        )
                        self.db.add(review)
                        await self._log_change(item_id, tenant_id, reviewer_id, "status_change", "status", "pending_review", "pending_promotion_review", "本级审核通过，提交上级复核")

                        # Update the current review record
                        rq = select(MarketplaceReviewModel).where(
                            and_(
                                MarketplaceReviewModel.item_id == item_id,
                                MarketplaceReviewModel.status == "pending",
                                MarketplaceReviewModel.tenant_id == tenant_id,
                            )
                        )
                        rresult = await self.db.execute(rq)
                        review = rresult.scalar_one_or_none()
                        if review:
                            review.status = "approved"
                            review.reviewer_id = reviewer_id
                            review.comment = comment
                            review.reviewed_at = datetime.now(UTC).replace(tzinfo=None)

                        await self.db.flush()
                        return {"id": item.id, "status": item.status, "message": "已提交上级复核"}
                    else:
                        # 无上级 → 直接发布
                        item.status = "published"
                        item.published_at = datetime.now(UTC).replace(tzinfo=None)
                else:
                    # department/tenant visibility → 本级可直接决定
                    item.status = "published"
                    item.published_at = datetime.now(UTC).replace(tzinfo=None)

            elif old_status == "pending_promotion_review":
                # 上级复核通过
                item.status = "published"
                item.published_at = datetime.now(UTC).replace(tzinfo=None)

            # Update review record (for the current tenant's pending review)
            rq = select(MarketplaceReviewModel).where(
                and_(
                    MarketplaceReviewModel.item_id == item_id,
                    MarketplaceReviewModel.status == "pending",
                    MarketplaceReviewModel.tenant_id == tenant_id,
                )
            )
            rresult = await self.db.execute(rq)
            review = rresult.scalar_one_or_none()
            if review:
                review.status = "approved"
                review.reviewer_id = reviewer_id
                review.comment = comment
                review.reviewed_at = datetime.now(UTC).replace(tzinfo=None)

            await self._log_change(item_id, tenant_id, reviewer_id, "status_change", "status", old_status, item.status, "审核通过")

            await self.db.flush()
            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in approve_review: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def reject_review(
        self, item_id: str, tenant_id: str, reviewer_id: str, comment: str = ""
    ) -> Dict[str, Any]:
        """审核驳回（支持本级初审和跨级复核）."""
        try:
            item = None
            old_status = None

            # Try pending_review first (本级初审 — item belongs to this tenant)
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.status == "pending_review",
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if item:
                old_status = "pending_review"
            else:
                # Try pending_promotion_review (跨级复核 — item belongs to a child tenant)
                child_q = select(TenantModel.id).where(TenantModel.parent_id == tenant_id)
                child_result = await self.db.execute(child_q)
                child_ids = [row[0] for row in child_result.all()]

                if child_ids:
                    q2 = select(MarketplaceItem).where(
                        and_(
                            MarketplaceItem.id == item_id,
                            MarketplaceItem.tenant_id.in_(child_ids),
                            MarketplaceItem.status == "pending_promotion_review",
                        )
                    )
                    result2 = await self.db.execute(q2)
                    item = result2.scalar_one_or_none()
                    if item:
                        old_status = "pending_promotion_review"

            if not item:
                raise ValueError("Item not found or not in a reviewable status")

            item.status = "rejected"
            item.reject_reason = comment

            # Update review record
            rq = select(MarketplaceReviewModel).where(
                and_(
                    MarketplaceReviewModel.item_id == item_id,
                    MarketplaceReviewModel.status == "pending",
                    MarketplaceReviewModel.tenant_id == tenant_id,
                )
            )
            rresult = await self.db.execute(rq)
            review = rresult.scalar_one_or_none()
            if review:
                review.status = "rejected"
                review.reviewer_id = reviewer_id
                review.comment = comment
                review.reviewed_at = datetime.now(UTC).replace(tzinfo=None)

            await self._log_change(item_id, tenant_id, reviewer_id, "status_change", "status", old_status, "rejected", f"审核驳回: {comment}")

            await self.db.flush()
            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in reject_review: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 资产管控 ==========

    async def freeze_item(
        self, item_id: str, tenant_id: str, reason: str = ""
    ) -> Dict[str, Any]:
        """冻结资产."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")

            old_status = item.status
            item.status = "frozen"
            item.frozen_at = datetime.now(UTC).replace(tzinfo=None)
            item.frozen_reason = reason

            await self._log_change(item_id, tenant_id, "system", "status_change", "status", old_status, "frozen", f"冻结: {reason}")

            await self.db.flush()
            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in freeze_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def unfreeze_item(
        self, item_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """解冻资产."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.status == "frozen",
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found or not frozen")

            item.status = "published"
            item.frozen_at = None
            item.frozen_reason = None

            await self._log_change(item_id, tenant_id, "system", "status_change", "status", "frozen", "published", "解冻")

            await self.db.flush()
            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in unfreeze_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def takedown_item(
        self, item_id: str, tenant_id: str, reason: str = ""
    ) -> Dict[str, Any]:
        """强制下架."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")

            old_status = item.status
            item.status = "takedown"
            item.frozen_reason = reason

            await self._log_change(item_id, tenant_id, "system", "status_change", "status", old_status, "takedown", f"下架: {reason}")

            await self.db.flush()
            return {"id": item.id, "status": item.status}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in takedown_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def promote_item(
        self, item_id: str, tenant_id: str, target_level: str
    ) -> Dict[str, Any]:
        """资产提级."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")

            # Expand visibility based on target level
            old_visibility = item.visibility
            if target_level == "group":
                item.visibility = "public"
                item.promoted_level = "group"
            elif target_level == "tenant":
                item.visibility = "tenant"
                item.promoted_level = "tenant"
            elif target_level == "department":
                item.visibility = "department"
                item.promoted_level = "department"

            await self._log_change(item_id, tenant_id, "system", "promote", "visibility", old_visibility, target_level, f"提级至{target_level}")

            await self.db.flush()
            return {"id": item.id, "visibility": item.visibility, "promoted_level": item.promoted_level}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in promote_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def toggle_featured(
        self, item_id: str, tenant_id: str, featured: bool
    ) -> Dict[str, Any]:
        """设置/取消精选."""
        try:
            q = select(MarketplaceItem).where(
                and_(
                    MarketplaceItem.id == item_id,
                    MarketplaceItem.tenant_id == tenant_id,
                )
            )
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")

            item.featured = featured
            await self.db.flush()
            return {"id": item.id, "featured": item.featured}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in toggle_featured: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def list_admin_items(
        self,
        tenant_id: str,
        status: str = "",
        keyword: str = "",
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """管理员查看资产列表（含所有状态）."""
        try:
            conditions = [MarketplaceItem.tenant_id == tenant_id]
            if status:
                conditions.append(MarketplaceItem.status == status)
            if keyword:
                conditions.append(
                    or_(
                        MarketplaceItem.title.ilike(f"%{keyword}%"),
                        MarketplaceItem.summary.ilike(f"%{keyword}%"),
                    )
                )

            count_q = (
                select(func.count())
                .select_from(MarketplaceItem)
                .where(and_(*conditions))
            )
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceItem)
                .where(and_(*conditions))
                .order_by(desc(MarketplaceItem.updated_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            items = result.scalars().all()

            return {
                "items": [self._to_detail_dict(item) for item in items],
                "total": total,
                "page": page,
                "size": size,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in list_admin_items: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 评分 ==========

    async def create_rating(
        self, item_id: str, user_id: str, tenant_id: str, score: int, comment: str = None
    ) -> Dict[str, Any]:
        """创建/更新评分."""
        try:
            # Check item exists
            q = select(MarketplaceItem).where(MarketplaceItem.id == item_id)
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")

            # Check existing rating
            rq = select(MarketplaceRatingModel).where(
                and_(
                    MarketplaceRatingModel.item_id == item_id,
                    MarketplaceRatingModel.user_id == user_id,
                )
            )
            rresult = await self.db.execute(rq)
            existing = rresult.scalar_one_or_none()

            if existing:
                existing.score = score
                existing.comment = comment
                await self.db.flush()
                rating_id = existing.id
            else:
                rating = MarketplaceRatingModel(
                    item_id=item_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    score=score,
                    comment=comment,
                )
                self.db.add(rating)
                await self.db.flush()
                rating_id = rating.id

            # Recalculate avg rating
            avg_q = select(
                func.avg(MarketplaceRatingModel.score),
                func.count(MarketplaceRatingModel.id),
            ).where(MarketplaceRatingModel.item_id == item_id)
            avg_result = await self.db.execute(avg_q)
            avg_row = avg_result.one()
            item.avg_rating = round(float(avg_row[0] or 0), 2)
            item.rating_count = int(avg_row[1] or 0)
            await self.db.flush()

            return {"id": rating_id, "score": score, "avg_rating": item.avg_rating}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in create_rating: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_item_ratings(
        self, item_id: str, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """获取资产评分列表."""
        try:
            count_q = (
                select(func.count())
                .select_from(MarketplaceRatingModel)
                .where(MarketplaceRatingModel.item_id == item_id)
            )
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceRatingModel)
                .where(MarketplaceRatingModel.item_id == item_id)
                .order_by(desc(MarketplaceRatingModel.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            ratings = result.scalars().all()

            items = []
            for r in ratings:
                # Get user name
                uq = select(UserModel.username).where(UserModel.id == r.user_id)
                uresult = await self.db.execute(uq)
                username = uresult.scalar_one_or_none() or "Unknown"
                items.append({
                    "id": r.id,
                    "item_id": r.item_id,
                    "user_id": r.user_id,
                    "score": r.score,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    "user_name": username,
                })

            return {"items": items, "total": total, "page": page, "size": size}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_item_ratings: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_my_rating(
        self, item_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取我的评分."""
        try:
            q = select(MarketplaceRatingModel).where(
                and_(
                    MarketplaceRatingModel.item_id == item_id,
                    MarketplaceRatingModel.user_id == user_id,
                )
            )
            result = await self.db.execute(q)
            rating = result.scalar_one_or_none()
            if not rating:
                return None
            return {
                "id": rating.id,
                "item_id": rating.item_id,
                "user_id": rating.user_id,
                "score": rating.score,
                "comment": rating.comment,
                "created_at": rating.created_at.isoformat() if rating.created_at else None,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_my_rating: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 克隆 ==========

    async def clone_item(
        self, item_id: str, cloner_id: str, target_tenant_id: str
    ) -> Dict[str, Any]:
        """克隆资产."""
        try:
            # Get source item
            q = select(MarketplaceItem).where(
                MarketplaceItem.id == item_id,
                MarketplaceItem.status.in_(["published", "approved"]),
            )
            result = await self.db.execute(q)
            source = result.scalar_one_or_none()
            if not source:
                raise ValueError("Source item not found or not published")

            config = source.config_snapshot or {}

            # Create new asset in target tenant
            if source.asset_type == "agent":
                new_agent = AgentModel(
                    tenant_id=target_tenant_id,
                    name=f"{config.get('name', source.title)} (克隆)",
                    description=config.get("description", ""),
                    model_provider=config.get("model_provider"),
                    model_name=config.get("model_name"),
                    model_config=config.get("model_config", {}),
                    system_prompt=config.get("system_prompt", ""),
                    tools=config.get("tools", []),
                    knowledge_base_ids=config.get("knowledge_base_ids", []),
                    safety_config=config.get("safety_config", {}),
                    status="draft",
                )
                self.db.add(new_agent)
                await self.db.flush()
                target_asset_id = new_agent.id
            else:
                target_asset_id = "not_implemented"

            # Record clone
            clone = MarketplaceCloneModel(
                source_item_id=item_id,
                target_tenant_id=target_tenant_id,
                target_asset_id=target_asset_id,
                cloner_id=cloner_id,
            )
            self.db.add(clone)

            # Increment clone count
            source.clone_count = (source.clone_count or 0) + 1

            await self._log_change(item_id, "system", cloner_id, "clone", description="资产被克隆")

            await self.db.flush()

            return {
                "id": clone.id,
                "source_item_id": item_id,
                "target_asset_id": target_asset_id,
                "clone_count": source.clone_count,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in clone_item: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 统计 ==========

    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取市集统计（增强版）."""
        try:
            # Total items
            tq = select(func.count()).select_from(MarketplaceItem).where(
                MarketplaceItem.tenant_id == tenant_id
            )
            total_result = await self.db.execute(tq)
            total_items = total_result.scalar() or 0

            # Published
            pq = select(func.count()).select_from(MarketplaceItem).where(
                and_(
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.status.in_(["published", "approved"]),
                )
            )
            pub_result = await self.db.execute(pq)
            published_items = pub_result.scalar() or 0

            # Pending review
            prq = select(func.count()).select_from(MarketplaceItem).where(
                and_(
                    MarketplaceItem.tenant_id == tenant_id,
                    MarketplaceItem.status == "pending_review",
                )
            )
            pend_result = await self.db.execute(prq)
            pending_items = pend_result.scalar() or 0

            # Ratings & usage
            rq = select(
                func.sum(MarketplaceItem.rating_count),
                func.sum(MarketplaceItem.clone_count),
                func.sum(MarketplaceItem.usage_count),
                func.avg(MarketplaceItem.avg_rating),
            ).where(MarketplaceItem.tenant_id == tenant_id)
            rresult = await self.db.execute(rq)
            row = rresult.one()

            # By category
            cq = (
                select(MarketplaceItem.category, func.count())
                .where(
                    and_(
                        MarketplaceItem.tenant_id == tenant_id,
                        MarketplaceItem.category != "",
                    )
                )
                .group_by(MarketplaceItem.category)
            )
            cresult = await self.db.execute(cq)
            by_category = {row[0]: row[1] for row in cresult.all()}

            # By status
            sq = (
                select(MarketplaceItem.status, func.count())
                .where(MarketplaceItem.tenant_id == tenant_id)
                .group_by(MarketplaceItem.status)
            )
            sresult = await self.db.execute(sq)
            by_status = {row[0]: row[1] for row in sresult.all()}

            # Covered organizations (tenants that have published assets)
            org_q = (
                select(
                    MarketplaceItem.tenant_id,
                    func.count(MarketplaceItem.id),
                )
                .where(MarketplaceItem.status.in_(["published", "approved"]))
                .group_by(MarketplaceItem.tenant_id)
            )
            org_result = await self.db.execute(org_q)
            org_coverage = {row[0]: row[1] for row in org_result.all()}

            # By tenant name
            tenant_q = (
                select(
                    TenantModel.name,
                    func.count(MarketplaceItem.id),
                )
                .join(TenantModel, MarketplaceItem.tenant_id == TenantModel.id)
                .where(MarketplaceItem.status.in_(["published", "approved"]))
                .group_by(TenantModel.name)
            )
            tenant_result = await self.db.execute(tenant_q)
            by_tenant_name = {row[0]: row[1] for row in tenant_result.all()}

            return {
                "total_items": total_items,
                "published_items": published_items,
                "pending_review_items": pending_items,
                "total_ratings": int(row[0] or 0),
                "total_clones": int(row[1] or 0),
                "total_usage": int(row[2] or 0),
                "avg_rating": round(float(row[3] or 0), 2),
                "items_by_category": by_category,
                "items_by_status": by_status,
                "covered_organizations": len(org_coverage),
                "items_by_tenant": by_tenant_name,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_stats: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_stats_trends(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """获取趋势数据（按天）."""
        try:
            from datetime import timedelta

            now = datetime.now(UTC).replace(tzinfo=None)
            start = now - timedelta(days=days)

            # Daily new items
            item_q = (
                select(
                    func.date(MarketplaceItem.created_at).label("date"),
                    func.count(MarketplaceItem.id),
                )
                .where(
                    and_(
                        MarketplaceItem.tenant_id == tenant_id,
                        MarketplaceItem.created_at >= start,
                    )
                )
                .group_by(func.date(MarketplaceItem.created_at))
                .order_by(func.date(MarketplaceItem.created_at))
            )
            item_result = await self.db.execute(item_q)
            daily_items = [{"date": str(row[0]), "count": row[1]} for row in item_result.all()]

            # Daily ratings
            rating_q = (
                select(
                    func.date(MarketplaceRatingModel.created_at).label("date"),
                    func.count(MarketplaceRatingModel.id),
                    func.avg(MarketplaceRatingModel.score),
                )
                .where(
                    and_(
                        MarketplaceRatingModel.tenant_id == tenant_id,
                        MarketplaceRatingModel.created_at >= start,
                    )
                )
                .group_by(func.date(MarketplaceRatingModel.created_at))
                .order_by(func.date(MarketplaceRatingModel.created_at))
            )
            rating_result = await self.db.execute(rating_q)
            daily_ratings = [
                {
                    "date": str(row[0]),
                    "count": row[1],
                    "avg_score": round(float(row[2] or 0), 2),
                }
                for row in rating_result.all()
            ]

            # Daily clones
            clone_q = (
                select(
                    func.date(MarketplaceCloneModel.created_at).label("date"),
                    func.count(MarketplaceCloneModel.id),
                )
                .where(MarketplaceCloneModel.created_at >= start)
                .group_by(func.date(MarketplaceCloneModel.created_at))
                .order_by(func.date(MarketplaceCloneModel.created_at))
            )
            clone_result = await self.db.execute(clone_q)
            daily_clones = [{"date": str(row[0]), "count": row[1]} for row in clone_result.all()]

            return {
                "period_days": days,
                "daily_items": daily_items,
                "daily_ratings": daily_ratings,
                "daily_clones": daily_clones,
            }
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_stats_trends: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 试用 ==========

    async def record_trial(self, item_id: str) -> None:
        """记录试用（增加usage_count）."""
        try:
            q = select(MarketplaceItem).where(MarketplaceItem.id == item_id)
            result = await self.db.execute(q)
            item = result.scalar_one_or_none()
            if item:
                item.usage_count = (item.usage_count or 0) + 1
                await self.db.flush()
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in record_trial: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== 变更日志 ==========

    async def get_changelog(self, item_id: str, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取资产变更日志."""
        try:
            count_q = select(func.count()).select_from(MarketplaceChangeLogModel).where(
                MarketplaceChangeLogModel.item_id == item_id
            )
            total_result = await self.db.execute(count_q)
            total = total_result.scalar() or 0

            q = (
                select(MarketplaceChangeLogModel)
                .where(MarketplaceChangeLogModel.item_id == item_id)
                .order_by(desc(MarketplaceChangeLogModel.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )
            result = await self.db.execute(q)
            logs = result.scalars().all()

            items = []
            for log in logs:
                items.append({
                    "id": log.id,
                    "item_id": log.item_id,
                    "operator_id": log.operator_id,
                    "change_type": log.change_type,
                    "field_name": log.field_name,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "description": log.description,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                })

            return {"items": items, "total": total, "page": page, "size": size}
        except (ValueError, HTTPException):
            raise
        except Exception as e:
            logger.error("Error in get_changelog: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # ========== Whitebox ==========

    def generate_whitebox_flow(self, config: dict) -> tuple:
        """将Agent配置转换为可视化流程图节点和边."""
        nodes = []
        edges = []
        x, y = 0, 0
        step = 250

        # 1. Input node
        nodes.append({
            "id": "input", "type": "custom", "label": "用户输入",
            "position": {"x": x, "y": y},
            "config": {"description": "用户发起的对话输入"},
            "style": {"background": "#1890ff"},
        })
        prev_id = "input"
        x += step

        # 2. System Prompt
        if config.get("system_prompt"):
            node_id = "system_prompt"
            prompt = config["system_prompt"]
            nodes.append({
                "id": node_id, "type": "custom", "label": "系统提示词",
                "position": {"x": x, "y": y},
                "config": {"prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt, "description": "定义Agent的角色和行为规范"},
                "style": {"background": "#1890ff"},
            })
            edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
            prev_id = node_id
            x += step

        # 3. LLM
        provider = config.get("model_provider", "")
        model = config.get("model_name", "")
        node_id = "llm"
        nodes.append({
            "id": node_id, "type": "custom", "label": f"LLM推理 ({provider}/{model})" if provider else "LLM推理",
            "position": {"x": x, "y": y},
            "config": {"model_provider": provider, "model_name": model, "description": f"使用{provider}的{model}模型进行推理" if provider else "大语言模型推理"},
            "style": {"background": "#1890ff"},
        })
        edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        x += step

        # 4. Tools
        tools = config.get("tools", [])
        if tools:
            node_id = "tools"
            tool_names = []
            for t in tools:
                if isinstance(t, dict):
                    tool_names.append(t.get("name", t.get("function", {}).get("name", "unknown")))
                else:
                    tool_names.append(str(t))
            nodes.append({
                "id": node_id, "type": "custom", "label": f"工具调用 ({len(tools)}个)",
                "position": {"x": x, "y": y},
                "config": {"tools": tool_names, "description": f"可调用{len(tools)}个外部工具: {', '.join(tool_names[:5])}"},
                "style": {"background": "#52c41a"},
            })
            edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
            prev_id = node_id
            x += step

        # 5. Knowledge Base
        kb_ids = config.get("knowledge_base_ids", [])
        if kb_ids:
            node_id = "knowledge"
            nodes.append({
                "id": node_id, "type": "custom", "label": f"知识库检索 ({len(kb_ids)}个)",
                "position": {"x": x, "y": y},
                "config": {"knowledge_base_count": len(kb_ids), "description": f"从{len(kb_ids)}个知识库中检索相关文档片段"},
                "style": {"background": "#722ed1"},
            })
            edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
            prev_id = node_id
            x += step

        # 6. Safety
        safety = config.get("safety_config", {})
        if safety:
            node_id = "safety"
            nodes.append({
                "id": node_id, "type": "custom", "label": "安全过滤",
                "position": {"x": x, "y": y},
                "config": {"description": "输入/输出内容安全检查（提示词注入检测、PII脱敏、敏感词过滤）"},
                "style": {"background": "#fa541c"},
            })
            edges.append({"id": f"e_{prev_id}_{node_id}", "source": prev_id, "target": node_id})
            prev_id = node_id
            x += step

        # 7. Output
        nodes.append({
            "id": "output", "type": "custom", "label": "Agent响应",
            "position": {"x": x, "y": y},
            "config": {"description": "最终输出给用户的响应"},
            "style": {"background": "#52c41a"},
        })
        edges.append({"id": f"e_{prev_id}_output", "source": prev_id, "target": "output"})

        return nodes, edges

    # ========== Helper methods ==========

    async def _log_change(self, item_id: str, tenant_id: str, operator_id: str, change_type: str, field_name: str = None, old_value=None, new_value=None, description: str = ""):
        """记录变更日志."""
        import json as _json
        log = MarketplaceChangeLogModel(
            item_id=item_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            change_type=change_type,
            field_name=field_name,
            old_value=_json.dumps(old_value, ensure_ascii=False, default=str) if old_value is not None else None,
            new_value=_json.dumps(new_value, ensure_ascii=False, default=str) if new_value is not None else None,
            description=description,
        )
        self.db.add(log)

    def _to_list_dict(self, item: MarketplaceItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "asset_type": item.asset_type,
            "title": item.title,
            "summary": item.summary,
            "cover_image": item.cover_image,
            "category": item.category,
            "tags": item.tags or [],
            "avg_rating": item.avg_rating or 0,
            "rating_count": item.rating_count or 0,
            "usage_count": item.usage_count or 0,
            "clone_count": item.clone_count or 0,
            "featured": item.featured or False,
            "promoted_level": item.promoted_level,
            "published_at": item.published_at.isoformat() if item.published_at else None,
        }

    def _to_detail_dict(self, item: MarketplaceItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "creator_id": item.creator_id,
            "asset_type": item.asset_type,
            "asset_id": item.asset_id,
            "title": item.title,
            "summary": item.summary,
            "description": item.description,
            "cover_image": item.cover_image,
            "category": item.category,
            "tags": item.tags or [],
            "visibility": item.visibility,
            "status": item.status,
            "reject_reason": item.reject_reason,
            "version": item.version or 1,
            "avg_rating": item.avg_rating or 0,
            "rating_count": item.rating_count or 0,
            "usage_count": item.usage_count or 0,
            "clone_count": item.clone_count or 0,
            "featured": item.featured or False,
            "promoted_level": item.promoted_level,
            "frozen_at": item.frozen_at.isoformat() if item.frozen_at else None,
            "frozen_reason": item.frozen_reason,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }

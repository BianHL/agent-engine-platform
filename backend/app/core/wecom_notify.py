"""企业微信消息通知服务."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WeComNotify:
    """企业微信消息通知."""

    @classmethod
    async def send_webhook(cls, content: str, msg_type: str = "markdown") -> bool:
        """通过Webhook发送消息."""
        webhook_url = getattr(settings, "WECOM_WEBHOOK_URL", "")
        if not webhook_url:
            logger.warning("WECOM_WEBHOOK_URL not configured")
            return False

        payload = {"msgtype": msg_type, msg_type: {"content": content}}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                data = resp.json()
                if data.get("errcode", 0) != 0:
                    logger.error("WeCom webhook failed: %s", data)
                    return False
                return True
        except Exception:
            logger.exception("WeCom webhook error")
            return False

    @classmethod
    async def send_review_notification(cls, user_id: str, item_title: str, status: str, reason: str = "") -> bool:
        """发送审核结果通知."""
        result_text = "✅ 通过" if status == "approved" else "❌ 驳回"
        content = (
            f"## AI市集审核通知\n"
            f"**资产名称**: {item_title}\n"
            f"**审核结果**: {result_text}\n"
        )
        if reason:
            content += f"**原因**: {reason}\n"
        content += "请登录平台查看详情。"
        return await cls.send_webhook(content)

    @classmethod
    async def send_alert(cls, level: str, title: str, content: str) -> bool:
        """发送告警通知."""
        markdown = f"## [{level}] {title}\n{content}"
        return await cls.send_webhook(markdown)

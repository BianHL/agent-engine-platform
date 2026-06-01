"""企业微信OAuth2认证服务."""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WeComAuth:
    """企业微信OAuth2认证."""

    @classmethod
    def _get_config(cls) -> dict:
        """Get WeCom config from settings (supports runtime override)."""
        return {
            "corp_id": getattr(settings, "WECOM_CORP_ID", ""),
            "agent_id": getattr(settings, "WECOM_AGENT_ID", ""),
            "secret": getattr(settings, "WECOM_SECRET", ""),
            "redirect_uri": getattr(settings, "WECOM_REDIRECT_URI", ""),
        }

    @classmethod
    async def get_access_token(cls) -> str:
        """获取access_token."""
        cfg = cls._get_config()
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {"corpid": cfg["corp_id"], "corpsecret": cfg["secret"]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            if data.get("errcode", 0) != 0:
                logger.error("WeCom get_access_token failed: %s", data)
                raise ValueError(f"WeCom API error: {data.get('errmsg', 'unknown')}")
            return data["access_token"]

    @classmethod
    async def get_user_info(cls, code: str) -> dict:
        """通过OAuth2 code获取用户信息."""
        token = await cls.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo?access_token={token}&code={code}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            if data.get("errcode", 0) != 0:
                logger.error("WeCom get_user_info failed: %s", data)
                raise ValueError(f"WeCom API error: {data.get('errmsg', 'unknown')}")
            return data

    @classmethod
    async def get_user_detail(cls, userid: str) -> dict:
        """获取用户详细信息."""
        token = await cls.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={token}&userid={userid}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            if data.get("errcode", 0) != 0:
                logger.error("WeCom get_user_detail failed: %s", data)
                raise ValueError(f"WeCom API error: {data.get('errmsg', 'unknown')}")
            return data

    @classmethod
    def get_login_url(cls) -> str:
        """获取企业微信OAuth2登录URL."""
        cfg = cls._get_config()
        return (
            f"https://open.work.weixin.qq.com/wwopen/sso/qrConnect"
            f"?appid={cfg['corp_id']}"
            f"&agentid={cfg['agent_id']}"
            f"&redirect_uri={cfg['redirect_uri']}"
            f"&state=marketplace"
        )

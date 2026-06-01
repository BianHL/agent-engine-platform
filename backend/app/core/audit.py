"""Audit log middleware: automatically records all write operations."""
from __future__ import annotations

import json
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# HTTP methods that trigger audit logging
AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Path prefixes to exclude from audit (health checks, internal)
EXCLUDE_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}


def _extract_resource_info(path: str, method: str) -> tuple[str, str | None]:
    """Extract resource type and ID from the request path.

    Returns (resource_type, resource_id).
    """
    parts = [p for p in path.strip("/").split("/") if p]
    # Remove 'api' and 'v1' prefix
    if parts and parts[0] == "api":
        parts = parts[2:]  # skip api/v1

    if not parts:
        return "unknown", None

    # Map method to action
    resource_type = parts[0]  # e.g., agents, knowledge, workflows

    # Try to extract resource ID from path
    resource_id = None
    if len(parts) >= 2:
        # Check if second part looks like a UUID or ID
        candidate = parts[1]
        if candidate not in ("bases", "configs", "providers", "status", "executions", "messages"):
            resource_id = candidate

    return resource_type, resource_id


def _get_action(method: str, path: str) -> str:
    """Map HTTP method to audit action."""
    if method == "DELETE":
        return "delete"
    if method in ("PUT", "PATCH"):
        return "update"
    # POST - could be create or execute
    if "/execute" in path or "/run" in path or "/publish" in path:
        return "execute"
    if "/register" in path:
        return "create"
    return "create"


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all write operations to the operation_logs table."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only audit write methods
        if request.method not in AUDIT_METHODS:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(p) for p in EXCLUDE_PATHS):
            return await call_next(request)

        # Skip auth endpoints (login/register don't need audit)
        if "/auth/" in path:
            return await call_next(request)

        # Execute the request first
        response = await call_next(request)

        # Only audit successful responses
        if response.status_code >= 400:
            return response

        # Extract info for audit log
        resource_type, resource_id = _extract_resource_info(path, request.method)
        action = _get_action(request.method, path)

        # Get user info from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # Get client IP
        client_ip = request.client.host if request.client else None

        # Try to capture request body (limited)
        details = None
        try:
            body = await request.body()
            if body:
                parsed = json.loads(body)
                # Remove sensitive fields
                for field in ("password", "hashed_password", "token", "secret"):
                    if isinstance(parsed, dict) and field in parsed:
                        parsed[field] = "***"
                details = {"request_body": parsed}
        except Exception as e:
            logger.warning("Failed to parse request body for audit log: %s", e)

        # Write audit log asynchronously (don't block response)
        if tenant_id:
            try:
                await self._write_audit_log(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=client_ip,
                    details=details,
                )
            except Exception as e:
                logger.warning("Failed to write audit log: %s", e)

        return response

    async def _write_audit_log(
        self,
        tenant_id: str,
        user_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        ip_address: str | None,
        details: dict | None,
    ) -> None:
        """Write an audit log entry to the database."""
        from app.core.database import async_session
        from app.models.base import OperationLogModel

        async with async_session() as session:
            log = OperationLogModel(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                details=details,
            )
            session.add(log)
            await session.commit()

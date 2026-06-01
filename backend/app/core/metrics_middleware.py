"""Prometheus metrics collection middleware."""
from __future__ import annotations

import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import record_http_request


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect HTTP request metrics for Prometheus."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics/health endpoints
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Normalize endpoint path (remove IDs for cardinality control)
        path = request.url.path
        # Replace UUIDs with {id}
        normalized = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
        )

        record_http_request(
            method=request.method,
            endpoint=normalized,
            status_code=response.status_code,
            duration=duration,
        )

        return response

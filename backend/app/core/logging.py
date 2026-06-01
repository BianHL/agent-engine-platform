"""Structured JSON logging with sensitive field filtering."""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any

SENSITIVE_FIELDS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "access_token", "refresh_token", "hashed_password",
    "secret_key", "encryption_key", "credit_card", "ssn", "id_card",
})


def _filter_sensitive(data: Any, depth: int = 10) -> Any:
    if depth <= 0:
        return data
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if k.lower() in SENSITIVE_FIELDS else _filter_sensitive(v, depth - 1)
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [_filter_sensitive(item, depth - 1) for item in data]
    return data


class StructuredFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request_id if set by middleware
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = record.tenant_id

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields, filtering sensitive data
        for key in ("method", "path", "status_code", "duration_ms", "user_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def setup_logging():
    """Configure root logger with structured output."""
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

"""Prometheus metrics definitions for AI Marketplace."""
from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram, Info

    # HTTP request metrics
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )

    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Marketplace business metrics
    marketplace_items_total = Gauge(
        "marketplace_items_total",
        "Total marketplace items by status",
        ["status"],
    )

    marketplace_ratings_total = Counter(
        "marketplace_ratings_total",
        "Total marketplace ratings submitted",
        ["score"],
    )

    marketplace_clones_total = Counter(
        "marketplace_clones_total",
        "Total marketplace clones",
    )

    marketplace_reviews_total = Counter(
        "marketplace_reviews_total",
        "Total marketplace review actions",
        ["action"],  # approve/reject
    )

    # LLM metrics
    llm_requests_total = Counter(
        "llm_requests_total",
        "Total LLM API requests",
        ["provider", "model", "status"],
    )

    llm_tokens_total = Counter(
        "llm_tokens_total",
        "Total LLM tokens consumed",
        ["provider", "model", "token_type"],  # prompt/completion
    )

    # System metrics
    active_users = Gauge(
        "active_users",
        "Currently active users",
    )

    HAS_PROMETHEUS = True

except ImportError:
    HAS_PROMETHEUS = False


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record an HTTP request (no-op if prometheus_client not installed)."""
    if not HAS_PROMETHEUS:
        return
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_marketplace_rating(score: int):
    """Record a marketplace rating submission."""
    if not HAS_PROMETHEUS:
        return
    marketplace_ratings_total.labels(score=str(score)).inc()


def record_marketplace_clone():
    """Record a marketplace clone."""
    if not HAS_PROMETHEUS:
        return
    marketplace_clones_total.inc()


def record_marketplace_review(action: str):
    """Record a marketplace review action."""
    if not HAS_PROMETHEUS:
        return
    marketplace_reviews_total.labels(action=action).inc()

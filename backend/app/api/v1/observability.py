"""Observability API endpoints — metrics, traces, errors, alerts, service map.

These endpoints provide dashboard data for the observability page.
Currently returns stub data; will be wired to real telemetry in future.
"""
from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/metrics")
async def get_metrics(
    range: str = Query("1h"),
    start: str = Query(None),
    end: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Return aggregated metrics for the observability dashboard."""
    return {
        "qps": 0,
        "qps_trend": 0,
        "avg_latency": 0,
        "latency_trend": 0,
        "error_rate": 0,
        "error_trend": 0,
        "total_requests": 0,
        "active_services": 0,
        "p50": 0,
        "p90": 0,
        "p99": 0,
        "qps_series": [],
        "latency_series": [],
        "error_series": [],
    }


@router.get("/traces")
async def get_traces(
    range: str = Query("1h"),
    start: str = Query(None),
    end: str = Query(None),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """Return recent request traces."""
    return []


@router.get("/errors")
async def get_errors(
    range: str = Query("1h"),
    start: str = Query(None),
    end: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Return error analysis data."""
    return []


@router.get("/alerts")
async def get_alerts(
    user: dict = Depends(get_current_user),
):
    """Return configured alert rules."""
    return []


@router.get("/service-map")
async def get_service_map(
    user: dict = Depends(get_current_user),
):
    """Return service dependency map."""
    return {"nodes": [], "edges": []}

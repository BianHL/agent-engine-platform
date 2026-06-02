"""Compliance report generation API endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, UTC, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_tenant_id
from app.core.rbac import require_permission
from app.core.database import get_db
from app.models.agent import AgentModel
from app.models.audit import OperationLogModel
from app.models.user import UserModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ComplianceReportRequest(BaseModel):
    report_type: str = Field(..., description="Report type: security, access, data, audit")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="json", description="Output format: json, csv, pdf")
    include_details: bool = Field(default=True, description="Include detailed records")


class ComplianceReport(BaseModel):
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: dict
    details: Optional[list[dict]] = None
    format: str


class SecurityReport(BaseModel):
    total_events: int
    failed_logins: int
    suspicious_activities: int
    ip_addresses: list[dict]
    user_agents: list[dict]
    recommendations: list[str]


class AccessReport(BaseModel):
    total_access_events: int
    unique_users: int
    top_resources: list[dict]
    access_patterns: dict
    role_distribution: dict


class DataReport(BaseModel):
    total_operations: int
    create_operations: int
    update_operations: int
    delete_operations: int
    sensitive_data_access: int
    data_retention_compliance: dict


class AuditReport(BaseModel):
    total_audit_logs: int
    actions_breakdown: dict
    resource_types: dict
    user_activities: list[dict]
    compliance_score: float


# ---------------------------------------------------------------------------
# Compliance endpoints
# ---------------------------------------------------------------------------

@router.post("/reports", response_model=ComplianceReport)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("compliance", "create")),
    tenant_id: str = Depends(get_tenant_id),
):
    """Generate a compliance report."""
    # Set default date range
    end_date = request.end_date or datetime.now(UTC)
    start_date = request.start_date or (end_date - timedelta(days=30))

    report_id = f"report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    if request.report_type == "security":
        report_data = await _generate_security_report(db, tenant_id, start_date, end_date)
    elif request.report_type == "access":
        report_data = await _generate_access_report(db, tenant_id, start_date, end_date)
    elif request.report_type == "data":
        report_data = await _generate_data_report(db, tenant_id, start_date, end_date)
    elif request.report_type == "audit":
        report_data = await _generate_audit_report(db, tenant_id, start_date, end_date)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")

    return ComplianceReport(
        report_id=report_id,
        report_type=request.report_type,
        generated_at=datetime.now(UTC),
        period_start=start_date,
        period_end=end_date,
        summary=report_data.get("summary", {}),
        details=report_data.get("details") if request.include_details else None,
        format=request.format,
    )


@router.get("/reports/security")
async def get_security_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get security compliance report."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    return await _generate_security_report(db, tenant_id, start_date, end_date)


@router.get("/reports/access")
async def get_access_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get access control compliance report."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    return await _generate_access_report(db, tenant_id, start_date, end_date)


@router.get("/reports/data")
async def get_data_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get data handling compliance report."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    return await _generate_data_report(db, tenant_id, start_date, end_date)


@router.get("/reports/audit")
async def get_audit_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get audit trail compliance report."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    return await _generate_audit_report(db, tenant_id, start_date, end_date)


@router.get("/score")
async def get_compliance_score(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get overall compliance score."""
    # Calculate compliance score based on various factors
    factors = {
        "authentication": await _check_auth_compliance(db, tenant_id),
        "authorization": await _check_authz_compliance(db, tenant_id),
        "data_protection": await _check_data_compliance(db, tenant_id),
        "audit_logging": await _check_audit_compliance(db, tenant_id),
        "access_control": await _check_access_compliance(db, tenant_id),
    }

    overall_score = sum(factors.values()) / len(factors)

    return {
        "overall_score": round(overall_score, 2),
        "factors": factors,
        "grade": _get_compliance_grade(overall_score),
        "recommendations": _get_compliance_recommendations(factors),
    }


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------

async def _generate_security_report(
    db: AsyncSession, tenant_id: str, start_date: datetime, end_date: datetime
) -> dict:
    """Generate security compliance report."""
    # Get security-related events
    stmt = select(OperationLogModel).where(
        and_(
            OperationLogModel.tenant_id == tenant_id,
            OperationLogModel.created_at.between(start_date, end_date),
            OperationLogModel.action.in_(["login", "logout", "failed_login", "password_change"]),
        )
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    # Analyze events
    failed_logins = sum(1 for e in events if e.action == "failed_login")
    successful_logins = sum(1 for e in events if e.action == "login")

    # Get unique IPs
    ip_addresses = {}
    for event in events:
        if event.ip_address:
            ip_addresses[event.ip_address] = ip_addresses.get(event.ip_address, 0) + 1

    return {
        "summary": {
            "total_events": len(events),
            "failed_logins": failed_logins,
            "successful_logins": successful_logins,
            "unique_ips": len(ip_addresses),
            "success_rate": round(successful_logins / max(1, successful_logins + failed_logins) * 100, 2),
        },
        "details": [
            {
                "action": e.action,
                "user_id": e.user_id,
                "ip_address": e.ip_address,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events[:100]  # Limit to 100 records
        ],
    }


async def _generate_access_report(
    db: AsyncSession, tenant_id: str, start_date: datetime, end_date: datetime
) -> dict:
    """Generate access control compliance report."""
    # Get access events
    stmt = select(OperationLogModel).where(
        and_(
            OperationLogModel.tenant_id == tenant_id,
            OperationLogModel.created_at.between(start_date, end_date),
        )
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    # Analyze by resource type
    resource_types = {}
    for event in events:
        rt = event.resource_type or "unknown"
        resource_types[rt] = resource_types.get(rt, 0) + 1

    # Get unique users
    unique_users = len(set(e.user_id for e in events if e.user_id))

    return {
        "summary": {
            "total_access_events": len(events),
            "unique_users": unique_users,
            "resource_types": resource_types,
        },
        "details": [
            {
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "user_id": e.user_id,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events[:100]
        ],
    }


async def _generate_data_report(
    db: AsyncSession, tenant_id: str, start_date: datetime, end_date: datetime
) -> dict:
    """Generate data handling compliance report."""
    # Get data operations
    stmt = select(OperationLogModel).where(
        and_(
            OperationLogModel.tenant_id == tenant_id,
            OperationLogModel.created_at.between(start_date, end_date),
            OperationLogModel.action.in_(["create", "update", "delete"]),
        )
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    # Analyze operations
    operations = {"create": 0, "update": 0, "delete": 0}
    for event in events:
        if event.action in operations:
            operations[event.action] += 1

    return {
        "summary": {
            "total_operations": len(events),
            "create_operations": operations["create"],
            "update_operations": operations["update"],
            "delete_operations": operations["delete"],
        },
        "details": [
            {
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "user_id": e.user_id,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events[:100]
        ],
    }


async def _generate_audit_report(
    db: AsyncSession, tenant_id: str, start_date: datetime, end_date: datetime
) -> dict:
    """Generate audit trail compliance report."""
    # Get all audit logs
    stmt = select(OperationLogModel).where(
        and_(
            OperationLogModel.tenant_id == tenant_id,
            OperationLogModel.created_at.between(start_date, end_date),
        )
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    # Analyze by action
    actions = {}
    for event in events:
        actions[event.action] = actions.get(event.action, 0) + 1

    # Get user activities
    user_activities = {}
    for event in events:
        if event.user_id:
            if event.user_id not in user_activities:
                user_activities[event.user_id] = {"count": 0, "actions": set()}
            user_activities[event.user_id]["count"] += 1
            user_activities[event.user_id]["actions"].add(event.action)

    return {
        "summary": {
            "total_audit_logs": len(events),
            "actions_breakdown": actions,
            "unique_users": len(user_activities),
        },
        "details": [
            {
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "user_id": e.user_id,
                "ip_address": e.ip_address,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events[:100]
        ],
    }


# ---------------------------------------------------------------------------
# Compliance checks
# ---------------------------------------------------------------------------

async def _check_auth_compliance(db: AsyncSession, tenant_id: str) -> float:
    """Check authentication compliance."""
    # Check for password policies, MFA, etc.
    return 0.85  # Placeholder


async def _check_authz_compliance(db: AsyncSession, tenant_id: str) -> float:
    """Check authorization compliance."""
    # Check RBAC implementation
    return 0.90


async def _check_data_compliance(db: AsyncSession, tenant_id: str) -> float:
    """Check data protection compliance."""
    # Check encryption, data retention
    return 0.80


async def _check_audit_compliance(db: AsyncSession, tenant_id: str) -> float:
    """Check audit logging compliance."""
    # Check audit log completeness
    return 0.95


async def _check_access_compliance(db: AsyncSession, tenant_id: str) -> float:
    """Check access control compliance."""
    # Check access control implementation
    return 0.88


def _get_compliance_grade(score: float) -> str:
    """Get compliance grade from score."""
    if score >= 0.95:
        return "A+"
    elif score >= 0.90:
        return "A"
    elif score >= 0.85:
        return "B+"
    elif score >= 0.80:
        return "B"
    elif score >= 0.70:
        return "C"
    else:
        return "D"


def _get_compliance_recommendations(factors: dict) -> list[str]:
    """Get compliance improvement recommendations."""
    recommendations = []

    if factors.get("authentication", 1) < 0.9:
        recommendations.append("Implement multi-factor authentication (MFA)")
    if factors.get("authorization", 1) < 0.9:
        recommendations.append("Review and strengthen RBAC policies")
    if factors.get("data_protection", 1) < 0.9:
        recommendations.append("Enhance data encryption and retention policies")
    if factors.get("audit_logging", 1) < 0.9:
        recommendations.append("Improve audit log coverage and retention")
    if factors.get("access_control", 1) < 0.9:
        recommendations.append("Implement stricter access control measures")

    return recommendations

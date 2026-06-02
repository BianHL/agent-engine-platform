"""Agent version management and A/B testing API endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_tenant_id
from app.core.rbac import require_permission
from app.core.database import get_db
from app.models.base import AgentModel, AgentVersionModel, ABTestModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-versions", tags=["Agent Versions"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VersionCreate(BaseModel):
    version: str = Field(..., description="Version identifier (e.g., 1.0.0, v2-beta)")
    system_prompt: str = Field(..., description="System prompt for this version")
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None
    is_active: bool = Field(default=False, description="Set as active version")


class VersionResponse(BaseModel):
    id: str
    agent_id: str
    version: str
    system_prompt: str
    model_provider: Optional[str]
    model_name: Optional[str]
    config: Optional[dict]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    created_by: str


class ABTestCreate(BaseModel):
    name: str = Field(..., description="A/B test name")
    description: Optional[str] = None
    version_a_id: str = Field(..., description="Version A ID (control)")
    version_b_id: str = Field(..., description="Version B ID (variant)")
    traffic_split: float = Field(default=0.5, ge=0.1, le=0.9, description="Traffic to version B (0.1-0.9)")
    metric: str = Field(default="satisfaction", description="Primary metric to optimize")
    duration_hours: int = Field(default=24, ge=1, le=720, description="Test duration in hours")
    min_samples: int = Field(default=100, ge=10, description="Minimum samples per variant")


class ABTestResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    description: Optional[str]
    version_a_id: str
    version_b_id: str
    traffic_split: float
    metric: str
    duration_hours: int
    min_samples: int
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    results: Optional[dict]
    created_at: datetime


class ABTestResults(BaseModel):
    test_id: str
    status: str
    version_a: dict
    version_b: dict
    winner: Optional[str]
    confidence: Optional[float]
    recommendation: Optional[str]


# ---------------------------------------------------------------------------
# Version endpoints
# ---------------------------------------------------------------------------

@router.get("/{agent_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """List all versions for an agent."""
    # Verify agent exists and belongs to tenant
    stmt = select(AgentModel).where(
        and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    stmt = (
        select(AgentVersionModel)
        .where(AgentVersionModel.agent_id == agent_id)
        .order_by(desc(AgentVersionModel.created_at))
    )
    result = await db.execute(stmt)
    versions = result.scalars().all()

    return [
        VersionResponse(
            id=v.id,
            agent_id=v.agent_id,
            version=v.version,
            system_prompt=v.system_prompt,
            model_provider=v.model_provider,
            model_name=v.model_name,
            config=v.config,
            description=v.description,
            is_active=v.is_active,
            created_at=v.created_at,
            created_by=v.created_by,
        )
        for v in versions
    ]


@router.post("/{agent_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    agent_id: str,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new version for an agent."""
    # Verify agent exists
    stmt = select(AgentModel).where(
        and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check version uniqueness
    stmt = select(AgentVersionModel).where(
        and_(
            AgentVersionModel.agent_id == agent_id,
            AgentVersionModel.version == data.version,
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Version {data.version} already exists")

    # If setting as active, deactivate other versions
    if data.is_active:
        stmt = select(AgentVersionModel).where(
            and_(
                AgentVersionModel.agent_id == agent_id,
                AgentVersionModel.is_active == True,
            )
        )
        result = await db.execute(stmt)
        for v in result.scalars().all():
            v.is_active = False

    version = AgentVersionModel(
        agent_id=agent_id,
        version=data.version,
        system_prompt=data.system_prompt,
        model_provider=data.model_provider or agent.model_provider,
        model_name=data.model_name or agent.model_name,
        config=data.config or {},
        description=data.description,
        is_active=data.is_active,
        created_by=user["id"],
        tenant_id=tenant_id,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return VersionResponse(
        id=version.id,
        agent_id=version.agent_id,
        version=version.version,
        system_prompt=version.system_prompt,
        model_provider=version.model_provider,
        model_name=version.model_name,
        config=version.config,
        description=version.description,
        is_active=version.is_active,
        created_at=version.created_at,
        created_by=version.created_by,
    )


@router.put("/{agent_id}/versions/{version_id}/activate", response_model=VersionResponse)
async def activate_version(
    agent_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Activate a specific version."""
    # Get the version
    stmt = select(AgentVersionModel).where(
        and_(
            AgentVersionModel.id == version_id,
            AgentVersionModel.agent_id == agent_id,
            AgentVersionModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Deactivate all versions for this agent
    stmt = select(AgentVersionModel).where(
        and_(
            AgentVersionModel.agent_id == agent_id,
            AgentVersionModel.is_active == True,
        )
    )
    result = await db.execute(stmt)
    for v in result.scalars().all():
        v.is_active = False

    # Activate the target version
    version.is_active = True
    await db.commit()
    await db.refresh(version)

    return VersionResponse(
        id=version.id,
        agent_id=version.agent_id,
        version=version.version,
        system_prompt=version.system_prompt,
        model_provider=version.model_provider,
        model_name=version.model_name,
        config=version.config,
        description=version.description,
        is_active=version.is_active,
        created_at=version.created_at,
        created_by=version.created_by,
    )


@router.delete("/{agent_id}/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    agent_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Delete a version (cannot delete active version)."""
    stmt = select(AgentVersionModel).where(
        and_(
            AgentVersionModel.id == version_id,
            AgentVersionModel.agent_id == agent_id,
            AgentVersionModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.is_active:
        raise HTTPException(status_code=400, detail="Cannot delete active version")

    await db.delete(version)
    await db.commit()


# ---------------------------------------------------------------------------
# A/B Test endpoints
# ---------------------------------------------------------------------------

@router.get("/{agent_id}/ab-tests", response_model=list[ABTestResponse])
async def list_ab_tests(
    agent_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """List A/B tests for an agent."""
    filters = [ABTestModel.agent_id == agent_id, ABTestModel.tenant_id == tenant_id]
    if status_filter:
        filters.append(ABTestModel.status == status_filter)

    stmt = select(ABTestModel).where(and_(*filters)).order_by(desc(ABTestModel.created_at))
    result = await db.execute(stmt)
    tests = result.scalars().all()

    return [
        ABTestResponse(
            id=t.id,
            agent_id=t.agent_id,
            name=t.name,
            description=t.description,
            version_a_id=t.version_a_id,
            version_b_id=t.version_b_id,
            traffic_split=t.traffic_split,
            metric=t.metric,
            duration_hours=t.duration_hours,
            min_samples=t.min_samples,
            status=t.status,
            started_at=t.started_at,
            ended_at=t.ended_at,
            results=t.results,
            created_at=t.created_at,
        )
        for t in tests
    ]


@router.post("/{agent_id}/ab-tests", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    agent_id: str,
    data: ABTestCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new A/B test."""
    # Verify agent exists
    stmt = select(AgentModel).where(
        and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    # Verify both versions exist
    for version_id in [data.version_a_id, data.version_b_id]:
        stmt = select(AgentVersionModel).where(
            and_(
                AgentVersionModel.id == version_id,
                AgentVersionModel.agent_id == agent_id,
            )
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

    # Check for active tests
    stmt = select(ABTestModel).where(
        and_(
            ABTestModel.agent_id == agent_id,
            ABTestModel.status == "running",
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An active A/B test already exists")

    test = ABTestModel(
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        version_a_id=data.version_a_id,
        version_b_id=data.version_b_id,
        traffic_split=data.traffic_split,
        metric=data.metric,
        duration_hours=data.duration_hours,
        min_samples=data.min_samples,
        status="created",
        tenant_id=tenant_id,
        created_by=user["id"],
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return ABTestResponse(
        id=test.id,
        agent_id=test.agent_id,
        name=test.name,
        description=test.description,
        version_a_id=test.version_a_id,
        version_b_id=test.version_b_id,
        traffic_split=test.traffic_split,
        metric=test.metric,
        duration_hours=test.duration_hours,
        min_samples=test.min_samples,
        status=test.status,
        started_at=test.started_at,
        ended_at=test.ended_at,
        results=test.results,
        created_at=test.created_at,
    )


@router.post("/{agent_id}/ab-tests/{test_id}/start", response_model=ABTestResponse)
async def start_ab_test(
    agent_id: str,
    test_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Start an A/B test."""
    stmt = select(ABTestModel).where(
        and_(
            ABTestModel.id == test_id,
            ABTestModel.agent_id == agent_id,
            ABTestModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")

    if test.status != "created":
        raise HTTPException(status_code=400, detail=f"Cannot start test with status: {test.status}")

    test.status = "running"
    test.started_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(test)

    return ABTestResponse(
        id=test.id,
        agent_id=test.agent_id,
        name=test.name,
        description=test.description,
        version_a_id=test.version_a_id,
        version_b_id=test.version_b_id,
        traffic_split=test.traffic_split,
        metric=test.metric,
        duration_hours=test.duration_hours,
        min_samples=test.min_samples,
        status=test.status,
        started_at=test.started_at,
        ended_at=test.ended_at,
        results=test.results,
        created_at=test.created_at,
    )


@router.post("/{agent_id}/ab-tests/{test_id}/stop", response_model=ABTestResponse)
async def stop_ab_test(
    agent_id: str,
    test_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Stop an A/B test and calculate results."""
    stmt = select(ABTestModel).where(
        and_(
            ABTestModel.id == test_id,
            ABTestModel.agent_id == agent_id,
            ABTestModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")

    if test.status != "running":
        raise HTTPException(status_code=400, detail=f"Cannot stop test with status: {test.status}")

    test.status = "completed"
    test.ended_at = datetime.now(UTC)

    # Calculate results (simplified - in production, aggregate from metrics)
    test.results = {
        "version_a": {"samples": 0, "avg_score": 0},
        "version_b": {"samples": 0, "avg_score": 0},
        "winner": None,
        "confidence": 0,
    }

    await db.commit()
    await db.refresh(test)

    return ABTestResponse(
        id=test.id,
        agent_id=test.agent_id,
        name=test.name,
        description=test.description,
        version_a_id=test.version_a_id,
        version_b_id=test.version_b_id,
        traffic_split=test.traffic_split,
        metric=test.metric,
        duration_hours=test.duration_hours,
        min_samples=test.min_samples,
        status=test.status,
        started_at=test.started_at,
        ended_at=test.ended_at,
        results=test.results,
        created_at=test.created_at,
    )


@router.get("/{agent_id}/ab-tests/{test_id}/results", response_model=ABTestResults)
async def get_ab_test_results(
    agent_id: str,
    test_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get A/B test results with statistical analysis."""
    stmt = select(ABTestModel).where(
        and_(
            ABTestModel.id == test_id,
            ABTestModel.agent_id == agent_id,
            ABTestModel.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")

    if test.status not in ["completed", "stopped"]:
        raise HTTPException(status_code=400, detail="Test not completed yet")

    results = test.results or {}
    return ABTestResults(
        test_id=test.id,
        status=test.status,
        version_a=results.get("version_a", {}),
        version_b=results.get("version_b", {}),
        winner=results.get("winner"),
        confidence=results.get("confidence"),
        recommendation=results.get("recommendation"),
    )

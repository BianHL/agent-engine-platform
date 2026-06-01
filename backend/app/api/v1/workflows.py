"""Workflow management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.base import WorkflowExecutionModel, WorkflowModel
from app.platform.workflow_service.workflow_service import (
    WorkflowExecutionService,
    WorkflowVersionService,
)
from app.schemas.api import (
    CreateWorkflowRequest,
    PaginatedResponse,
    RunWorkflowRequest,
    StatusResponse,
    UpdateWorkflowRequest,
    WorkflowExecutionResponse,
    WorkflowResponse)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/")
async def list_workflows(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List workflows for the current tenant."""
    tenant_id = user["tenant_id"]

    count_result = await db.execute(
        select(func.count()).where(WorkflowModel.tenant_id == tenant_id)
    )
    total = count_result.scalar()

    stmt = (
        select(WorkflowModel)
        .where(WorkflowModel.tenant_id == tenant_id)
        .order_by(WorkflowModel.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    workflows = result.scalars().all()

    return {
        "items": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status,
                "version": w.version,
                "dag_config": w.dag_config or {},
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None,
            }
            for w in workflows
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: CreateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("workflow", "create"))):
    """Create a new workflow."""
    workflow = WorkflowModel(
        tenant_id=user["tenant_id"],
        name=body.name,
        description=body.description,
        agent_id=body.agent_id,
        dag_config=body.dag_config)
    db.add(workflow)
    await db.flush()
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "version": workflow.version,
        "dag_config": workflow.dag_config or {},
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get a workflow by ID."""
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "version": workflow.version,
        "dag_config": workflow.dag_config or {},
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: UpdateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("workflow", "update"))):
    """Update a workflow. Auto-increments version when dag_config changes."""
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if body.name is not None:
        workflow.name = body.name
    if body.description is not None:
        workflow.description = body.description

    # Auto-version when dag_config changes
    if body.dag_config is not None:
        version_svc = WorkflowVersionService(db)
        # Snapshot current config before overwriting
        await version_svc.snapshot_version(
            workflow_id=workflow_id,
            version=workflow.version,
            dag_config=workflow.dag_config or {},
            created_by=user.get("user_id"),
        )
        workflow.version = workflow.version + 1
        workflow.dag_config = body.dag_config

    await db.flush()
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "version": workflow.version,
        "dag_config": workflow.dag_config or {},
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("workflow", "delete"))):
    """Delete a workflow."""
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(workflow)
    await db.flush()
    return None


@router.post("/{workflow_id}/run", status_code=status.HTTP_201_CREATED)
async def run_workflow(
    workflow_id: str,
    body: RunWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("workflow", "execute"))):
    """Execute a workflow, creating a new execution record."""
    # Verify workflow exists and belongs to tenant
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    svc = WorkflowExecutionService(db)
    execution = await svc.start_execution(
        workflow_id=workflow_id,
        tenant_id=user["tenant_id"],
        variables=body.variables)
    return execution


@router.get("/{workflow_id}/executions")
async def list_executions(
    workflow_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List executions for a workflow."""
    # Verify workflow exists
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    count_result = await db.execute(
        select(func.count()).where(
            WorkflowExecutionModel.workflow_id == workflow_id,
            WorkflowExecutionModel.tenant_id == user["tenant_id"])
    )
    total = count_result.scalar()

    stmt = (
        select(WorkflowExecutionModel)
        .where(
            WorkflowExecutionModel.workflow_id == workflow_id,
            WorkflowExecutionModel.tenant_id == user["tenant_id"])
        .order_by(WorkflowExecutionModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    exec_result = await db.execute(stmt)
    executions = exec_result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "workflow_id": e.workflow_id,
                "status": e.status,
                "node_states": e.node_states or {},
                "variables": e.variables or {},
                "execution_log": e.execution_log or [],
                "error_message": e.error_message,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in executions
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get a workflow execution by ID."""
    svc = WorkflowExecutionService(db)
    execution = await svc.get_execution(execution_id, tenant_id=user["tenant_id"])
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/executions/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Resume a paused or failed workflow execution."""
    svc = WorkflowExecutionService(db)
    try:
        execution = await svc.resume_execution(execution_id, tenant_id=user["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return execution


# ---------------------------------------------------------------------------
# Workflow Version Management
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/versions")
async def list_workflow_versions(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List all versions for a workflow."""
    # Verify workflow exists and belongs to tenant
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    version_svc = WorkflowVersionService(db)
    versions = await version_svc.list_versions(workflow_id)
    return {"items": versions, "total": len(versions)}


@router.get("/{workflow_id}/versions/{version}")
async def get_workflow_version(
    workflow_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get a specific version's DAG config snapshot."""
    # Verify workflow exists and belongs to tenant
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    version_svc = WorkflowVersionService(db)
    ver = await version_svc.get_version(workflow_id, version)
    if not ver:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    return ver


@router.post("/{workflow_id}/versions/{version}/rollback")
async def rollback_workflow_version(
    workflow_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Rollback a workflow to a previous version.

    Snapshots the current config, then restores the target version's config.
    """
    # Verify workflow exists and belongs to tenant
    stmt = select(WorkflowModel).where(
        WorkflowModel.id == workflow_id,
        WorkflowModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    version_svc = WorkflowVersionService(db)
    try:
        restored = await version_svc.rollback_to_version(
            workflow_id=workflow_id,
            version=version,
            user_id=user.get("user_id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return restored

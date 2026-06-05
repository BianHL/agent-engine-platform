"""Evaluation API endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.engines.eval_engine.evaluator import EvaluationEngine
from app.engines.eval_engine.dataset import load_dataset, extract_from_logs
from app.models.base import EvaluationModel, EvaluationRunModel, EvaluationResultModel
from app.schemas.api import (
    CreateEvaluationRequest,
    EvaluationResponse,
    EvaluationResultResponse,
    EvaluationRunResponse,
    PaginatedResponse,
    StatusResponse,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    body: CreateEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("evaluation", "create")),
):
    """Create a new evaluation task."""
    eval_model = EvaluationModel(
        tenant_id=user["tenant_id"],
        name=body.name,
        description=body.description,
        agent_id=body.agent_id,
        dataset=body.dataset or [],
        metrics={"metrics": body.metrics},
        status="draft",
    )
    db.add(eval_model)
    await db.flush()
    return _eval_to_dict(eval_model)


@router.get("/")
async def list_evaluations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List evaluations for the current tenant."""
    offset = (page - 1) * size
    stmt = (
        select(EvaluationModel)
        .where(EvaluationModel.tenant_id == user["tenant_id"])
        .order_by(EvaluationModel.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = (
        select(func.count())
        .select_from(EvaluationModel)
        .where(EvaluationModel.tenant_id == user["tenant_id"])
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    return PaginatedResponse(
        items=[_eval_to_dict(e) for e in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get evaluation detail."""
    eval_model = await _get_eval(db, evaluation_id, user["tenant_id"])
    return _eval_to_dict(eval_model)


@router.post("/{evaluation_id}/run")
async def run_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("evaluation", "create")),
):
    """Execute an evaluation run."""
    eval_model = await _get_eval(db, evaluation_id, user["tenant_id"])

    # Create run record
    run = EvaluationRunModel(
        evaluation_id=evaluation_id,
        tenant_id=user["tenant_id"],
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    # Load dataset
    dataset = eval_model.dataset or []
    if not dataset and eval_model.agent_id:
        # Try extracting from production logs
        dataset = await extract_from_logs(db, eval_model.agent_id, limit=50)

    if not dataset:
        run.status = "failed"
        run.summary = {"error": "No dataset available"}
        run.completed_at = datetime.now(timezone.utc)
        await db.flush()
        raise HTTPException(status_code=400, detail="No dataset available for evaluation")

    # Get metrics list
    metrics_config = eval_model.metrics or {}
    metrics_list = metrics_config.get("metrics", ["faithfulness", "answer_relevancy"])

    # Run evaluation
    engine = EvaluationEngine()
    try:
        summary = await engine.evaluate(dataset, metrics_list)
    except Exception as exc:
        run.status = "failed"
        run.summary = {"error": str(exc)}
        run.completed_at = datetime.now(timezone.utc)
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")

    # Store results
    for result in summary.results:
        eval_result = EvaluationResultModel(
            run_id=run.id,
            test_case_index=result.test_case_index,
            input_text=result.input_text,
            expected_output=result.expected_output,
            actual_output=result.actual_output,
            scores=result.scores,
            latency_ms=result.latency_ms,
        )
        db.add(eval_result)

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    run.summary = {
        "metric_averages": summary.metric_averages,
        "total_cases": len(summary.results),
    }
    eval_model.status = "completed"
    await db.flush()

    return _run_to_dict(run)


@router.get("/{evaluation_id}/runs")
async def list_runs(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List runs for an evaluation."""
    await _get_eval(db, evaluation_id, user["tenant_id"])

    stmt = (
        select(EvaluationRunModel)
        .where(EvaluationRunModel.evaluation_id == evaluation_id)
        .order_by(EvaluationRunModel.created_at.desc())
    )
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [_run_to_dict(r) for r in runs]


@router.get("/runs/{run_id}/results")
async def get_run_results(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get detailed results for a specific run."""
    stmt = select(EvaluationRunModel).where(EvaluationRunModel.id == run_id, EvaluationRunModel.tenant_id == user.get("tenant_id"))
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    results_stmt = (
        select(EvaluationResultModel)
        .where(EvaluationResultModel.run_id == run_id)
        .order_by(EvaluationResultModel.test_case_index)
    )
    results_result = await db.execute(results_stmt)
    results = results_result.scalars().all()

    return {
        "run": _run_to_dict(run),
        "results": [_result_to_dict(r) for r in results],
    }


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("evaluation", "delete")),
):
    """Delete an evaluation and its runs/results."""
    eval_model = await _get_eval(db, evaluation_id, user["tenant_id"])
    await db.delete(eval_model)
    return StatusResponse(status="deleted")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_eval(db: AsyncSession, eval_id: str, tenant_id: str) -> EvaluationModel:
    stmt = select(EvaluationModel).where(
        EvaluationModel.id == eval_id,
        EvaluationModel.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    eval_model = result.scalar_one_or_none()
    if not eval_model:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return eval_model


def _eval_to_dict(e: EvaluationModel) -> dict:
    return {
        "id": e.id,
        "name": e.name,
        "description": e.description,
        "agent_id": e.agent_id,
        "dataset": e.dataset,
        "metrics": e.metrics,
        "status": e.status,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }


def _run_to_dict(r: EvaluationRunModel) -> dict:
    return {
        "id": r.id,
        "evaluation_id": r.evaluation_id,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "summary": r.summary,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _result_to_dict(r: EvaluationResultModel) -> dict:
    return {
        "id": r.id,
        "run_id": r.run_id,
        "test_case_index": r.test_case_index,
        "input_text": r.input_text,
        "expected_output": r.expected_output,
        "actual_output": r.actual_output,
        "scores": r.scores,
        "latency_ms": r.latency_ms,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

"""Evaluation related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CreateEvaluationRequest(BaseModel):
    name: str
    description: str = ""
    agent_id: Optional[str] = None
    dataset: Optional[List[dict]] = None
    metrics: List[str] = ["faithfulness", "answer_relevancy"]


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    dataset: list = []
    metrics: dict = {}
    eval_config: Optional[dict] = None
    status: str
    total_runs: int = 0
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evaluation_id: str
    tenant_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    summary: Dict[str, Any] = {}
    avg_scores: Optional[Dict[str, float]] = None
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    evaluation_id: Optional[str] = None
    test_case_index: int
    input_text: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    scores: Dict[str, Any] = {}
    overall_score: Optional[float] = None
    latency_ms: Optional[int] = None
    token_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

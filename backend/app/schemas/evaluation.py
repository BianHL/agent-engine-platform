"""Evaluation related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CreateEvaluationRequest(BaseModel):
    name: str
    description: str = ""
    agent_id: Optional[str] = None
    dataset: Optional[List[dict]] = None
    metrics: List[str] = ["faithfulness", "answer_relevancy"]


class EvaluationResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class EvaluationRunResponse(BaseModel):
    id: str
    evaluation_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: dict = {}
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvaluationResultResponse(BaseModel):
    id: str
    run_id: str
    test_case_index: int
    input_text: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    scores: dict = {}
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

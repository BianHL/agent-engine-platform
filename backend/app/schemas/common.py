from typing import Any, Optional

from pydantic import BaseModel


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: TokenUsage
    finish_reason: str = "stop"
    raw_response: Optional[dict] = None


class FunctionCallResponse(BaseModel):
    function_name: Optional[str] = None
    arguments: Optional[dict] = None
    content: Optional[str] = None
    raw_response: Optional[dict] = None


class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: dict = {}


class RerankResult(BaseModel):
    document: str
    score: float
    index: int


class ASRResult(BaseModel):
    text: str
    language: str
    duration: float
    confidence: float


class SafetyIssue(BaseModel):
    type: str
    detail: str


class SafetyResult(BaseModel):
    safe: bool
    issues: list[SafetyIssue] = []
    filtered_content: Optional[str] = None


class RAGResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
    confidence: float
    graph_context: Optional[str] = None


class ToolResult(BaseModel):
    success: bool
    output: Any = None
    error: Optional[str] = None


class WorkflowResult(BaseModel):
    status: str
    output: Optional[dict] = None
    execution_log: list[dict] = []


class MemoryContext(BaseModel):
    short_term: list[dict] = []
    long_term: dict = {}
    relevant: list[dict] = []


class Entity(BaseModel):
    name: str
    type: str
    description: str = ""


class Relation(BaseModel):
    from_entity: str
    to_entity: str
    relation_type: str
    description: str = ""


class ProviderEndpoint(BaseModel):
    provider_id: str
    model_name: str
    weight: int = 1
    timeout: int = 30
    healthy: bool = True
    active_connections: int = 0
    cost_per_token: float = 0.0
    avg_latency_ms: int = 0

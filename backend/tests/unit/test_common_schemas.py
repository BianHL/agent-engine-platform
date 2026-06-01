"""Unit tests for common Pydantic schemas"""
import pytest
from app.schemas.common import (
    TokenUsage, LLMResponse, FunctionCallResponse,
    SearchResult, RerankResult, ASRResult,
    SafetyIssue, SafetyResult, RAGResponse,
    ToolResult, WorkflowResult, MemoryContext,
    Entity, Relation, ProviderEndpoint
)


def test_token_usage():
    u = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
    assert u.input_tokens == 100
    assert u.total_tokens == 150


def test_token_usage_defaults():
    u = TokenUsage()
    assert u.input_tokens == 0
    assert u.output_tokens == 0


def test_llm_response():
    r = LLMResponse(content="Hello", model="gpt-4", usage=TokenUsage())
    assert r.content == "Hello"
    assert r.finish_reason == "stop"
    assert r.raw_response is None


def test_function_call_response():
    r = FunctionCallResponse(function_name="get_weather", arguments={"city": "Beijing"})
    assert r.function_name == "get_weather"
    assert r.arguments["city"] == "Beijing"


def test_search_result():
    r = SearchResult(id="1", score=0.95, content="test content")
    assert r.score == 0.95
    assert r.metadata == {}


def test_rerank_result():
    r = RerankResult(document="test doc", score=0.9, index=0)
    assert r.score == 0.9


def test_asr_result():
    r = ASRResult(text="hello world", language="zh", duration=5.0, confidence=0.95)
    assert r.text == "hello world"
    assert r.confidence == 0.95


def test_safety_result():
    r = SafetyResult(safe=True, issues=[], filtered_content=None)
    assert r.safe is True


def test_safety_result_with_issues():
    issue = SafetyIssue(type="injection", detail="detected")
    r = SafetyResult(safe=False, issues=[issue])
    assert r.safe is False
    assert len(r.issues) == 1


def test_rag_response():
    r = RAGResponse(answer="42", sources=[], confidence=0.9)
    assert r.answer == "42"
    assert r.graph_context is None


def test_tool_result():
    r = ToolResult(success=True, output="result")
    assert r.success is True
    assert r.error is None


def test_workflow_result():
    r = WorkflowResult(status="success", output={"key": "value"})
    assert r.status == "success"


def test_memory_context():
    m = MemoryContext(short_term=[], long_term={}, relevant=[])
    assert m.short_term == []


def test_entity():
    e = Entity(name="Python", type="Language", description="Programming language")
    assert e.name == "Python"


def test_relation():
    r = Relation(from_entity="A", to_entity="B", relation_type="RELATED_TO")
    assert r.relation_type == "RELATED_TO"


def test_provider_endpoint():
    ep = ProviderEndpoint(provider_id="p1", model_name="gpt-4o")
    assert ep.weight == 1
    assert ep.healthy is True
    assert ep.timeout == 30


def test_provider_endpoint_custom():
    ep = ProviderEndpoint(provider_id="p1", model_name="gpt-4o", weight=5, timeout=60, healthy=False)
    assert ep.weight == 5
    assert ep.timeout == 60
    assert ep.healthy is False

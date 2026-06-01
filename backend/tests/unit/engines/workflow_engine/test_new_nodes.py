"""Unit tests for new workflow node types: TEMPLATE, QUESTION_CLASSIFIER,
PARAMETER_EXTRACTOR, VARIABLE_AGGREGATOR, VARIABLE_ASSIGNER."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.engines.workflow_engine.workflow import (
    DAG, WorkflowNode, WorkflowEdge, WorkflowState, WorkflowEngine,
    NodeType, NodeStatus,
)


# === Fixtures ===

@pytest.fixture
def engine():
    return WorkflowEngine()


@pytest.fixture
def state():
    s = WorkflowState()
    s.set_var("name", "Alice")
    s.set_var("items", [1, 2, 3])
    s.set_var("counter", 5)
    s.set_var("config", {"debug": True, "verbose": False})
    s.set_var("question", "How do I reset my password?")
    s.set_var("text", "My name is John and I am 30 years old")
    return s


def _make_mock_llm(content: str):
    mock = AsyncMock()
    response = MagicMock()
    response.content = content
    response.usage.dict.return_value = {}
    mock.chat.return_value = response
    return mock


# === TEMPLATE Node Tests ===

@pytest.mark.asyncio
async def test_template_basic(engine, state):
    node = WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": "Hello, {{ name }}!"},
    )
    result = await engine._execute_template(node, state)
    assert result["rendered"] == "Hello, Alice!"


@pytest.mark.asyncio
async def test_template_with_variables_key(engine, state):
    node = WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": "Items: {{ value | join(', ') }}", "variables_key": "items"},
    )
    result = await engine._execute_template(node, state)
    assert result["rendered"] == "Items: 1, 2, 3"


@pytest.mark.asyncio
async def test_template_empty(engine, state):
    node = WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": ""},
    )
    result = await engine._execute_template(node, state)
    assert result["rendered"] == ""


@pytest.mark.asyncio
async def test_template_complex(engine, state):
    state.set_var("users", [{"name": "Alice"}, {"name": "Bob"}])
    node = WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": "{% for u in users %}{{ u.name }} {% endfor %}"},
    )
    result = await engine._execute_template(node, state)
    assert result["rendered"] == "Alice Bob "


@pytest.mark.asyncio
async def test_template_missing_var(engine):
    state = WorkflowState()
    node = WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": "Hello, {{ missing }}!"},
    )
    result = await engine._execute_template(node, state)
    assert result["rendered"] == "Hello, !"


# === QUESTION_CLASSIFIER Node Tests ===

@pytest.mark.asyncio
async def test_question_classifier_success(engine, state):
    engine.set_llm_adapter(_make_mock_llm("technical"))
    node = WorkflowNode(
        id="qc1",
        type=NodeType.QUESTION_CLASSIFIER,
        config={
            "categories": ["billing", "technical", "general"],
            "input_key": "question",
        },
    )
    result = await engine._execute_question_classifier(node, state)
    assert result["category"] == "technical"
    assert result["confidence"] == 1.0


@pytest.mark.asyncio
async def test_question_classifier_invalid_response(engine, state):
    engine.set_llm_adapter(_make_mock_llm("unknown_category"))
    node = WorkflowNode(
        id="qc1",
        type=NodeType.QUESTION_CLASSIFIER,
        config={
            "categories": ["billing", "technical", "general"],
            "input_key": "question",
        },
    )
    result = await engine._execute_question_classifier(node, state)
    assert result["category"] == "billing"  # defaults to first
    assert result["confidence"] == 0.5


@pytest.mark.asyncio
async def test_question_classifier_no_adapter(state):
    engine = WorkflowEngine()
    node = WorkflowNode(
        id="qc1",
        type=NodeType.QUESTION_CLASSIFIER,
        config={
            "categories": ["billing", "technical"],
            "input_key": "question",
        },
    )
    result = await engine._execute_question_classifier(node, state)
    assert result["category"] == "billing"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_question_classifier_empty_input(engine):
    state = WorkflowState()
    engine.set_llm_adapter(_make_mock_llm("technical"))
    node = WorkflowNode(
        id="qc1",
        type=NodeType.QUESTION_CLASSIFIER,
        config={
            "categories": ["billing", "technical"],
            "input_key": "question",
        },
    )
    result = await engine._execute_question_classifier(node, state)
    assert result["category"] == "billing"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_question_classifier_llm_error(engine, state):
    mock = AsyncMock()
    mock.chat.side_effect = Exception("LLM error")
    engine.set_llm_adapter(mock)
    node = WorkflowNode(
        id="qc1",
        type=NodeType.QUESTION_CLASSIFIER,
        config={
            "categories": ["billing", "technical"],
            "input_key": "question",
        },
    )
    result = await engine._execute_question_classifier(node, state)
    assert result["category"] == "billing"
    assert result["confidence"] == 0.0


# === PARAMETER_EXTRACTOR Node Tests ===

@pytest.mark.asyncio
async def test_parameter_extractor_success(engine, state):
    import json
    engine.set_llm_adapter(_make_mock_llm(json.dumps({"name": "John", "age": 30})))
    node = WorkflowNode(
        id="pe1",
        type=NodeType.PARAMETER_EXTRACTOR,
        config={
            "input_key": "text",
            "parameters_schema": {"name": "string", "age": "integer"},
        },
    )
    result = await engine._execute_parameter_extractor(node, state)
    assert result["parameters"] == {"name": "John", "age": 30}


@pytest.mark.asyncio
async def test_parameter_extractor_markdown_response(engine, state):
    import json
    json_str = json.dumps({"name": "John", "age": 30})
    engine.set_llm_adapter(_make_mock_llm(f"```json\n{json_str}\n```"))
    node = WorkflowNode(
        id="pe1",
        type=NodeType.PARAMETER_EXTRACTOR,
        config={
            "input_key": "text",
            "parameters_schema": {"name": "string", "age": "integer"},
        },
    )
    result = await engine._execute_parameter_extractor(node, state)
    assert result["parameters"] == {"name": "John", "age": 30}


@pytest.mark.asyncio
async def test_parameter_extractor_invalid_json(engine, state):
    engine.set_llm_adapter(_make_mock_llm("not valid json"))
    node = WorkflowNode(
        id="pe1",
        type=NodeType.PARAMETER_EXTRACTOR,
        config={
            "input_key": "text",
            "parameters_schema": {"name": "string", "age": "integer"},
        },
    )
    result = await engine._execute_parameter_extractor(node, state)
    assert result["parameters"] == {"name": None, "age": None}


@pytest.mark.asyncio
async def test_parameter_extractor_no_adapter(state):
    engine = WorkflowEngine()
    node = WorkflowNode(
        id="pe1",
        type=NodeType.PARAMETER_EXTRACTOR,
        config={
            "input_key": "text",
            "parameters_schema": {"name": "string", "age": "integer"},
        },
    )
    result = await engine._execute_parameter_extractor(node, state)
    assert result["parameters"] == {"name": None, "age": None}


@pytest.mark.asyncio
async def test_parameter_extractor_empty_input(engine):
    state = WorkflowState()
    engine.set_llm_adapter(_make_mock_llm("{}"))
    node = WorkflowNode(
        id="pe1",
        type=NodeType.PARAMETER_EXTRACTOR,
        config={
            "input_key": "text",
            "parameters_schema": {"name": "string"},
        },
    )
    result = await engine._execute_parameter_extractor(node, state)
    assert result["parameters"] == {"name": None}


# === VARIABLE_AGGREGATOR Node Tests ===

@pytest.mark.asyncio
async def test_variable_aggregator_all_present(engine, state):
    state.set_var("result_a", "hello")
    state.set_var("result_b", 42)
    node = WorkflowNode(
        id="agg1",
        type=NodeType.VARIABLE_AGGREGATOR,
        config={
            "branches": [
                {"variable": "result_a", "default": None},
                {"variable": "result_b", "default": 0},
            ],
        },
    )
    result = await engine._execute_variable_aggregator(node, state)
    assert result == {"result_a": "hello", "result_b": 42}


@pytest.mark.asyncio
async def test_variable_aggregator_with_defaults(engine):
    state = WorkflowState()
    node = WorkflowNode(
        id="agg1",
        type=NodeType.VARIABLE_AGGREGATOR,
        config={
            "branches": [
                {"variable": "missing_a", "default": "fallback"},
                {"variable": "missing_b", "default": 0},
            ],
        },
    )
    result = await engine._execute_variable_aggregator(node, state)
    assert result == {"missing_a": "fallback", "missing_b": 0}


@pytest.mark.asyncio
async def test_variable_aggregator_empty_branches(engine, state):
    node = WorkflowNode(
        id="agg1",
        type=NodeType.VARIABLE_AGGREGATOR,
        config={"branches": []},
    )
    result = await engine._execute_variable_aggregator(node, state)
    assert result == {}


# === VARIABLE_ASSIGNER Node Tests ===

@pytest.mark.asyncio
async def test_variable_assigner_set_direct(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "counter", "value": 10, "operation": "set"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"counter": 10}
    assert state.get_var("counter") == 10


@pytest.mark.asyncio
async def test_variable_assigner_set_expression(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "counter", "value": "$counter + 1", "operation": "set"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"counter": 6}
    assert state.get_var("counter") == 6


@pytest.mark.asyncio
async def test_variable_assigner_append_to_list(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "items", "value": 4, "operation": "append"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"items": [1, 2, 3, 4]}
    assert state.get_var("items") == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_variable_assigner_append_to_non_list(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "counter", "value": 10, "operation": "append"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"counter": [5, 10]}
    assert state.get_var("counter") == [5, 10]


@pytest.mark.asyncio
async def test_variable_assigner_append_to_none(engine):
    state = WorkflowState()
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "new_list", "value": "item", "operation": "append"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"new_list": ["item"]}
    assert state.get_var("new_list") == ["item"]


@pytest.mark.asyncio
async def test_variable_assigner_merge_dicts(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "config", "value": {"verbose": True, "level": 5}, "operation": "merge"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"config": {"debug": True, "verbose": True, "level": 5}}
    assert state.get_var("config") == {"debug": True, "verbose": True, "level": 5}


@pytest.mark.asyncio
async def test_variable_assigner_merge_none(engine):
    state = WorkflowState()
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "data", "value": {"key": "val"}, "operation": "merge"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"] == {"data": {"key": "val"}}
    assert state.get_var("data") == {"key": "val"}


@pytest.mark.asyncio
async def test_variable_assigner_unknown_operation(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "x", "value": 1, "operation": "invalid"},
            ],
        },
    )
    with pytest.raises(ValueError, match="Unknown operation"):
        await engine._execute_variable_assigner(node, state)


@pytest.mark.asyncio
async def test_variable_assigner_multiple_assignments(engine, state):
    node = WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "counter", "value": "$counter * 2", "operation": "set"},
                {"variable": "items", "value": 99, "operation": "append"},
                {"variable": "config", "value": {"new_key": "new_val"}, "operation": "merge"},
            ],
        },
    )
    result = await engine._execute_variable_assigner(node, state)
    assert result["assigned"]["counter"] == 10
    assert result["assigned"]["items"] == [1, 2, 3, 99]
    assert result["assigned"]["config"]["new_key"] == "new_val"
    assert state.get_var("counter") == 10


# === Integration Tests ===

@pytest.mark.asyncio
async def test_template_in_dag(engine):
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="t1",
        type=NodeType.TEMPLATE,
        config={"template": "Welcome {{ user }}!"},
    ))
    result = await engine.execute(dag, initial_vars={"user": "Bob"})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_variable_assigner_in_dag(engine):
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="va1",
        type=NodeType.VARIABLE_ASSIGNER,
        config={
            "assignments": [
                {"variable": "x", "value": "$x + 10", "operation": "set"},
            ],
        },
    ))
    result = await engine.execute(dag, initial_vars={"x": 5})
    assert result["status"] == "success"
    assert result["output"]["x"] == 15


@pytest.mark.asyncio
async def test_variable_aggregator_in_dag(engine):
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="agg1",
        type=NodeType.VARIABLE_AGGREGATOR,
        config={
            "branches": [
                {"variable": "a", "default": 0},
                {"variable": "b", "default": 0},
            ],
        },
    ))
    result = await engine.execute(dag, initial_vars={"a": 10, "b": 20})
    assert result["status"] == "success"

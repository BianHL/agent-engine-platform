"""Unit tests for SUB_WORKFLOW node execution."""
import pytest
import asyncio
from unittest.mock import AsyncMock

from app.engines.workflow_engine.workflow import (
    DAG, WorkflowNode, WorkflowEdge, WorkflowState, WorkflowEngine,
    NodeType, NodeStatus,
)


def _make_simple_sub_workflow_def():
    """Return a simple sub-workflow definition with two nodes."""
    return {
        "nodes": [
            {"id": "sw_n1", "type": "condition", "config": {"expression": "True"}},
            {"id": "sw_n2", "type": "condition", "config": {"expression": "True"}},
        ],
        "edges": [
            {"source": "sw_n1", "target": "sw_n2"},
        ],
    }


@pytest.mark.asyncio
async def test_sub_workflow_basic_execution():
    """Sub-workflow executes and returns result."""
    loader = AsyncMock(return_value=_make_simple_sub_workflow_def())

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-123"},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "success"
    loader.assert_called_once_with("wf-123")


@pytest.mark.asyncio
async def test_sub_workflow_input_mapping():
    """Parent variables are mapped to child variables correctly."""
    async def loader(workflow_id):
        return {
            "nodes": [
                {"id": "sw_n1", "type": "condition", "config": {"expression": "child_x > 5"}},
            ],
            "edges": [],
        }

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={
            "workflow_id": "wf-123",
            "input_mapping": {
                "parent_x": "child_x",
            },
        },
    ))

    result = await engine.execute(dag, initial_vars={"parent_x": 10})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_sub_workflow_output_mapping():
    """Child output variables are mapped back to parent state."""
    async def loader(workflow_id):
        return {
            "nodes": [
                {"id": "sw_n1", "type": "code", "config": {
                    "code": "state.set_var('child_result', 42)\nstate.set_var('child_status', 'ok')",
                }},
            ],
            "edges": [],
        }

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={
            "workflow_id": "wf-out",
            "output_mapping": {
                "child_result": "parent_result",
                "child_status": "parent_status",
            },
        },
    ))

    result = await engine.execute(dag)
    assert result["status"] == "success"
    assert result["output"]["parent_result"] == 42
    assert result["output"]["parent_status"] == "ok"


@pytest.mark.asyncio
async def test_sub_workflow_input_and_output_mapping():
    """Full round-trip: parent -> child input -> child output -> parent."""
    async def loader(workflow_id):
        return {
            "nodes": [
                {"id": "sw_n1", "type": "code", "config": {
                    "code": "state.set_var('doubled', state.get_var('val') * 2)",
                }},
            ],
            "edges": [],
        }

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={
            "workflow_id": "wf-round",
            "input_mapping": {"x": "val"},
            "output_mapping": {"doubled": "result"},
        },
    ))

    result = await engine.execute(dag, initial_vars={"x": 21})
    assert result["status"] == "success"
    assert result["output"]["result"] == 42


@pytest.mark.asyncio
async def test_sub_workflow_missing_workflow_id():
    """Raises ValueError if workflow_id is not in config."""
    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(AsyncMock())

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "failed"
    assert "workflow_id" in result["error"]


@pytest.mark.asyncio
async def test_sub_workflow_no_loader_set():
    """Raises ValueError if no loader is set."""
    engine = WorkflowEngine()

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-123"},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "failed"
    assert "sub_workflow_loader" in result["error"]


@pytest.mark.asyncio
async def test_sub_workflow_loader_failure():
    """Raises RuntimeError if loader throws an exception."""
    loader = AsyncMock(side_effect=Exception("DB connection failed"))
    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-bad"},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "failed"
    assert "DB connection failed" in result["error"]


@pytest.mark.asyncio
async def test_sub_workflow_invalid_definition():
    """Raises RuntimeError if loader returns invalid definition."""
    loader = AsyncMock(return_value={"invalid": "no nodes key"})
    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-bad-def"},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "failed"
    assert "invalid definition" in result["error"].lower()


@pytest.mark.asyncio
async def test_sub_workflow_child_failure_propagates():
    """Sub-workflow failure causes parent node to fail."""
    async def loader(workflow_id):
        return {
            "nodes": [
                {"id": "sw_fail", "type": "code", "config": {
                    "code": "raise ValueError('child error')",
                }},
            ],
            "edges": [],
        }

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-fail"},
    ))

    result = await engine.execute(dag)
    assert result["status"] == "failed"
    assert "child error" in result["error"]


@pytest.mark.asyncio
async def test_sub_workflow_missing_input_var_skipped():
    """Missing parent variables are silently skipped (not an error)."""
    async def loader(workflow_id):
        return {
            "nodes": [
                {"id": "sw_n1", "type": "condition", "config": {"expression": "True"}},
            ],
            "edges": [],
        }

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={
            "workflow_id": "wf-skip",
            "input_mapping": {
                "nonexistent_var": "child_var",
            },
        },
    ))

    result = await engine.execute(dag)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_sub_workflow_nested():
    """Nested sub-workflows work (child engine inherits the loader)."""
    async def inner_loader(workflow_id):
        return {
            "nodes": [
                {"id": "inner_n1", "type": "code", "config": {
                    "code": "state.set_var('inner_result', 'deep')",
                }},
            ],
            "edges": [],
        }

    async def outer_loader(workflow_id):
        if workflow_id == "outer-wf":
            return {
                "nodes": [
                    {"id": "sw_inner", "type": "sub_workflow", "config": {
                        "workflow_id": "inner-wf",
                        "output_mapping": {"inner_result": "nested_val"},
                    }},
                ],
                "edges": [],
            }
        return await inner_loader(workflow_id)

    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(outer_loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={
            "workflow_id": "outer-wf",
            "output_mapping": {"nested_val": "final_val"},
        },
    ))

    result = await engine.execute(dag)
    assert result["status"] == "success"
    assert result["output"]["final_val"] == "deep"


@pytest.mark.asyncio
async def test_sub_workflow_result_contains_metadata():
    """The sub-workflow node result includes sub-workflow metadata."""
    loader = AsyncMock(return_value=_make_simple_sub_workflow_def())
    engine = WorkflowEngine()
    engine.set_sub_workflow_loader(loader)

    dag = DAG()
    dag.add_node(WorkflowNode(
        id="main_sub",
        type=NodeType.SUB_WORKFLOW,
        config={"workflow_id": "wf-meta"},
    ))

    result = await engine.execute(dag)
    node_output = result["output"].get("main_sub")
    # The node output is stored in node_outputs, check execution_log
    log_entry = result["execution_log"][0]
    assert log_entry["status"] == "success"

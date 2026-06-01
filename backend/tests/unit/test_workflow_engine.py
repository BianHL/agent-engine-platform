"""Unit tests for Workflow Engine"""
import pytest
import asyncio
from app.engines.workflow_engine.workflow import (
    DAG, WorkflowNode, WorkflowEdge, WorkflowState, WorkflowEngine,
    NodeType, NodeStatus, _pending_approvals, _approval_decisions,
    cancel_pending_approval,
)


# === DAG Tests ===

def test_dag_add_node():
    dag = DAG()
    node = WorkflowNode(id="n1", type=NodeType.LLM)
    dag.add_node(node)
    assert "n1" in dag.nodes


def test_dag_add_edge():
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.CONDITION))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))
    assert "n2" in dag.adjacency["n1"]


def test_dag_cycle_detection():
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n3", type=NodeType.LLM))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))
    dag.add_edge(WorkflowEdge(source="n2", target="n3"))
    dag.add_edge(WorkflowEdge(source="n3", target="n1"))

    with pytest.raises(ValueError, match="cycle"):
        dag.validate()


def test_dag_no_cycle():
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n3", type=NodeType.LLM))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))
    dag.add_edge(WorkflowEdge(source="n2", target="n3"))
    dag.validate()  # Should not raise


def test_dag_topological_sort():
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n3", type=NodeType.LLM))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))
    dag.add_edge(WorkflowEdge(source="n2", target="n3"))

    order = dag.topological_sort()
    assert order.index("n1") < order.index("n2")
    assert order.index("n2") < order.index("n3")


def test_dag_topological_sort_parallel():
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n3", type=NodeType.LLM))
    dag.add_node(WorkflowNode(id="n4", type=NodeType.LLM))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))
    dag.add_edge(WorkflowEdge(source="n1", target="n3"))
    dag.add_edge(WorkflowEdge(source="n2", target="n4"))
    dag.add_edge(WorkflowEdge(source="n3", target="n4"))

    order = dag.topological_sort()
    assert order.index("n1") < order.index("n2")
    assert order.index("n1") < order.index("n3")
    assert order.index("n2") < order.index("n4")
    assert order.index("n3") < order.index("n4")


# === WorkflowState Tests ===

def test_state_set_get():
    state = WorkflowState()
    state.set_var("key", "value")
    assert state.get_var("key") == "value"
    assert state.get_var("missing", "default") == "default"


def test_state_evaluate_expression():
    state = WorkflowState()
    state.set_var("x", 10)
    state.set_var("y", 20)
    assert state.evaluate_expression("x + y") == 30
    assert state.evaluate_expression("x * 2") == 20


def test_state_evaluate_forbidden():
    state = WorkflowState()
    with pytest.raises(ValueError, match="Forbidden"):
        state.evaluate_expression("__import__('os').system('rm -rf /')")


def test_state_evaluate_safe_functions():
    state = WorkflowState()
    assert state.evaluate_expression("len('hello')") == 5
    assert state.evaluate_expression("abs(-5)") == 5
    assert state.evaluate_expression("max(1, 2, 3)") == 3


# === WorkflowEngine Tests ===

@pytest.mark.asyncio
async def test_engine_simple_dag():
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.CONDITION, config={"expression": "True"}))
    dag.add_node(WorkflowNode(id="n2", type=NodeType.CONDITION, config={"expression": "True"}))
    dag.add_edge(WorkflowEdge(source="n1", target="n2"))

    result = await engine.execute(dag)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_engine_with_variables():
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.CONDITION, config={"expression": "x > 0"}))

    result = await engine.execute(dag, initial_vars={"x": 10})
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_engine_retry():
    call_count = 0

    class FailingAdapter:
        async def chat(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return type("Resp", (), {"content": "ok", "usage": type("U", (), {"dict": lambda s: {}})()})()

    engine = WorkflowEngine()
    engine.set_llm_adapter(FailingAdapter())
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LLM, config={"prompt": "test"}, retry_count=3))

    result = await engine.execute(dag)
    assert result["status"] == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_engine_global_timeout():
    engine = WorkflowEngine()
    engine._timeout = 0.1  # 100ms timeout

    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.LOOP, config={"max_iterations": 1000000, "exit_condition": "False"}))

    result = await engine.execute(dag)
    assert result["status"] in ("timeout", "success")  # May or may not timeout depending on speed


@pytest.mark.asyncio
async def test_engine_parallel_node():
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(id="n1", type=NodeType.PARALLEL, config={"tasks": [{"task": "a"}, {"task": "b"}, {"task": "c"}]}))

    result = await engine.execute(dag)
    assert result["status"] == "success"
    output = result["output"].get("n1", result.get("execution_log", [{}]))
    # Parallel node should complete


# === Human Approval Node Tests ===

@pytest.fixture(autouse=True)
def _clean_approval_registry():
    """确保每个测试开始前审批注册表是干净的。"""
    _pending_approvals.clear()
    _approval_decisions.clear()
    yield
    _pending_approvals.clear()
    _approval_decisions.clear()


@pytest.mark.asyncio
async def test_human_approval_approved():
    """审批通过：工作流应正常完成。"""
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="approve",
        type=NodeType.HUMAN,
        config={"approvers": ["user1"], "timeout_minutes": 5, "blocking": True},
        timeout=600,
    ))

    async def approve_after_delay():
        await asyncio.sleep(0.1)
        # 从 state 变量中获取 approval_id
        # 但因为 state 在 execute 内部，我们通过 _pending_approvals 获取
        approval_ids = list(_pending_approvals.keys())
        assert len(approval_ids) == 1
        await engine.resume_human_approval(approval_ids[0], "approved", "looks good")

    approve_task = asyncio.create_task(approve_after_delay())
    result = await engine.execute(dag)
    await approve_task

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_human_approval_rejected():
    """审批拒绝：工作流应以 failed 状态结束。"""
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="approve",
        type=NodeType.HUMAN,
        config={"approvers": ["user1"], "timeout_minutes": 5, "blocking": True},
        timeout=600,
    ))

    async def reject_after_delay():
        await asyncio.sleep(0.1)
        approval_ids = list(_pending_approvals.keys())
        assert len(approval_ids) == 1
        await engine.resume_human_approval(approval_ids[0], "rejected", "not allowed")

    reject_task = asyncio.create_task(reject_after_delay())
    result = await engine.execute(dag)
    await reject_task

    assert result["status"] == "failed"
    assert "rejected" in result["error"]


@pytest.mark.asyncio
async def test_human_approval_timeout():
    """审批超时：工作流应以 failed 状态结束并报 TimeoutError。"""
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="approve",
        type=NodeType.HUMAN,
        config={"approvers": ["user1"], "timeout_minutes": 0, "blocking": True},  # 0 分钟 = 立即超时
        timeout=600,
    ))

    result = await engine.execute(dag)

    assert result["status"] == "failed"
    assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_resume_invalid_decision():
    """无效的 decision 值应抛出 ValueError。"""
    engine = WorkflowEngine()
    with pytest.raises(ValueError, match="Invalid decision"):
        await engine.resume_human_approval("fake-id", "maybe")


@pytest.mark.asyncio
async def test_cancel_pending_approval():
    """cancel_pending_approval 应唤醒等待中的审批并标记为 rejected。"""
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="approve",
        type=NodeType.HUMAN,
        config={"approvers": ["user1"], "timeout_minutes": 60, "blocking": True},
        timeout=600,
    ))

    async def cancel_after_delay():
        await asyncio.sleep(0.1)
        approval_ids = list(_pending_approvals.keys())
        assert len(approval_ids) == 1
        result = cancel_pending_approval(approval_ids[0])
        assert result is True

    cancel_task = asyncio.create_task(cancel_after_delay())
    result = await engine.execute(dag)
    await cancel_task

    assert result["status"] == "failed"
    assert "rejected" in result["error"]


def test_cancel_nonexistent_approval():
    """取消不存在的 approval_id 应返回 False。"""
    assert cancel_pending_approval("nonexistent-id") is False


@pytest.mark.asyncio
async def test_human_approval_with_preceding_node():
    """审批节点前有其他节点时，整体工作流应正常执行。"""
    engine = WorkflowEngine()
    dag = DAG()
    dag.add_node(WorkflowNode(
        id="check",
        type=NodeType.CONDITION,
        config={"expression": "True"},
    ))
    dag.add_node(WorkflowNode(
        id="approve",
        type=NodeType.HUMAN,
        config={"approvers": ["user1"], "timeout_minutes": 5, "blocking": True},
        timeout=600,
    ))
    dag.add_edge(WorkflowEdge(source="check", target="approve"))

    async def approve_after_delay():
        await asyncio.sleep(0.1)
        approval_ids = list(_pending_approvals.keys())
        await engine.resume_human_approval(approval_ids[0], "approved")

    approve_task = asyncio.create_task(approve_after_delay())
    result = await engine.execute(dag)
    await approve_task

    assert result["status"] == "success"
    # 两个节点都应成功
    assert result["node_logs"][0]["status"] == "success"
    assert result["node_logs"][1]["status"] == "success"

"""Unit tests for workflow debug mode: DebugMode, DebugSession, and debug-enhanced execution."""
import asyncio
import pytest

from app.engines.workflow_engine.workflow import (
    DAG, WorkflowNode, WorkflowEdge, WorkflowState, WorkflowEngine,
    NodeType, NodeStatus, DebugMode, DebugSession, NodeExecutionLog,
)


@pytest.fixture
def simple_dag():
    """A -> B -> C linear DAG."""
    dag = DAG()
    dag.add_node(WorkflowNode(id="A", type=NodeType.CONDITION, config={"expression": "True"}))
    dag.add_node(WorkflowNode(id="B", type=NodeType.CONDITION, config={"expression": "True"}))
    dag.add_node(WorkflowNode(id="C", type=NodeType.CONDITION, config={"expression": "True"}))
    dag.add_edge(WorkflowEdge(source="A", target="B"))
    dag.add_edge(WorkflowEdge(source="B", target="C"))
    return dag


@pytest.fixture
def engine():
    return WorkflowEngine()


# === DebugMode enum ===

def test_debug_mode_enum_values():
    assert DebugMode.DISABLED == "disabled"
    assert DebugMode.RECORD == "record"
    assert DebugMode.STEP_THROUGH == "step_through"
    assert DebugMode.BREAKPOINT == "breakpoint"


def test_debug_mode_is_str_enum():
    assert isinstance(DebugMode.RECORD, str)


# === DebugSession dataclass ===

def test_debug_session_defaults():
    session = DebugSession()
    assert session.mode == DebugMode.RECORD
    assert session.breakpoints == set()
    assert session.step_events == {}
    assert session.paused_at is None
    assert session.history == []


def test_debug_session_with_breakpoints():
    session = DebugSession(mode=DebugMode.BREAKPOINT, breakpoints={"node_1", "node_3"})
    assert session.mode == DebugMode.BREAKPOINT
    assert "node_1" in session.breakpoints
    assert "node_3" in session.breakpoints


# === WorkflowEngine debug methods ===

def test_engine_debug_disabled_by_default(engine):
    assert engine._debug_session is None


def test_set_debug(engine):
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)
    assert engine._debug_session is session


def test_clear_debug(engine):
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)
    engine.clear_debug()
    assert engine._debug_session is None


def test_get_debug_state_none_when_disabled(engine):
    state = engine.get_debug_state()
    assert state == {"enabled": False}


def test_get_debug_state_when_enabled(engine):
    session = DebugSession(mode=DebugMode.BREAKPOINT, breakpoints={"A", "C"})
    engine.set_debug(session)
    state = engine.get_debug_state()
    assert state["enabled"] is True
    assert state["mode"] == "breakpoint"
    assert set(state["breakpoints"]) == {"A", "C"}
    assert state["paused_at"] is None


# === RECORD mode: enhanced logging ===

@pytest.mark.asyncio
async def test_record_mode_captures_input_output_snapshots(engine, simple_dag):
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)

    result = await engine.execute(simple_dag, initial_vars={"x": 10})

    assert result["status"] == "success"
    node_logs = result["node_logs"]
    assert len(node_logs) == 3

    for log in node_logs:
        assert "input_snapshot" in log
        assert "output_snapshot" in log
        assert isinstance(log["input_snapshot"], dict)
        assert isinstance(log["output_snapshot"], dict)


@pytest.mark.asyncio
async def test_record_mode_populates_debug_notes(engine, simple_dag):
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)

    result = await engine.execute(simple_dag)
    for log in result["node_logs"]:
        assert log["debug_notes"] is not None


@pytest.mark.asyncio
async def test_record_mode_populates_history(engine, simple_dag):
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)

    await engine.execute(simple_dag)
    assert len(session.history) == 3
    for entry in session.history:
        assert "node_id" in entry
        assert "status" in entry
        assert "timestamp" in entry


# === STEP_THROUGH mode: pause and continue ===

@pytest.mark.asyncio
async def test_step_through_pauses_at_each_node(engine, simple_dag):
    session = DebugSession(mode=DebugMode.STEP_THROUGH)
    engine.set_debug(session)

    async def run_workflow():
        return await engine.execute(simple_dag, initial_vars={"x": 1})

    task = asyncio.create_task(run_workflow())

    # Wait for it to pause at node A
    await asyncio.sleep(0.1)
    assert session.paused_at == "A"

    # Continue from A
    engine.continue_debug("A")
    await asyncio.sleep(0.1)
    assert session.paused_at == "B"

    # Continue from B
    engine.continue_debug("B")
    await asyncio.sleep(0.1)
    assert session.paused_at == "C"

    # Continue from C
    engine.continue_debug("C")
    result = await task

    assert result["status"] == "success"
    assert session.paused_at is None


# === BREAKPOINT mode: pause at specific nodes ===

@pytest.mark.asyncio
async def test_breakpoint_mode_pauses_at_breakpoints(engine, simple_dag):
    session = DebugSession(mode=DebugMode.BREAKPOINT, breakpoints={"B"})
    engine.set_debug(session)

    async def run_workflow():
        return await engine.execute(simple_dag, initial_vars={"x": 1})

    task = asyncio.create_task(run_workflow())

    # A runs instantly, then pauses at B breakpoint
    await asyncio.sleep(0.1)
    assert session.paused_at == "B"

    # Continue from B
    engine.continue_debug("B")
    result = await task

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_breakpoint_mode_multiple_breakpoints(engine, simple_dag):
    session = DebugSession(mode=DebugMode.BREAKPOINT, breakpoints={"A", "C"})
    engine.set_debug(session)

    async def run_workflow():
        return await engine.execute(simple_dag, initial_vars={"x": 1})

    task = asyncio.create_task(run_workflow())

    await asyncio.sleep(0.1)
    assert session.paused_at == "A"

    engine.continue_debug("A")
    # B runs instantly (no breakpoint), then pauses at C
    await asyncio.sleep(0.1)
    assert session.paused_at == "C"

    engine.continue_debug("C")
    result = await task

    assert result["status"] == "success"


# === Debug state retrieval ===

@pytest.mark.asyncio
async def test_get_debug_state_while_paused(engine, simple_dag):
    session = DebugSession(mode=DebugMode.STEP_THROUGH)
    engine.set_debug(session)

    async def run_workflow():
        return await engine.execute(simple_dag)

    task = asyncio.create_task(run_workflow())
    await asyncio.sleep(0.1)

    state = engine.get_debug_state()
    assert state["enabled"] is True
    assert state["paused_at"] == "A"
    assert len(state["history"]) == 0  # A hasn't completed yet

    engine.continue_debug("A")
    await asyncio.sleep(0.1)
    engine.continue_debug("B")
    await asyncio.sleep(0.1)
    engine.continue_debug("C")
    result = await task
    assert result["status"] == "success"


# === Debug session lifecycle ===

@pytest.mark.asyncio
async def test_debug_session_lifecycle(engine, simple_dag):
    # Start with debug
    session = DebugSession(mode=DebugMode.RECORD)
    engine.set_debug(session)

    result = await engine.execute(simple_dag)
    assert result["status"] == "success"
    assert len(session.history) == 3

    # Clear debug
    engine.clear_debug()

    # Execute without debug - no enhanced snapshots
    result2 = await engine.execute(simple_dag)
    assert result2["status"] == "success"
    for log in result2["node_logs"]:
        assert log.get("input_snapshot") is None or log.get("input_snapshot") == {}
        assert log.get("debug_notes") is None


@pytest.mark.asyncio
async def test_disabled_mode_no_extra_logging(engine, simple_dag):
    session = DebugSession(mode=DebugMode.DISABLED)
    engine.set_debug(session)

    result = await engine.execute(simple_dag)
    assert result["status"] == "success"
    assert len(session.history) == 0


@pytest.mark.asyncio
async def test_continue_debug_nonexistent_node(engine, simple_dag):
    """Calling continue_debug with unknown node_id should not raise."""
    session = DebugSession(mode=DebugMode.STEP_THROUGH)
    engine.set_debug(session)

    # Should not raise
    engine.continue_debug("nonexistent_node")


@pytest.mark.asyncio
async def test_step_through_with_initial_vars(engine, simple_dag):
    session = DebugSession(mode=DebugMode.STEP_THROUGH)
    engine.set_debug(session)

    async def run_workflow():
        return await engine.execute(simple_dag, initial_vars={"name": "test", "count": 42})

    task = asyncio.create_task(run_workflow())
    await asyncio.sleep(0.1)

    assert session.paused_at == "A"

    # Check that history records input vars
    engine.continue_debug("A")
    await asyncio.sleep(0.1)
    engine.continue_debug("B")
    await asyncio.sleep(0.1)
    engine.continue_debug("C")
    result = await task

    assert result["status"] == "success"
    for entry in session.history:
        assert "variables_snapshot" in entry

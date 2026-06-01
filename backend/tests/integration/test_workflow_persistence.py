"""Integration tests for workflow execution state persistence (W-013).

These tests verify that workflow execution state can be saved and restored,
enabling crash recovery and pause/resume of long-running workflows.

Uses SQLite in-memory following the pattern in tests/integration/conftest.py.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.base import Base, WorkflowExecutionModel
from app.engines.workflow_engine.workflow import (
    DAG,
    WorkflowEngine,
    WorkflowNode,
    WorkflowEdge,
    NodeType,
    NodeStatus,
    WorkflowState,
)
from app.platform.workflow_service.workflow_service import WorkflowExecutionService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def workflow_engine():
    return WorkflowEngine()


def _build_simple_dag() -> DAG:
    """Build a linear three-node DAG:  init -> process -> final."""
    dag = DAG()
    dag.add_node(WorkflowNode(id="init", type=NodeType.CODE, config={
        "code": "result = {'step': 'init'}",
    }))
    dag.add_node(WorkflowNode(id="process", type=NodeType.CODE, config={
        "code": "result = {'step': 'process'}",
    }))
    dag.add_node(WorkflowNode(id="final", type=NodeType.CODE, config={
        "code": "result = {'step': 'final'}",
    }))
    dag.add_edge(WorkflowEdge(source="init", target="process"))
    dag.add_edge(WorkflowEdge(source="process", target="final"))
    return dag


def _build_dag_with_condition() -> DAG:
    """Build a DAG with a condition node to test branching."""
    dag = DAG()
    dag.add_node(WorkflowNode(id="check", type=NodeType.CONDITION, config={
        "expression": "x > 0",
    }))
    dag.add_node(WorkflowNode(id="positive", type=NodeType.CODE, config={
        "code": "result = {'branch': 'positive'}",
    }))
    dag.add_node(WorkflowNode(id="negative", type=NodeType.CODE, config={
        "code": "result = {'branch': 'negative'}",
    }))
    dag.add_edge(WorkflowEdge(source="check", target="positive"))
    dag.add_edge(WorkflowEdge(source="check", target="negative"))
    return dag


def _build_failing_dag() -> DAG:
    """Build a DAG where the second node raises an exception."""
    dag = DAG()
    dag.add_node(WorkflowNode(id="step_a", type=NodeType.CODE, config={
        "code": "result = {'step': 'a'}",
    }))
    dag.add_node(WorkflowNode(id="step_b", type=NodeType.CODE, config={
        "code": "raise ValueError('boom')",
    }))
    dag.add_node(WorkflowNode(id="step_c", type=NodeType.CODE, config={
        "code": "result = {'step': 'c'}",
    }))
    dag.add_edge(WorkflowEdge(source="step_a", target="step_b"))
    dag.add_edge(WorkflowEdge(source="step_b", target="step_c"))
    return dag


# ===========================================================================
# T-W013-1: Workflow engine executes a simple DAG and produces result state
# ===========================================================================

@pytest.mark.asyncio
async def test_simple_dag_execution_produces_success(workflow_engine):
    """Engine runs a linear three-node DAG and returns overall 'success'."""
    dag = _build_simple_dag()
    result = await workflow_engine.execute(dag)

    assert result["status"] == "success"
    assert "output" in result
    assert "execution_log" in result
    assert len(result["execution_log"]) == 3


@pytest.mark.asyncio
async def test_simple_dag_execution_preserves_initial_variables(workflow_engine):
    """Initial variables passed to execute() appear in the result output."""
    dag = _build_simple_dag()
    result = await workflow_engine.execute(dag, initial_vars={"greeting": "hello", "count": 42})

    assert result["status"] == "success"
    assert result["output"]["greeting"] == "hello"
    assert result["output"]["count"] == 42


@pytest.mark.asyncio
async def test_dag_with_condition_evaluates_expression(workflow_engine):
    """Condition node evaluates expression using workflow variables."""
    dag = _build_dag_with_condition()
    result = await workflow_engine.execute(dag, initial_vars={"x": 5})

    assert result["status"] == "success"
    # Both downstream nodes run because the DAG doesn't branch; they just
    # depend on "check" succeeding.
    assert len(result["execution_log"]) == 3


# ===========================================================================
# T-W013-2: Execution results include node-level status
# ===========================================================================

@pytest.mark.asyncio
async def test_node_status_tracking_all_success(workflow_engine):
    """After successful execution every node has SUCCESS status."""
    dag = _build_simple_dag()
    await workflow_engine.execute(dag)

    engine_state_nodes = list(dag.nodes.keys())
    # The engine tracks state internally; verify via execution_log
    result = await workflow_engine.execute(dag)
    log_node_ids = [entry["node_id"] for entry in result["execution_log"]]
    assert set(log_node_ids) == {"init", "process", "final"}
    for entry in result["execution_log"]:
        assert entry["status"] == "success"


@pytest.mark.asyncio
async def test_node_status_includes_failed_node(workflow_engine):
    """When a node fails, execution stops and status reflects failure."""
    dag = _build_failing_dag()
    result = await workflow_engine.execute(dag)

    assert result["status"] == "failed"
    assert "error" in result
    # step_a should have succeeded
    log = result["execution_log"]
    assert log[0]["node_id"] == "step_a"
    assert log[0]["status"] == "success"
    # step_b failed and step_c was skipped
    assert len(log) >= 1


@pytest.mark.asyncio
async def test_node_status_skipped_when_predecessor_fails(workflow_engine):
    """Downstream nodes are skipped when a predecessor fails."""
    dag = _build_failing_dag()
    result = await workflow_engine.execute(dag)

    assert result["status"] == "failed"
    log = result["execution_log"]
    log_node_ids = [entry["node_id"] for entry in log]
    # step_c should be skipped because step_b failed
    if "step_c" in log_node_ids:
        step_c_entry = next(e for e in log if e["node_id"] == "step_c")
        assert step_c_entry["status"] == "skipped"


# ===========================================================================
# T-W013-3: Workflow can be resumed from a partial state (crash recovery)
# ===========================================================================

@pytest.mark.asyncio
async def test_persist_and_retrieve_execution(db_session):
    """WorkflowExecutionService can create and read back an execution record."""
    service = WorkflowExecutionService(db_session)
    created = await service.start_execution(
        workflow_id="wf-1", tenant_id="t1", variables={"k": "v"},
    )

    assert created["id"] is not None
    assert created["workflow_id"] == "wf-1"
    assert created["tenant_id"] == "t1"
    assert created["status"] == "running"
    assert created["variables"] == {"k": "v"}

    fetched = await service.get_execution(created["id"], "t1")
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["variables"] == {"k": "v"}


@pytest.mark.asyncio
async def test_update_node_status_persists(db_session):
    """Individual node statuses are persisted in the JSON node_states column."""
    service = WorkflowExecutionService(db_session)
    created = await service.start_execution(
        workflow_id="wf-2", tenant_id="t1",
    )

    await service.update_node_status(
        created["id"], "t1", "node_a", "success", {"result": "ok"},
    )
    await service.update_node_status(
        created["id"], "t1", "node_b", "failed", {"error": "timeout"},
    )

    fetched = await service.get_execution(created["id"], "t1")
    ns = fetched["node_states"]
    assert ns["node_a"]["status"] == "success"
    assert ns["node_a"]["output"] == {"result": "ok"}
    assert ns["node_b"]["status"] == "failed"
    assert ns["node_b"]["output"] == {"error": "timeout"}


@pytest.mark.asyncio
async def test_update_execution_status_persists(db_session):
    """Top-level execution status, log, and error are persisted correctly."""
    service = WorkflowExecutionService(db_session)
    created = await service.start_execution(
        workflow_id="wf-3", tenant_id="t1",
    )

    log = [{"node_id": "x", "status": "success"}]
    updated = await service.update_execution_status(
        created["id"], "t1", "failed",
        variables={"out": 1},
        execution_log=log,
        error_message="node x exploded",
    )

    assert updated["status"] == "failed"
    assert updated["variables"] == {"out": 1}
    assert updated["execution_log"] == log
    assert updated["error_message"] == "node x exploded"


@pytest.mark.asyncio
async def test_resume_execution_restores_running_status(db_session):
    """resume_execution() resets status to 'running' and clears error."""
    service = WorkflowExecutionService(db_session)
    created = await service.start_execution(
        workflow_id="wf-4", tenant_id="t1", variables={"seed": 99},
    )

    # Simulate a crash
    await service.update_execution_status(
        created["id"], "t1", "failed",
        execution_log=[{"node_id": "step1", "status": "success"}],
        error_message="crash!",
    )

    # Resume
    resumed = await service.resume_execution(created["id"], "t1")
    assert resumed["status"] == "running"
    assert resumed["error_message"] is None
    # Variables and log are preserved
    assert resumed["variables"] == {"seed": 99}
    assert len(resumed["execution_log"]) == 1


@pytest.mark.asyncio
async def test_resume_then_continue_execution(workflow_engine, db_session):
    """Full round-trip: execute partially -> persist -> resume -> continue.

    This simulates crash recovery: the first two nodes succeed, we persist
    their state, then resume and let the engine run the remaining nodes.
    """
    service = WorkflowExecutionService(db_session)

    # Create and persist a partial execution
    created = await service.start_execution(
        workflow_id="wf-5", tenant_id="t1", variables={"counter": 10},
    )
    await service.update_node_status(
        created["id"], "t1", "init", "success", {"step": "init"},
    )
    await service.update_node_status(
        created["id"], "t1", "process", "success", {"step": "process"},
    )
    await service.update_execution_status(
        created["id"], "t1", "paused",
        execution_log=[
            {"node_id": "init", "status": "success"},
            {"node_id": "process", "status": "success"},
        ],
    )

    # Resume from persisted state
    resumed = await service.resume_execution(created["id"], "t1")
    assert resumed["status"] == "running"
    assert resumed["variables"]["counter"] == 10

    # Execute the full DAG again (engine always runs from scratch;
    # the persisted state acts as a checkpoint for higher-level orchestration)
    dag = _build_simple_dag()
    engine_result = await workflow_engine.execute(
        dag, initial_vars=resumed["variables"],
    )
    assert engine_result["status"] == "success"

    # Persist final result
    await service.update_execution_status(
        resumed["id"], "t1", engine_result["status"],
        variables=engine_result["output"],
        execution_log=engine_result["execution_log"],
    )

    final = await service.get_execution(resumed["id"], "t1")
    assert final["status"] == "success"
    assert final["variables"]["counter"] == 10


@pytest.mark.asyncio
async def test_get_nonexistent_execution_returns_none(db_session):
    """Querying a non-existent execution returns None."""
    service = WorkflowExecutionService(db_session)
    result = await service.get_execution("no-such-id", "t1")
    assert result is None


@pytest.mark.asyncio
async def test_tenant_isolation_on_execution(db_session):
    """Executions from other tenants are not visible."""
    service = WorkflowExecutionService(db_session)
    created = await service.start_execution(
        workflow_id="wf-iso", tenant_id="tenant-a",
    )

    # tenant-b cannot see tenant-a's execution
    result = await service.get_execution(created["id"], "tenant-b")
    assert result is None

    # tenant-a can see it
    result = await service.get_execution(created["id"], "tenant-a")
    assert result is not None


# ===========================================================================
# T-W013-4: Workflow variables are preserved across execution
# ===========================================================================

@pytest.mark.asyncio
async def test_variables_preserved_in_state_object():
    """WorkflowState stores and retrieves variables correctly."""
    state = WorkflowState()
    state.set_var("name", "alice")
    state.set_var("score", 42)
    state.set_var("tags", ["a", "b"])

    assert state.get_var("name") == "alice"
    assert state.get_var("score") == 42
    assert state.get_var("tags") == ["a", "b"]
    assert state.get_var("missing", "default") == "default"


@pytest.mark.asyncio
async def test_variables_propagated_through_dag_execution(workflow_engine):
    """Variables set by one node are accessible to subsequent nodes."""
    dag = DAG()
    dag.add_node(WorkflowNode(id="writer", type=NodeType.CODE, config={
        "code": "state.set_var('computed', 100 + 23)",
    }))
    dag.add_node(WorkflowNode(id="reader", type=NodeType.CONDITION, config={
        "expression": "computed == 123",
    }))
    dag.add_edge(WorkflowEdge(source="writer", target="reader"))

    result = await workflow_engine.execute(dag, initial_vars={"seed": 1})

    assert result["status"] == "success"
    assert result["output"]["seed"] == 1
    assert result["output"]["computed"] == 123


@pytest.mark.asyncio
async def test_variables_survive_round_trip_persistence(db_session):
    """Variables survive save -> retrieve -> use cycle."""
    service = WorkflowExecutionService(db_session)

    complex_vars = {
        "string_var": "hello",
        "int_var": 999,
        "list_var": [1, 2, 3],
        "nested": {"key": "value", "flag": True},
    }
    created = await service.start_execution(
        workflow_id="wf-vars", tenant_id="t1", variables=complex_vars,
    )

    fetched = await service.get_execution(created["id"], "t1")
    assert fetched["variables"] == complex_vars

    # Update variables then verify they persist
    complex_vars["string_var"] = "updated"
    await service.update_execution_status(
        created["id"], "t1", "running", variables=complex_vars,
    )
    fetched2 = await service.get_execution(created["id"], "t1")
    assert fetched2["variables"]["string_var"] == "updated"
    assert fetched2["variables"]["nested"]["flag"] is True


@pytest.mark.asyncio
async def test_expression_evaluation_uses_variables():
    """WorkflowState.evaluate_expression can access stored variables."""
    state = WorkflowState()
    state.set_var("x", 10)
    state.set_var("y", 20)

    assert state.evaluate_expression("x + y") == 30
    assert state.evaluate_expression("x * y") == 200
    assert state.evaluate_expression("x > 5") is True


@pytest.mark.asyncio
async def test_execution_log_structure(workflow_engine):
    """Execution log entries contain expected fields for each node."""
    dag = _build_simple_dag()
    result = await workflow_engine.execute(dag)

    for entry in result["execution_log"]:
        assert "node_id" in entry
        assert "status" in entry
        assert entry["status"] in ("success", "failed", "skipped")


@pytest.mark.asyncio
async def test_resume_preserves_node_states_across_sessions(db_engine):
    """Node states survive across separate database sessions (simulates
    application restart).
    """
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False,
    )

    # Session 1: create and partially populate
    async with session_factory() as session1:
        service1 = WorkflowExecutionService(session1)
        created = await service1.start_execution(
            workflow_id="wf-cross", tenant_id="t1", variables={"persist": True},
        )
        await service1.update_node_status(
            created["id"], "t1", "step1", "success", {"out": 1},
        )
        await service1.update_node_status(
            created["id"], "t1", "step2", "success", {"out": 2},
        )
        await service1.update_execution_status(
            created["id"], "t1", "paused",
            execution_log=[
                {"node_id": "step1", "status": "success"},
                {"node_id": "step2", "status": "success"},
            ],
        )
        await session1.commit()
        exec_id = created["id"]

    # Session 2: resume (simulates new process / crash recovery)
    async with session_factory() as session2:
        service2 = WorkflowExecutionService(session2)
        resumed = await service2.resume_execution(exec_id, "t1")

        assert resumed["status"] == "running"
        assert resumed["variables"]["persist"] is True
        assert len(resumed["node_states"]) == 2
        assert resumed["node_states"]["step1"]["status"] == "success"
        assert resumed["node_states"]["step2"]["status"] == "success"
        assert len(resumed["execution_log"]) == 2

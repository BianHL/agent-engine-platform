"""Unit tests for PlanAndExecuteAgent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.engines.multi_agent.plan_execute import (
    PlanAndExecuteAgent,
    ExecutionPlan,
    PlanStep,
    StepResult,
    PlanExecuteResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_llm(content: str):
    mock = AsyncMock()
    response = MagicMock()
    response.content = content
    mock.chat.return_value = response
    return mock


def _plan_response(*steps: dict) -> str:
    return json.dumps({
        "goal": "test goal",
        "steps": list(steps),
    })


def _step_result_response(success: bool, output: str = "", error: str = "") -> str:
    data: dict = {"success": success, "output": output}
    if error:
        data["error"] = error
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_plan():
    return ExecutionPlan(
        goal="Build a website",
        steps=[
            PlanStep(id="step_1", description="Design layout"),
            PlanStep(id="step_2", description="Write HTML", dependencies=["step_1"]),
            PlanStep(id="step_3", description="Add CSS", dependencies=["step_2"]),
        ],
    )


# ---------------------------------------------------------------------------
# Plan creation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_plan_with_llm():
    plan_json = _plan_response(
        {"id": "step_1", "description": "Research topic", "dependencies": []},
        {"id": "step_2", "description": "Write draft", "dependencies": ["step_1"]},
    )
    llm = _make_mock_llm(plan_json)
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")

    result = await agent._create_plan("Write an article", {})

    assert result.goal == "test goal"
    assert len(result.steps) == 2
    assert result.steps[0].id == "step_1"
    assert result.steps[1].dependencies == ["step_1"]


@pytest.mark.asyncio
async def test_create_plan_no_llm():
    agent = PlanAndExecuteAgent(llm_adapter=None)
    result = await agent._create_plan("Do something", {})

    assert result.goal == "Do something"
    assert len(result.steps) == 1
    assert "No LLM adapter" in result.steps[0].description


@pytest.mark.asyncio
async def test_create_plan_llm_error():
    llm = AsyncMock()
    llm.chat.side_effect = Exception("API error")
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")

    result = await agent._create_plan("Do something", {})

    assert len(result.steps) == 1
    assert "failed" in result.steps[0].description.lower()


@pytest.mark.asyncio
async def test_create_plan_markdown_json():
    plan_json = _plan_response(
        {"id": "step_1", "description": "Step one", "dependencies": []},
    )
    wrapped = f"Here is the plan:\n```json\n{plan_json}\n```"
    llm = _make_mock_llm(wrapped)
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")

    result = await agent._create_plan("Test", {})
    assert len(result.steps) == 1


# ---------------------------------------------------------------------------
# Step execution tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_step_with_llm():
    resp = _step_result_response(True, output="Layout designed")
    llm = _make_mock_llm(resp)
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    step = PlanStep(id="step_1", description="Design layout")

    result = await agent._execute_step(step, "no prior context", {})

    assert result.success is True
    assert result.output == "Layout designed"
    assert step.status == "success"


@pytest.mark.asyncio
async def test_execute_step_no_llm():
    agent = PlanAndExecuteAgent(llm_adapter=None)
    step = PlanStep(id="step_1", description="Do thing")

    result = await agent._execute_step(step, "", {})

    assert result.success is True
    assert "Simulated" in result.output


@pytest.mark.asyncio
async def test_execute_step_llm_error():
    llm = AsyncMock()
    llm.chat.side_effect = Exception("Timeout")
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    step = PlanStep(id="step_1", description="Do thing")

    result = await agent._execute_step(step, "", {})

    assert result.success is False
    assert "Timeout" in result.error
    assert result.needs_replan is True


@pytest.mark.asyncio
async def test_execute_step_failed_result():
    resp = _step_result_response(False, error="Invalid input")
    llm = _make_mock_llm(resp)
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    step = PlanStep(id="step_1", description="Validate input")

    result = await agent._execute_step(step, "", {})

    assert result.success is False
    assert result.error == "Invalid input"


# ---------------------------------------------------------------------------
# Dependency ordering tests
# ---------------------------------------------------------------------------

def test_next_runnable_step_respects_dependencies(simple_plan):
    agent = PlanAndExecuteAgent()
    step, skipped = agent._next_runnable_step(simple_plan, [])

    assert step is not None
    assert step.id == "step_1"
    assert skipped is None


def test_next_runnable_step_advances_after_completion(simple_plan):
    agent = PlanAndExecuteAgent()
    completed = [StepResult(step_id="step_1", success=True, output="done")]

    step, skipped = agent._next_runnable_step(simple_plan, completed)

    assert step is not None
    assert step.id == "step_2"


def test_next_runnable_step_skips_on_failed_dependency(simple_plan):
    agent = PlanAndExecuteAgent()
    completed = [StepResult(step_id="step_1", success=False, error="oops")]

    step, skipped = agent._next_runnable_step(simple_plan, completed)

    # step_2 should be skipped, step_3 also skipped
    assert step is None
    assert skipped is not None
    assert skipped.step_id == "step_2"
    assert "dependency" in skipped.error.lower()


def test_next_runnable_step_returns_none_when_done(simple_plan):
    agent = PlanAndExecuteAgent()
    completed = [
        StepResult(step_id="step_1", success=True),
        StepResult(step_id="step_2", success=True),
        StepResult(step_id="step_3", success=True),
    ]

    step, skipped = agent._next_runnable_step(simple_plan, completed)

    assert step is None
    assert skipped is None


def test_no_dependencies_runs_in_order():
    plan = ExecutionPlan(
        goal="test",
        steps=[
            PlanStep(id="a", description="A"),
            PlanStep(id="b", description="B"),
            PlanStep(id="c", description="C"),
        ],
    )
    agent = PlanAndExecuteAgent()

    ids = []
    while True:
        step, skipped = agent._next_runnable_step(plan, [
            StepResult(step_id=sid, success=True) for sid in ids
        ])
        if step is None:
            break
        ids.append(step.id)

    assert ids == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Replanning tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_replan_preserves_completed_steps():
    new_plan_json = _plan_response(
        {"id": "step_1", "description": "Design layout", "dependencies": []},
        {"id": "step_2b", "description": "Retry with different approach", "dependencies": ["step_1"]},
    )
    llm = _make_mock_llm(new_plan_json)
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")

    original = ExecutionPlan(
        goal="Build site",
        steps=[
            PlanStep(id="step_1", description="Design layout", status="success"),
            PlanStep(id="step_2", description="Write HTML", status="failed"),
        ],
    )
    failed_step = original.steps[1]
    result = StepResult(step_id="step_2", success=False, error="Parse error")

    new_plan = await agent._replan(original, failed_step, result, {})

    completed_ids = [s.id for s in new_plan.steps if s.status == "success"]
    assert "step_1" in completed_ids
    assert any(s.id == "step_2b" for s in new_plan.steps)


@pytest.mark.asyncio
async def test_replan_no_llm_returns_original():
    agent = PlanAndExecuteAgent(llm_adapter=None)
    plan = ExecutionPlan(
        goal="test",
        steps=[PlanStep(id="s1", description="Do thing")],
    )
    failed = PlanStep(id="s1", description="Do thing")
    result = StepResult(step_id="s1", success=False, error="err")

    new_plan = await agent._replan(plan, failed, result, {})

    assert new_plan is plan


@pytest.mark.asyncio
async def test_replan_llm_error_returns_original():
    llm = AsyncMock()
    llm.chat.side_effect = Exception("API down")
    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    plan = ExecutionPlan(
        goal="test",
        steps=[PlanStep(id="s1", description="Do thing")],
    )
    failed = PlanStep(id="s1", description="Do thing")
    result = StepResult(step_id="s1", success=False, error="err")

    new_plan = await agent._replan(plan, failed, result, {})

    assert new_plan is plan


# ---------------------------------------------------------------------------
# Max replans limit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_max_replans_limit():
    """Agent should stop after max_replans failures."""
    step1_resp = _step_result_response(False, error="fail")
    step2_resp = _step_result_response(True, output="ok")

    llm = AsyncMock()
    llm.chat.side_effect = [
        # _create_plan
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Do A", "dependencies": []},
            {"id": "step_2", "description": "Do B", "dependencies": []},
        )),
        # _execute_step (step_1 fails)
        MagicMock(content=step1_resp),
        # _replan
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Do A", "dependencies": []},
            {"id": "step_2", "description": "Do B", "dependencies": []},
        )),
        # _execute_step (step_1 fails again)
        MagicMock(content=step1_resp),
        # _replan (2nd)
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Do A", "dependencies": []},
            {"id": "step_2", "description": "Do B", "dependencies": []},
        )),
        # _execute_step (step_1 fails 3rd time)
        MagicMock(content=step1_resp),
        # _replan (3rd - max reached)
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Do A", "dependencies": []},
            {"id": "step_2", "description": "Do B", "dependencies": []},
        )),
        # _execute_step (step_1 fails 4th time - max replans exceeded)
        MagicMock(content=step1_resp),
    ]

    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model", max_replans=3)
    result = await agent.run("Test task")

    # Should have stopped after max_replans
    assert result.steps_completed == 0
    assert all(not r.success for r in result.step_results)


# ---------------------------------------------------------------------------
# Full run integration tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_run_success():
    """Successful end-to-end run with all steps passing."""
    llm = AsyncMock()
    llm.chat.side_effect = [
        # _create_plan
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Gather info", "dependencies": []},
            {"id": "step_2", "description": "Analyze", "dependencies": ["step_1"]},
        )),
        # _execute_step (step_1)
        MagicMock(content=_step_result_response(True, output="Info gathered")),
        # _execute_step (step_2)
        MagicMock(content=_step_result_response(True, output="Analysis done")),
    ]

    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    result = await agent.run("Analyze data")

    assert result.steps_completed == 2
    assert result.steps_total == 2
    assert len(result.step_results) == 2
    assert result.output["results"][1]["output"] == "Analysis done"


@pytest.mark.asyncio
async def test_full_run_no_llm():
    """Run without LLM should simulate all steps."""
    agent = PlanAndExecuteAgent(llm_adapter=None)
    result = await agent.run("Do the thing")

    assert result.steps_completed == 1
    assert "Simulated" in result.output


@pytest.mark.asyncio
async def test_full_run_with_context():
    """Run passes context to LLM calls."""
    llm = AsyncMock()
    llm.chat.side_effect = [
        MagicMock(content=_plan_response(
            {"id": "step_1", "description": "Step one", "dependencies": []},
        )),
        MagicMock(content=_step_result_response(True, output="done")),
    ]

    agent = PlanAndExecuteAgent(llm_adapter=llm, model="test-model")
    result = await agent.run("Task", context={"key": "value"})

    assert result.steps_completed == 1
    # Verify context was passed to LLM
    call_args = llm.chat.call_args_list[0]
    assert "value" in call_args[1]["messages"][0]["content"] or \
           "value" in str(call_args)


# ---------------------------------------------------------------------------
# Parsing helper tests
# ---------------------------------------------------------------------------

def test_extract_json_bare():
    text = '{"goal": "test", "steps": []}'
    result = PlanAndExecuteAgent._extract_json(text)
    assert result == {"goal": "test", "steps": []}


def test_extract_json_markdown():
    text = 'Here is the plan:\n```json\n{"goal": "test", "steps": []}\n```'
    result = PlanAndExecuteAgent._extract_json(text)
    assert result == {"goal": "test", "steps": []}


def test_extract_json_none():
    result = PlanAndExecuteAgent._extract_json("no json here")
    assert result is None


def test_build_execution_context_empty():
    agent = PlanAndExecuteAgent()
    plan = ExecutionPlan(goal="test", steps=[])
    ctx = agent._build_execution_context(plan, [])
    assert "No steps" in ctx


def test_build_execution_context_with_results():
    agent = PlanAndExecuteAgent()
    plan = ExecutionPlan(
        goal="test",
        steps=[
            PlanStep(id="s1", description="First step"),
            PlanStep(id="s2", description="Second step"),
        ],
    )
    results = [
        StepResult(step_id="s1", success=True, output="done"),
        StepResult(step_id="s2", success=False, error="oops"),
    ]
    ctx = agent._build_execution_context(plan, results)
    assert "SUCCESS" in ctx
    assert "FAILED" in ctx
    assert "done" in ctx
    assert "oops" in ctx

"""Unit tests for Multi-Agent Engine."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.engines.multi_agent.crew import AgentRole, Task, Crew
from app.engines.multi_agent.handoff import HandoffManager


# ---------------------------------------------------------------------------
# Crew - sequential
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crew_sequential_execution():
    """Sequential crew runs tasks in order."""
    agents = [
        AgentRole(name="Researcher", goal="Research topics", agent_id="researcher"),
        AgentRole(name="Writer", goal="Write content", agent_id="writer"),
    ]
    tasks = [
        Task(description="Research AI trends", agent_id="researcher", task_id="t1"),
        Task(description="Write article", agent_id="writer", task_id="t2"),
    ]
    crew = Crew(agents=agents, tasks=tasks, process="sequential")
    results = await crew.run({"topic": "AI"})

    assert len(results) == 2
    assert results[0].task_id == "t1"
    assert results[0].agent_id == "researcher"
    assert results[1].task_id == "t2"
    assert results[1].agent_id == "writer"
    assert results[0].status == "completed"
    assert results[1].status == "completed"


@pytest.mark.asyncio
async def test_crew_sequential_with_context():
    """Sequential crew passes previous outputs as context."""
    agents = [AgentRole(name="Worker", goal="Do tasks", agent_id="w")]
    tasks = [
        Task(description="Step 1", agent_id="w", task_id="s1"),
        Task(description="Step 2", agent_id="w", task_id="s2", context=["s1"]),
    ]
    crew = Crew(agents=agents, tasks=tasks, process="sequential")
    results = await crew.run()
    assert len(results) == 2
    # s2 should have received context from s1
    assert results[1].status == "completed"


@pytest.mark.asyncio
async def test_crew_sequential_missing_agent():
    """Task referencing nonexistent agent gets error status."""
    agents = [AgentRole(name="Worker", goal="Do work", agent_id="w")]
    tasks = [
        Task(description="Task for missing agent", agent_id="nonexistent", task_id="t1"),
    ]
    crew = Crew(agents=agents, tasks=tasks, process="sequential")
    results = await crew.run()
    assert results[0].status == "error: agent not found"


@pytest.mark.asyncio
async def test_crew_with_llm():
    """Crew uses LLM adapter when provided."""
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = "LLM response for the task"
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    agents = [AgentRole(name="Analyst", goal="Analyze data", agent_id="a")]
    tasks = [Task(description="Analyze sales data", agent_id="a", task_id="t1")]
    crew = Crew(agents=agents, tasks=tasks, process="sequential", llm_adapter=mock_llm, model="test-model")
    results = await crew.run({"data": "sales figures"})

    assert len(results) == 1
    assert results[0].output == "LLM response for the task"
    mock_llm.chat.assert_called_once()


# ---------------------------------------------------------------------------
# Crew - hierarchical
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crew_hierarchical_execution():
    """Hierarchical crew: manager plans, workers execute."""
    agents = [
        AgentRole(name="Manager", goal="Coordinate team", agent_id="manager"),
        AgentRole(name="Worker1", goal="Execute tasks", agent_id="w1"),
    ]
    tasks = [
        Task(description="Research task", agent_id="w1", task_id="t1"),
    ]
    crew = Crew(agents=agents, tasks=tasks, process="hierarchical")
    results = await crew.run()

    # Should have task result + synthesis
    assert len(results) >= 2
    # Last result should be the synthesis
    synthesis = results[-1]
    assert synthesis.task_id == "synthesis"


# ---------------------------------------------------------------------------
# Crew validation
# ---------------------------------------------------------------------------

def test_crew_zero_agents_raises():
    """Crew with no agents should raise ValueError."""
    with pytest.raises(ValueError, match="at least one agent"):
        Crew(agents=[], tasks=[Task(description="t", agent_id="a")])


def test_crew_zero_tasks_raises():
    """Crew with no tasks should raise ValueError."""
    with pytest.raises(ValueError, match="at least one task"):
        Crew(agents=[AgentRole(name="A", goal="G")], tasks=[])


@pytest.mark.asyncio
async def test_crew_unknown_process_raises():
    """Unknown process type should raise ValueError."""
    crew = Crew(
        agents=[AgentRole(name="A", goal="G", agent_id="a")],
        tasks=[Task(description="t", agent_id="a")],
        process="unknown",
    )
    with pytest.raises(ValueError, match="Unknown process type"):
        await crew.run()


# ---------------------------------------------------------------------------
# HandoffManager
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handoff_manager_basic():
    """Handoff between two agents."""
    agents = {
        "triage": {"name": "Triage", "goal": "Route requests", "system_prompt": "You triage."},
        "support": {"name": "Support", "goal": "Help users", "system_prompt": "You help."},
    }
    targets = {
        "triage": ["support"],
        "support": [],
    }
    manager = HandoffManager(agents=agents, handoff_targets=targets)

    result = await manager.handoff("triage", "support", {"user_id": "u1"}, reason="needs help")
    assert result["from_agent"] == "triage"
    assert result["to_agent"] == "support"
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_handoff_manager_invalid_target():
    """Handoff to invalid target raises ValueError."""
    agents = {"a": {"name": "A"}, "b": {"name": "B"}}
    targets = {"a": []}
    manager = HandoffManager(agents=agents, handoff_targets=targets)

    with pytest.raises(ValueError, match="cannot hand off"):
        await manager.handoff("a", "b", {})


@pytest.mark.asyncio
async def test_handoff_manager_max_hops():
    """execute_with_handoff respects max_hops limit."""
    # Use LLM that always returns handoff instructions
    call_count = 0

    async def mock_chat(messages, model, **kwargs):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        if call_count % 2 == 1:
            resp.content = "[HANDOFF:b:forward the request]"
        else:
            resp.content = "[HANDOFF:a:send it back]"
        return resp

    mock_llm = AsyncMock()
    mock_llm.chat = mock_chat

    agents = {
        "a": {"name": "A", "goal": "", "system_prompt": "You route to b."},
        "b": {"name": "B", "goal": "", "system_prompt": "You route to a."},
    }
    targets = {"a": ["b"], "b": ["a"]}
    manager = HandoffManager(agents=agents, handoff_targets=targets, llm_adapter=mock_llm, model="test")

    result = await manager.execute_with_handoff("a", "hello", max_hops=3)
    assert result["status"] == "max_hops_reached"
    assert result["hops"] == 3


@pytest.mark.asyncio
async def test_handoff_manager_no_handoff():
    """Agent responds without handoff instruction."""
    agents = {
        "agent1": {"name": "Agent1", "goal": "", "system_prompt": "You are helpful."},
    }
    targets = {"agent1": ["agent2"]}
    manager = HandoffManager(agents=agents, handoff_targets=targets)

    result = await manager.execute_with_handoff("agent1", "hello", max_hops=5)
    assert result["status"] == "completed"
    assert result["hops"] == 0


@pytest.mark.asyncio
async def test_handoff_manager_agent_not_found():
    """Execute with nonexistent agent returns error."""
    manager = HandoffManager(agents={}, handoff_targets={})
    result = await manager.execute_with_handoff("ghost", "hello")
    assert result["status"] == "error"
    assert "not found" in result["message"]


@pytest.mark.asyncio
async def test_handoff_manager_with_llm():
    """HandoffManager uses LLM when available."""
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = "Final answer, no handoff needed."
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    agents = {"a": {"name": "A", "goal": "Help", "system_prompt": "Be helpful."}}
    targets = {"a": []}
    manager = HandoffManager(agents=agents, handoff_targets=targets, llm_adapter=mock_llm, model="test")

    result = await manager.execute_with_handoff("a", "What is AI?")
    assert result["status"] == "completed"
    mock_llm.chat.assert_called_once()


def test_parse_handoff():
    """Test handoff instruction parsing."""
    assert HandoffManager._parse_handoff("[HANDOFF:agent2:reason]") == "agent2"
    assert HandoffManager._parse_handoff("[HANDOFF:agent3]") == "agent3"
    assert HandoffManager._parse_handoff("No handoff here") is None
    assert HandoffManager._parse_handoff("[HANDOFF:agent4:long reason here]") == "agent4"


def test_get_handoff_targets():
    manager = HandoffManager(handoff_targets={"a": ["b", "c"], "b": []})
    assert manager.get_handoff_targets("a") == ["b", "c"]
    assert manager.get_handoff_targets("b") == []
    assert manager.get_handoff_targets("unknown") == []

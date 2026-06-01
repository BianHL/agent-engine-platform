"""Multi-agent orchestration API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.engines.multi_agent.crew import AgentRole, Crew, Task
from app.engines.multi_agent.handoff import HandoffManager
from app.schemas.api import (
    CreateCrewRequest,
    CrewResponse,
    HandoffRequest,
    StatusResponse,
)

router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])

# In-memory store for saved crew configs (production would use DB)
_crew_configs: dict[str, dict] = {}


@router.post("/crew", status_code=status.HTTP_201_CREATED)
async def create_and_run_crew(
    body: CreateCrewRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create and run a crew."""
    agents = [
        AgentRole(
            name=a.get("name", ""),
            goal=a.get("goal", ""),
            backstory=a.get("backstory", ""),
            tools=a.get("tools", []),
            agent_id=a.get("agent_id", a.get("name", "")),
        )
        for a in body.agents
    ]

    tasks = [
        Task(
            description=t.get("description", ""),
            agent_id=t.get("agent_id", ""),
            expected_output=t.get("expected_output", ""),
            context=t.get("context", []),
            task_id=t.get("task_id", ""),
        )
        for t in body.tasks
    ]

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=body.process,
    )

    try:
        results = await crew.run(body.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Save config
    config_id = f"crew_{len(_crew_configs) + 1}"
    _crew_configs[config_id] = {
        "id": config_id,
        "agents": body.agents,
        "tasks": body.tasks,
        "process": body.process,
        "tenant_id": user["tenant_id"],
    }

    return {
        "id": config_id,
        "process": body.process,
        "results": [
            {
                "task_id": r.task_id,
                "agent_id": r.agent_id,
                "output": r.output,
                "status": r.status,
            }
            for r in results
        ],
    }


@router.post("/handoff")
async def execute_handoff(
    body: HandoffRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Execute handoff between agents."""
    manager = HandoffManager(
        agents=body.agents,
        handoff_targets=body.handoff_targets,
    )

    try:
        result = await manager.execute_with_handoff(
            agent_id=body.from_agent,
            message=body.message,
            max_hops=body.max_hops,
            context_variables=body.context_variables,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result


@router.get("/crews")
async def list_crews(
    user: dict = Depends(get_current_user),
):
    """List saved crew configurations."""
    tenant_crews = [
        c for c in _crew_configs.values()
        if c.get("tenant_id") == user["tenant_id"]
    ]
    return tenant_crews


@router.post("/crew/dry-run")
async def dry_run_crew(
    body: CreateCrewRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Test crew execution without side effects (no LLM calls)."""
    agents = [
        AgentRole(
            name=a.get("name", ""),
            goal=a.get("goal", ""),
            backstory=a.get("backstory", ""),
            tools=a.get("tools", []),
            agent_id=a.get("agent_id", a.get("name", "")),
        )
        for a in body.agents
    ]

    tasks = [
        Task(
            description=t.get("description", ""),
            agent_id=t.get("agent_id", ""),
            expected_output=t.get("expected_output", ""),
            context=t.get("context", []),
            task_id=t.get("task_id", ""),
        )
        for t in body.tasks
    ]

    # Run without LLM adapter (uses placeholder responses)
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=body.process,
    )

    try:
        results = await crew.run(body.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "dry_run": True,
        "process": body.process,
        "results": [
            {
                "task_id": r.task_id,
                "agent_id": r.agent_id,
                "output": r.output,
                "status": r.status,
            }
            for r in results
        ],
    }

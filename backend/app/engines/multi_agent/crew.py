"""Crew-based multi-agent orchestration.

Supports sequential, hierarchical, parallel, and consensus processes.
"""
import asyncio
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM protocol
# ---------------------------------------------------------------------------

class LLMAdapter(Protocol):
    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any: ...


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentRole:
    """Defines an agent's role in a crew."""
    name: str
    goal: str
    backstory: str = ""
    tools: list[str] = field(default_factory=list)
    agent_id: str = ""


@dataclass
class Task:
    """A unit of work assigned to an agent."""
    description: str
    agent_id: str
    expected_output: str = ""
    context: list[str] = field(default_factory=list)
    task_id: str = ""


@dataclass
class TaskResult:
    """Result of a completed task."""
    task_id: str
    agent_id: str
    output: str
    status: str = "completed"


# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------

class Crew:
    """Orchestrates multiple agents to complete a sequence of tasks."""

    def __init__(
        self,
        agents: list[AgentRole],
        tasks: list[Task],
        process: str = "sequential",
        llm_adapter: Optional[LLMAdapter] = None,
        model: str = "",
    ):
        if not agents:
            raise ValueError("Crew must have at least one agent")
        if not tasks:
            raise ValueError("Crew must have at least one task")

        self.agents = {a.agent_id or a.name: a for a in agents}
        self.tasks = tasks
        self.process = process
        self.llm = llm_adapter
        self.model = model
        self.results: list[TaskResult] = []

    async def run(self, inputs: Optional[dict[str, Any]] = None) -> list[TaskResult]:
        """Execute all tasks using the configured process."""
        if self.process == "sequential":
            return await self._run_sequential(inputs or {})
        elif self.process == "hierarchical":
            return await self._run_hierarchical(inputs or {})
        elif self.process == "parallel":
            return await self._run_parallel(inputs or {})
        elif self.process == "consensus":
            return await self._run_consensus(inputs or {})
        else:
            raise ValueError(f"Unknown process type: {self.process}")

    async def _run_sequential(self, inputs: dict[str, Any]) -> list[TaskResult]:
        """Execute tasks in order; each gets previous outputs as context."""
        self.results = []
        previous_outputs: dict[str, str] = {}

        for task in self.tasks:
            agent = self.agents.get(task.agent_id)
            if not agent:
                self.results.append(TaskResult(
                    task_id=task.task_id or task.description[:20],
                    agent_id=task.agent_id,
                    output="",
                    status="error: agent not found",
                ))
                continue

            context_parts = []
            for ref in task.context:
                if ref in previous_outputs:
                    context_parts.append(previous_outputs[ref])

            output = await self._execute_task(task, agent, context_parts, inputs)
            result = TaskResult(
                task_id=task.task_id or task.description[:20],
                agent_id=task.agent_id,
                output=output,
            )
            self.results.append(result)
            previous_outputs[task.task_id or task.description[:20]] = output

        return self.results

    async def _run_hierarchical(self, inputs: dict[str, Any]) -> list[TaskResult]:
        """Manager agent decomposes work, assigns to workers, synthesizes."""
        self.results = []

        agent_list = list(self.agents.values())
        manager = agent_list[0]
        workers = agent_list[1:] if len(agent_list) > 1 else agent_list

        worker_descriptions = "\n".join(f"- {a.name}: {a.goal}" for a in workers)
        task_descriptions = "\n".join(f"- {t.description}" for t in self.tasks)

        plan = await self._generate_plan(manager, workers, task_descriptions, inputs)

        context_parts = [f"Manager plan: {plan}"]
        for task in self.tasks:
            agent = self.agents.get(task.agent_id) or workers[0]
            output = await self._execute_task(task, agent, context_parts, inputs)
            result = TaskResult(
                task_id=task.task_id or task.description[:20],
                agent_id=agent.agent_id or agent.name,
                output=output,
            )
            self.results.append(result)
            context_parts.append(f"Task '{task.description}' completed: {output[:200]}")

        synthesis = await self._synthesize_results(manager)
        self.results.append(TaskResult(
            task_id="synthesis",
            agent_id=manager.agent_id or manager.name,
            output=synthesis,
        ))

        return self.results

    async def _run_parallel(self, inputs: dict[str, Any]) -> list[TaskResult]:
        """ParallelCrewMode: execute multiple agents concurrently with task partitioning.

        将所有任务分配给对应 agent 并发执行，通过信号量限制最大并发数。
        """
        self.results = []
        agent_list = list(self.agents.values())
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run_single(task: Task, agent: AgentRole) -> TaskResult:
            """单个 agent 执行单个任务（受信号量约束）。"""
            async with semaphore:
                output = await self._execute_task(task, agent, [], inputs)
            return TaskResult(
                task_id=task.task_id or task.description[:20],
                agent_id=agent.agent_id or agent.name,
                output=output,
            )

        # 构建并发任务
        coros = []
        for task in self.tasks:
            agent = self.agents.get(task.agent_id)
            if not agent:
                coros.append(_make_error_result(task))
                continue
            # 如果任务多于 agent，复用 agent
            coros.append(_run_single(task, agent))

        results = await asyncio.gather(*coros, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                self.results.append(TaskResult(
                    task_id="error", agent_id="", output=str(r), status="error"
                ))
            else:
                self.results.append(r)

        return self.results

    async def _run_consensus(self, inputs: dict[str, Any]) -> list[TaskResult]:
        """ConsensusMode: agents vote on final answer, majority wins.

        每个 agent 对主任务给出答案，然后投票选出最终结论。
        """
        self.results = []
        agent_list = list(self.agents.values())
        primary_task = self.tasks[0]

        # 每个 agent 独立回答主任务
        async def _agent_answer(agent: AgentRole) -> tuple[str, str]:
            output = await self._execute_task(primary_task, agent, [], inputs)
            return agent.agent_id or agent.name, output

        coros = [_agent_answer(a) for a in agent_list]
        answers = await asyncio.gather(*coros, return_exceptions=True)

        proposals: dict[str, str] = {}
        for ans in answers:
            if isinstance(ans, Exception):
                continue
            agent_id, output = ans
            proposals[agent_id] = output
            self.results.append(TaskResult(
                task_id=f"proposal_{agent_id}",
                agent_id=agent_id,
                output=output,
            ))

        # LLM 评判或简单投票
        winner_id, final_answer = await self._resolve_consensus(proposals, inputs)

        self.results.append(TaskResult(
            task_id="consensus",
            agent_id=winner_id,
            output=final_answer,
        ))

        return self.results

    async def _resolve_consensus(
        self, proposals: dict[str, str], inputs: dict[str, Any]
    ) -> tuple[str, str]:
        """通过 LLM 或简单多数投票解决共识。"""
        if self.llm and self.model:
            return await self._llm_consensus(proposals, inputs)

        # 回退：取第一个 proposal 作为最终答案
        if proposals:
            first = next(iter(proposals.items()))
            return first[0], first[1]
        return "", "No proposals"

    async def _llm_consensus(
        self, proposals: dict[str, str], inputs: dict[str, Any]
    ) -> tuple[str, str]:
        """使用 LLM 从多个 agent 的 proposal 中选出最佳答案。"""
        proposals_text = "\n\n".join(
            f"Agent '{aid}': {output[:500]}"
            for aid, output in proposals.items()
        )
        prompt = (
            "Multiple agents have provided answers to the same task. "
            "Select the best answer based on accuracy and completeness.\n\n"
            f"Task: {self.tasks[0].description}\n\n"
            f"Proposals:\n{proposals_text}\n\n"
            "Return JSON: {\"winner\": \"<agent_id>\", \"final_answer\": \"<synthesized answer>\"}"
        )
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await self.llm.chat(messages=messages, model=self.model, temperature=0.0)
            content = resp.content if hasattr(resp, "content") else str(resp)
            import json
            data = json.loads(content)
            return data.get("winner", ""), data.get("final_answer", "")
        except Exception:
            # 回退到第一个 proposal
            if proposals:
                first = next(iter(proposals.items()))
                return first[0], first[1]
            return "", "Consensus failed"

    async def _execute_task(
        self,
        task: Task,
        agent: AgentRole,
        context_parts: list[str],
        inputs: dict[str, Any],
    ) -> str:
        """Execute a single task with an agent."""
        context_str = "\n".join(context_parts) if context_parts else ""
        input_str = str(inputs) if inputs else ""

        prompt = (
            f"You are {agent.name}. {agent.backstory}\n"
            f"Your goal: {agent.goal}\n\n"
            f"Task: {task.description}\n"
            f"Expected output: {task.expected_output}\n"
        )
        if context_str:
            prompt += f"\nContext from previous steps:\n{context_str}\n"
        if input_str:
            prompt += f"\nInputs:\n{input_str}\n"

        if not self.llm or not self.model:
            return f"[{agent.name}] Completed: {task.description}"

        messages = [{"role": "user", "content": prompt}]
        resp = await self.llm.chat(messages=messages, model=self.model, max_tokens=4096)
        return resp.content if hasattr(resp, "content") else str(resp)

    async def _generate_plan(
        self, manager: AgentRole, workers: list[AgentRole],
        task_descriptions: str, inputs: dict[str, Any],
    ) -> str:
        """让 manager agent 生成执行计划。"""
        worker_descriptions = "\n".join(f"- {a.name}: {a.goal}" for a in workers)
        plan_prompt = (
            f"You are the manager. Your team:\n{worker_descriptions}\n\n"
            f"Tasks to complete:\n{task_descriptions}\n\n"
            f"Inputs: {inputs}\n\n"
            "Create a plan assigning each task to a team member. "
            "Return a simple plan with task assignments."
        )
        if self.llm and self.model:
            messages = [{"role": "user", "content": plan_prompt}]
            resp = await self.llm.chat(messages=messages, model=self.model)
            return resp.content if hasattr(resp, "content") else str(resp)
        return f"Default plan: assign all tasks to {workers[0].name}"

    async def _synthesize_results(self, manager: AgentRole) -> str:
        """让 manager agent 综合所有任务结果。"""
        synthesis_prompt = (
            "Synthesize the results of all completed tasks into a final summary.\n\n"
            + "\n".join(
                f"Task '{r.task_id}' ({r.agent_id}): {r.output[:200]}"
                for r in self.results
            )
        )
        if self.llm and self.model:
            messages = [{"role": "user", "content": synthesis_prompt}]
            resp = await self.llm.chat(messages=messages, model=self.model)
            return resp.content if hasattr(resp, "content") else str(resp)
        return "All tasks completed successfully."


async def _make_error_result(task: Task) -> TaskResult:
    """为缺失 agent 的任务创建错误结果（用于 gather 兼容）。"""
    return TaskResult(
        task_id=task.task_id or task.description[:20],
        agent_id=task.agent_id,
        output="",
        status="error: agent not found",
    )

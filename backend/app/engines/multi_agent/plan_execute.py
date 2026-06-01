"""Plan-and-Execute multi-agent orchestration.

Implements a planner-executor-replanner loop:
1. Planner generates a step-by-step plan for a given task
2. Executor runs each step in dependency order
3. Re-planner adjusts the plan when a step fails
"""
import json
import logging
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field

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
# Data models
# ---------------------------------------------------------------------------

class PlanStep(BaseModel):
    id: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending, running, success, failed, skipped


class ExecutionPlan(BaseModel):
    goal: str
    steps: list[PlanStep]


class StepResult(BaseModel):
    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    needs_replan: bool = False


class PlanExecuteResult(BaseModel):
    output: Any
    steps_completed: int
    steps_total: int
    plan: ExecutionPlan
    step_results: list[StepResult]


# ---------------------------------------------------------------------------
# PlanAndExecuteAgent
# ---------------------------------------------------------------------------

class PlanAndExecuteAgent:
    """Orchestrates tasks using a plan-and-execute loop."""

    def __init__(
        self,
        llm_adapter: Optional[LLMAdapter] = None,
        max_replans: int = 3,
        model: str = "",
    ):
        self._llm = llm_adapter
        self._max_replans = max_replans
        self._model = model

    async def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> PlanExecuteResult:
        """Create a plan, execute steps, re-plan on failure."""
        context = context or {}

        plan = await self._create_plan(task, context)
        step_results: list[StepResult] = []
        replan_count = 0

        while True:
            step, skipped = self._next_runnable_step(plan, step_results)

            # All steps processed
            if step is None:
                break

            # Handle skipped steps (dependency failed)
            if skipped is not None:
                step_results.append(skipped)
                continue

            # Execute the step
            exec_context = self._build_execution_context(plan, step_results)
            result = await self._execute_step(step, exec_context, context)
            step_results.append(result)

            # Re-plan on failure
            if not result.success:
                if replan_count >= self._max_replans:
                    logger.warning(
                        "Max replans (%d) reached, stopping execution",
                        self._max_replans,
                    )
                    break

                plan = await self._replan(plan, step, result, context)
                replan_count += 1
                result.needs_replan = True

        steps_completed = sum(
            1 for r in step_results if r.success
        )
        final_output = self._synthesize_output(step_results)

        return PlanExecuteResult(
            output=final_output,
            steps_completed=steps_completed,
            steps_total=len(plan.steps),
            plan=plan,
            step_results=step_results,
        )

    def _next_runnable_step(
        self,
        plan: ExecutionPlan,
        completed: list[StepResult],
    ) -> tuple[PlanStep | None, StepResult | None]:
        """Find the next step whose dependencies are satisfied.

        Returns (step, None) if ready, (None, skip_result) if skipped,
        or (None, None) if all steps are done.
        """
        completed_ids = {r.step_id for r in completed}
        failed_ids = {
            r.step_id for r in completed if not r.success
        }

        for step in plan.steps:
            if step.id in completed_ids or step.status in ("success", "failed", "skipped"):
                continue

            # Check if any dependency failed -> skip
            unmet = [dep for dep in step.dependencies if dep in failed_ids]
            if unmet:
                step.status = "skipped"
                skip_result = StepResult(
                    step_id=step.id,
                    success=False,
                    error=f"Skipped: dependency {unmet} failed",
                )
                return None, skip_result

            # Check if all dependencies are satisfied
            if all(dep in completed_ids for dep in step.dependencies):
                return step, None

        return None, None

    # ------------------------------------------------------------------
    # LLM-backed methods
    # ------------------------------------------------------------------

    async def _create_plan(
        self,
        task: str,
        context: dict[str, Any],
    ) -> ExecutionPlan:
        """Call LLM to generate a step-by-step plan."""
        if not self._llm or not self._model:
            logger.warning("No LLM adapter configured, returning error plan")
            return ExecutionPlan(
                goal=task,
                steps=[PlanStep(id="error", description="No LLM adapter available")],
            )

        context_str = json.dumps(context) if context else "None"
        prompt = (
            f"Create a step-by-step plan to accomplish the following task.\n\n"
            f"Task: {task}\n"
            f"Context: {context_str}\n\n"
            f"Return a JSON object with this exact structure:\n"
            f'{{"goal": "<task summary>", "steps": [{{"id": "step_1", "description": "<what to do>", "dependencies": []}}]}}\n\n'
            f"Each step must have an id (step_1, step_2, ...), description, and dependencies (list of step ids it depends on)."
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await self._llm.chat(
                messages=messages, model=self._model, temperature=0.0,
            )
            content = resp.content if hasattr(resp, "content") else str(resp)
            return self._parse_plan(content, task)
        except Exception as e:
            logger.error("Failed to create plan: %s", e)
            return ExecutionPlan(
                goal=task,
                steps=[PlanStep(id="error", description=f"Plan creation failed: {e}")],
            )

    async def _execute_step(
        self,
        step: PlanStep,
        exec_context: str,
        task_context: dict[str, Any],
    ) -> StepResult:
        """Execute a single step via LLM."""
        step.status = "running"

        if not self._llm or not self._model:
            step.status = "success"
            return StepResult(
                step_id=step.id,
                success=True,
                output=f"[Simulated] Executed: {step.description}",
            )

        context_str = json.dumps(task_context) if task_context else "None"
        prompt = (
            f"Execute the following step and return the result.\n\n"
            f"Step: {step.description}\n"
            f"Context from previous steps:\n{exec_context}\n"
            f"Task context: {context_str}\n\n"
            f"Return a JSON object: {{\"success\": true/false, \"output\": \"<result>\", \"error\": \"<error if failed>\"}}"
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await self._llm.chat(
                messages=messages, model=self._model, temperature=0.0,
            )
            content = resp.content if hasattr(resp, "content") else str(resp)
            result = self._parse_step_result(content, step.id)
            step.status = "success" if result.success else "failed"
            return result
        except Exception as e:
            logger.error("Step %s execution failed: %s", step.id, e)
            step.status = "failed"
            return StepResult(
                step_id=step.id,
                success=False,
                error=str(e),
                needs_replan=True,
            )

    async def _replan(
        self,
        plan: ExecutionPlan,
        failed_step: PlanStep,
        result: StepResult,
        context: dict[str, Any],
    ) -> ExecutionPlan:
        """Re-plan remaining steps after a failure."""
        if not self._llm or not self._model:
            logger.warning("No LLM adapter, returning original plan")
            return plan

        remaining = [
            s.model_dump()
            for s in plan.steps
            if s.status in ("pending",)
        ]

        prompt = (
            f"A step in the execution plan has failed. Adjust the remaining plan.\n\n"
            f"Original goal: {plan.goal}\n"
            f"Failed step: {failed_step.description}\n"
            f"Error: {result.error}\n"
            f"Remaining steps: {json.dumps(remaining)}\n\n"
            f"Return a JSON object with the adjusted plan:\n"
            f'{{"goal": "<goal>", "steps": [{{"id": "<id>", "description": "<desc>", "dependencies": []}}]}}\n\n'
            f"Keep completed step ids. You may add, remove, or modify remaining steps."
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            resp = await self._llm.chat(
                messages=messages, model=self._model, temperature=0.0,
            )
            content = resp.content if hasattr(resp, "content") else str(resp)
            new_plan = self._parse_plan(content, plan.goal)

            # Preserve completed steps from the original plan
            completed_steps = [
                s for s in plan.steps if s.status in ("success", "skipped")
            ]
            new_plan.steps = completed_steps + new_plan.steps
            return new_plan
        except Exception as e:
            logger.error("Replanning failed: %s", e)
            return plan

    def _build_execution_context(
        self,
        plan: ExecutionPlan,
        completed: list[StepResult],
    ) -> str:
        """Build a context string from completed step results."""
        if not completed:
            return "No steps completed yet."

        parts = []
        for result in completed:
            step = next(
                (s for s in plan.steps if s.id == result.step_id), None
            )
            desc = step.description if step else result.step_id
            status = "SUCCESS" if result.success else "FAILED"
            output = result.output if result.success else result.error
            parts.append(f"[{status}] {desc}: {output}")

        return "\n".join(parts)

    def _synthesize_output(self, step_results: list[StepResult]) -> Any:
        """Produce final output from all step results."""
        successful = [r for r in step_results if r.success]
        if not successful:
            return "All steps failed."

        if len(successful) == 1:
            return successful[0].output

        return {
            "results": [
                {"step_id": r.step_id, "output": r.output}
                for r in successful
            ]
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_plan(content: str, task: str) -> ExecutionPlan:
        """Parse LLM output into an ExecutionPlan."""
        data = PlanAndExecuteAgent._extract_json(content)
        if not data or "steps" not in data:
            logger.warning("Failed to parse plan from LLM, using fallback")
            return ExecutionPlan(
                goal=task,
                steps=[PlanStep(id="step_1", description=task)],
            )

        steps = []
        for s in data["steps"]:
            steps.append(PlanStep(
                id=s.get("id", f"step_{len(steps) + 1}"),
                description=s.get("description", ""),
                dependencies=s.get("dependencies", []),
            ))

        return ExecutionPlan(
            goal=data.get("goal", task),
            steps=steps,
        )

    @staticmethod
    def _parse_step_result(content: str, step_id: str) -> StepResult:
        """Parse LLM output into a StepResult."""
        data = PlanAndExecuteAgent._extract_json(content)
        if data and "success" in data:
            return StepResult(
                step_id=step_id,
                success=bool(data["success"]),
                output=data.get("output"),
                error=data.get("error"),
            )

        # Fallback: treat raw content as successful output
        return StepResult(
            step_id=step_id,
            success=True,
            output=content,
        )

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        # Try markdown code block first
        import re
        json_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block:
            try:
                return json.loads(json_block.group(1))
            except (json.JSONDecodeError, TypeError):
                pass

        # Try bare JSON object
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except (json.JSONDecodeError, TypeError):
                pass

        return None

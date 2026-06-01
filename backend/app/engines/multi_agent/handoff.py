"""Agent handoff manager with structured protocol and routing."""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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
# Structured handoff message (Pydantic model)
# ---------------------------------------------------------------------------

class HandoffMessage(BaseModel):
    """Structured handoff instruction from LLM output."""
    target_agent: str = Field(..., description="目标 agent ID")
    context_summary: str = Field("", description="当前上下文摘要")
    pending_tasks: list[str] = Field(default_factory=list, description="待处理任务列表")

    def to_prompt_suffix(self) -> str:
        """生成追加到 agent prompt 的 handoff 格式说明。"""
        return (
            "\n\nTo hand off, respond with a JSON block:\n"
            '```json\n{"target_agent": "<id>", "context_summary": "<summary>", "pending_tasks": ["<task>"]}\n```\n'
            "Otherwise, provide your final answer."
        )


# ---------------------------------------------------------------------------
# Handoff context (internal tracking)
# ---------------------------------------------------------------------------

@dataclass
class HandoffContext:
    """Tracks handoff state during multi-agent execution."""
    current_agent_id: str
    history: list[dict[str, Any]] = field(default_factory=list)
    hop_count: int = 0


# ---------------------------------------------------------------------------
# Active handoff tracker
# ---------------------------------------------------------------------------

class HandoffTracker:
    """追踪活跃的 handoff 路由，用于监控和调试。"""

    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}

    def register(self, from_agent: str, to_agent: str, reason: str = "") -> str:
        """注册一个新的 handoff，返回 handoff_id。"""
        import uuid
        handoff_id = str(uuid.uuid4())
        self._active[handoff_id] = {
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "status": "in_progress",
        }
        return handoff_id

    def complete(self, handoff_id: str) -> None:
        """标记 handoff 为完成。"""
        if handoff_id in self._active:
            self._active[handoff_id]["status"] = "completed"

    @property
    def active_handoffs(self) -> list[dict[str, Any]]:
        """返回所有活跃的 handoff。"""
        return [h for h in self._active.values() if h["status"] == "in_progress"]

    def clear(self) -> None:
        """清除所有已完成的 handoff。"""
        self._active = {
            k: v for k, v in self._active.items() if v["status"] == "in_progress"
        }


# ---------------------------------------------------------------------------
# HandoffManager
# ---------------------------------------------------------------------------

class HandoffManager:
    """Manages agent-to-agent handoffs with structured protocol and loop prevention."""

    def __init__(
        self,
        agents: Optional[dict[str, dict[str, Any]]] = None,
        handoff_targets: Optional[dict[str, list[str]]] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        model: str = "",
    ):
        self.agents = agents or {}
        self.handoff_targets = handoff_targets or {}
        self.llm = llm_adapter
        self.model = model
        self.tracker = HandoffTracker()

    def get_handoff_targets(self, agent_id: str) -> list[str]:
        """Get which agents the given agent can hand off to."""
        return self.handoff_targets.get(agent_id, [])

    async def handoff(
        self,
        from_agent: str,
        to_agent: str,
        context_variables: dict[str, Any],
        reason: str = "",
    ) -> dict[str, Any]:
        """Transfer control from one agent to another."""
        targets = self.get_handoff_targets(from_agent)
        if to_agent not in targets:
            raise ValueError(
                f"Agent '{from_agent}' cannot hand off to '{to_agent}'. "
                f"Allowed targets: {targets}"
            )

        handoff_id = self.tracker.register(from_agent, to_agent, reason)

        logger.info(
            "Handoff from %s to %s (reason: %s)",
            from_agent, to_agent, reason,
        )

        self.tracker.complete(handoff_id)

        return {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "context_variables": context_variables,
            "reason": reason,
            "status": "completed",
            "handoff_id": handoff_id,
        }

    async def execute_with_handoff(
        self,
        agent_id: str,
        message: str,
        max_hops: int = 5,
        context_variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Run an agent and follow handoff instructions until completion or max_hops."""
        ctx = HandoffContext(
            current_agent_id=agent_id,
            history=[],
            hop_count=0,
        )
        current_message = message
        vars_so_far = dict(context_variables or {})

        while ctx.hop_count < max_hops:
            agent = self.agents.get(ctx.current_agent_id)
            if not agent:
                return {
                    "status": "error",
                    "message": f"Agent '{ctx.current_agent_id}' not found",
                    "history": ctx.history,
                    "hops": ctx.hop_count,
                }

            full_prompt = self._build_agent_prompt(ctx, agent, current_message, vars_so_far)

            # 获取 agent 响应
            if self.llm and self.model:
                messages = [{"role": "user", "content": full_prompt}]
                resp = await self.llm.chat(messages=messages, model=self.model)
                response_text = resp.content if hasattr(resp, "content") else str(resp)
            else:
                response_text = f"[{ctx.current_agent_id}] Response to: {current_message}"

            # 解析 handoff 指令（结构化 JSON 优先，regex 回退）
            handoff_msg = self._parse_handoff_structured(response_text)

            ctx.history.append({
                "agent_id": ctx.current_agent_id,
                "message": current_message[:200],
                "response": response_text[:500],
                "handoff_to": handoff_msg.target_agent if handoff_msg else None,
            })

            if handoff_msg and handoff_msg.target_agent in self.get_handoff_targets(ctx.current_agent_id):
                ctx.hop_count += 1
                ctx.current_agent_id = handoff_msg.target_agent
                current_message = response_text
                continue

            # 无 handoff - 返回最终结果
            return {
                "status": "completed",
                "final_agent": ctx.current_agent_id,
                "response": response_text,
                "history": ctx.history,
                "hops": ctx.hop_count,
            }

        # 达到最大跳数
        return {
            "status": "max_hops_reached",
            "final_agent": ctx.current_agent_id,
            "response": response_text if 'response_text' in dir() else "",
            "history": ctx.history,
            "hops": ctx.hop_count,
        }

    def _build_agent_prompt(
        self,
        ctx: HandoffContext,
        agent: dict,
        current_message: str,
        vars_so_far: dict,
    ) -> str:
        """构建包含 handoff 格式说明的 agent prompt。"""
        agent_prompt = agent.get("system_prompt", "")
        if agent.get("goal"):
            agent_prompt += f"\nYour goal: {agent['goal']}"
        if agent.get("backstory"):
            agent_prompt += f"\nBackstory: {agent['backstory']}"

        targets = self.get_handoff_targets(ctx.current_agent_id)
        if targets:
            agent_prompt += (
                f"\n\nYou may hand off to: {', '.join(targets)}. "
                "To hand off, respond with: [HANDOFF:agent_id:reason]. "
                "Alternatively, use JSON: "
                '{"target_agent": "<id>", "context_summary": "<summary>", "pending_tasks": ["<task>"]}. '
                "Otherwise, provide your final answer."
            )

        full_prompt = f"{agent_prompt}\n\nUser message: {current_message}"
        if vars_so_far:
            full_prompt += f"\nContext variables: {vars_so_far}"
        return full_prompt

    def _parse_handoff_structured(self, response: str) -> Optional[HandoffMessage]:
        """解析 LLM 输出为结构化 HandoffMessage。JSON 优先，regex 回退。"""
        # 1. 尝试 JSON 解析
        json_msg = self._try_parse_json_handoff(response)
        if json_msg:
            return json_msg

        # 2. Regex 回退
        target = self._parse_handoff_regex(response)
        if target:
            return HandoffMessage(target_agent=target)

        return None

    @staticmethod
    def _try_parse_json_handoff(response: str) -> Optional[HandoffMessage]:
        """尝试从 LLM 响应中提取 JSON 格式的 handoff 指令。"""
        # 尝试提取 ```json ... ``` 代码块
        json_block = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_block:
            text = json_block.group(1)
        else:
            # 尝试匹配独立的 JSON 对象
            json_match = re.search(r'\{[^{}]*"target_agent"\s*:\s*"[^"]*"[^{}]*\}', response)
            if json_match:
                text = json_match.group(0)
            else:
                return None

        try:
            data = json.loads(text)
            if "target_agent" in data:
                return HandoffMessage(
                    target_agent=data["target_agent"],
                    context_summary=data.get("context_summary", ""),
                    pending_tasks=data.get("pending_tasks", []),
                )
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        return None

    @staticmethod
    def _parse_handoff_regex(response: str) -> Optional[str]:
        """Regex fallback: parse [HANDOFF:agent] from response."""
        match = re.search(r'\[HANDOFF:([^:\]]+)(?::([^\]]*))?\]', response)
        if match:
            return match.group(1).strip()
        return None

    # 保持向后兼容的静态方法
    @staticmethod
    def _parse_handoff(response: str) -> Optional[str]:
        """Parse handoff instruction from agent response. Backward compatible."""
        # 先尝试 JSON
        json_msg = HandoffManager._try_parse_json_handoff(response)
        if json_msg:
            return json_msg.target_agent
        # Regex 回退
        return HandoffManager._parse_handoff_regex(response)

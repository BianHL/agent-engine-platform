import asyncio
import ast
import logging
import os
import signal
import resource
import time
import operator
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Module-level registry for pending human approvals.
# Maps approval_id -> asyncio.Event; set by _execute_human, signaled by resume_human_approval.
_pending_approvals: dict[str, asyncio.Event] = {}
# Maps approval_id -> dict holding the resolution decision; written by resume_human_approval.
_approval_decisions: dict[str, dict] = {}

class DebugMode(str, Enum):
    DISABLED = "disabled"
    RECORD = "record"
    STEP_THROUGH = "step_through"
    BREAKPOINT = "breakpoint"


class NodeType(str, Enum):
    START = "start"
    END = "end"
    LLM = "llm"
    KNOWLEDGE = "knowledge"
    QUESTION_CLASSIFIER = "question_classifier"
    PARAMETER_EXTRACTOR = "parameter_extractor"
    CODE = "code"
    TEMPLATE = "template"
    VARIABLE = "variable"
    CONDITION = "condition"
    PARALLEL = "parallel"
    ITERATION = "iteration"
    HTTP = "http"
    TOOL = "tool"
    HUMAN = "human"
    SUB_WORKFLOW = "sub_workflow"
    ANSWER = "answer"
    # Legacy aliases
    LOOP = "loop"
    VARIABLE_AGGREGATOR = "variable_aggregator"
    VARIABLE_ASSIGNER = "variable_assigner"

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class NodeExecutionLog:
    """Per-node execution detail log."""
    node_id: str
    node_type: str
    input_data: Any = None
    output_data: Any = None
    status: str = "pending"
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    variables_snapshot: dict = field(default_factory=dict)
    input_snapshot: dict = field(default_factory=dict)
    output_snapshot: dict = field(default_factory=dict)
    debug_notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DebugSession:
    """Configuration and state for a workflow debug session."""
    mode: DebugMode = DebugMode.RECORD
    breakpoints: set[str] = field(default_factory=set)
    step_events: dict[str, asyncio.Event] = field(default_factory=dict)
    paused_at: Optional[str] = None
    history: list[dict] = field(default_factory=list)


@dataclass
class TraceNode:
    """Execution trace tree node for call-chain tracking."""
    trace_id: str
    node_id: str
    parent_trace_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"
    children: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "node_id": self.node_id,
            "parent_trace_id": self.parent_trace_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "children": [c.to_dict() for c in self.children],
        }


class WorkflowNode(BaseModel):
    id: str
    type: NodeType
    config: dict = {}
    retry_count: int = 0
    timeout: int = 60

class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class DAG:
    def __init__(self):
        self.nodes: dict[str, WorkflowNode] = {}
        self.edges: list[WorkflowEdge] = []
        self.adjacency: dict[str, list[str]] = {}
        self.reverse_adj: dict[str, list[str]] = {}

    def add_node(self, node: WorkflowNode):
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []
        if node.id not in self.reverse_adj:
            self.reverse_adj[node.id] = []

    def add_edge(self, edge: WorkflowEdge):
        self.edges.append(edge)
        if edge.source not in self.adjacency:
            self.adjacency[edge.source] = []
        self.adjacency[edge.source].append(edge.target)
        if edge.target not in self.reverse_adj:
            self.reverse_adj[edge.target] = []
        self.reverse_adj[edge.target].append(edge.source)

    def validate(self):
        if self._has_cycle():
            raise ValueError("Workflow DAG contains cycles")

    def _has_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        in_degree = {n: 0 for n in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

        queue = [n for n, d in in_degree.items() if d == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in self.adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected during topological sort")
        return result

class _SafeExprVisitor(ast.NodeVisitor):
    """Whitelist AST node types for safe expression evaluation."""
    ALLOWED_NODES = {
        ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.Call, ast.Constant, ast.Name, ast.Load, ast.And, ast.Or,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.In, ast.NotIn, ast.USub, ast.Not, ast.Is, ast.IsNot,
        ast.List, ast.Tuple, ast.Dict,
        ast.Attribute, ast.Subscript,
    }

    def __init__(self):
        self.errors: list[str] = []

    def visit(self, node):
        if type(node) not in self.ALLOWED_NODES:
            self.errors.append(f"Forbidden expression: {type(node).__name__}")
            return
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            self.errors.append(f"Forbidden name: {node.id}")
            return
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Reject dunder attribute access to prevent sandbox escape
        via __class__.__bases__.__subclasses__() chains."""
        if node.attr.startswith("__"):
            self.errors.append(f"Forbidden attribute: {node.attr}")
            return
        self.generic_visit(node)

    def visit_Constant(self, node):
        """Only allow safe constant types (int, float, str, bool, None)."""
        if not isinstance(node.value, (int, float, str, bool, type(None))):
            self.errors.append(f"Forbidden constant type: {type(node.value).__name__}")
            return
        self.generic_visit(node)


class WorkflowState:
    def __init__(self):
        self.variables: dict[str, Any] = {}
        self.node_outputs: dict[str, Any] = {}
        self.node_status: dict[str, NodeStatus] = {}

    def set_var(self, key: str, value: Any):
        self.variables[key] = value

    def get_var(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def evaluate_expression(self, expr: str) -> Any:
        """Safely evaluate expression using AST whitelist."""
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid expression: {e}")

        visitor = _SafeExprVisitor()
        visitor.visit(tree)
        if visitor.errors:
            raise ValueError(f"Forbidden operation: {visitor.errors[0]}")

        safe_globals = {"__builtins__": {}}
        safe_locals = {
            "True": True, "False": False, "None": None,
            "len": len, "str": str, "int": int, "float": float,
            "abs": abs, "min": min, "max": max, "sum": sum,
            **self.variables,
        }

        return eval(compile(tree, "<expr>", "eval"), safe_globals, safe_locals)

class WorkflowEngine:
    def __init__(self):
        self._node_executors: dict[NodeType, Callable] = {
            NodeType.START: self._execute_start,
            NodeType.END: self._execute_end,
            NodeType.LLM: self._execute_llm,
            NodeType.KNOWLEDGE: self._execute_knowledge,
            NodeType.QUESTION_CLASSIFIER: self._execute_question_classifier,
            NodeType.PARAMETER_EXTRACTOR: self._execute_parameter_extractor,
            NodeType.CODE: self._execute_code,
            NodeType.TEMPLATE: self._execute_template,
            NodeType.VARIABLE: self._execute_variable,
            NodeType.CONDITION: self._execute_condition,
            NodeType.PARALLEL: self._execute_parallel,
            NodeType.ITERATION: self._execute_loop,
            NodeType.HTTP: self._execute_http,
            NodeType.TOOL: self._execute_tool,
            NodeType.HUMAN: self._execute_human,
            NodeType.SUB_WORKFLOW: self._execute_sub_workflow,
            NodeType.ANSWER: self._execute_answer,
            # Legacy aliases
            NodeType.LOOP: self._execute_loop,
            NodeType.PARAMETER_EXTRACTOR: self._execute_parameter_extractor,
            NodeType.VARIABLE_AGGREGATOR: self._execute_variable_aggregator,
            NodeType.VARIABLE_ASSIGNER: self._execute_variable_assigner,
        }
        self._llm_adapter = None
        self._timeout = 300  # 5 min global timeout
        self._sub_workflow_loader: Optional[Callable] = None
        self._debug_session: Optional[DebugSession] = None

    def set_llm_adapter(self, adapter):
        self._llm_adapter = adapter

    def set_sub_workflow_loader(self, loader: Callable):
        """Set an async callable that loads sub-workflow definitions.

        The loader must accept a workflow_id (str) and return a dict with
        keys "nodes" (list[dict]) and "edges" (list[dict]), where each node
        dict has at least {"id": str, "type": str, "config": dict} and each
        edge dict has at least {"source": str, "target": str}.
        """
        self._sub_workflow_loader = loader

    def set_debug(self, session: DebugSession):
        """Enable debug mode with the given session configuration."""
        self._debug_session = session

    def clear_debug(self):
        """Disable debug mode."""
        self._debug_session = None

    def continue_debug(self, node_id: str):
        """Signal to continue execution from a breakpoint or step-through pause."""
        if self._debug_session and node_id in self._debug_session.step_events:
            self._debug_session.step_events[node_id].set()

    def get_debug_state(self) -> dict:
        """Return the current debug state."""
        if not self._debug_session:
            return {"enabled": False}
        return {
            "enabled": True,
            "mode": self._debug_session.mode.value,
            "breakpoints": list(self._debug_session.breakpoints),
            "paused_at": self._debug_session.paused_at,
            "history": list(self._debug_session.history),
        }

    async def execute(self, dag: DAG, initial_vars: dict = None, parent_trace_id: str = None) -> dict:
        dag.validate()
        state = WorkflowState()
        if initial_vars:
            for k, v in initial_vars.items():
                state.set_var(k, v)

        trace_id = str(uuid.uuid4())
        execution_log = []
        node_logs: list[NodeExecutionLog] = []
        trace_nodes: dict[str, TraceNode] = {}
        start_time = time.time()
        debug = self._debug_session
        is_debug = debug is not None and debug.mode != DebugMode.DISABLED

        try:
            order = dag.topological_sort()
            for node_id in order:
                if time.time() - start_time > self._timeout:
                    timeout_logs = [nl.to_dict() for nl in node_logs]
                    return {
                        "status": "timeout",
                        "output": state.variables,
                        "execution_log": execution_log,
                        "trace_id": trace_id,
                        "node_logs": timeout_logs,
                        "trace_tree": self._build_trace_tree(trace_nodes, order),
                    }

                node = dag.nodes[node_id]
                state.node_status[node_id] = NodeStatus.RUNNING

                trace_node = TraceNode(
                    trace_id=str(uuid.uuid4()),
                    node_id=node_id,
                    parent_trace_id=parent_trace_id or trace_id,
                    started_at=datetime.now(timezone.utc).isoformat(),
                    status="running",
                )
                trace_nodes[node_id] = trace_node

                predecessors = dag.reverse_adj.get(node_id, [])
                skip = False
                for pred in predecessors:
                    if state.node_status.get(pred) in (NodeStatus.FAILED, NodeStatus.SKIPPED):
                        skip = True
                        break

                if skip:
                    state.node_status[node_id] = NodeStatus.SKIPPED
                    trace_node.status = "skipped"
                    trace_node.completed_at = datetime.now(timezone.utc).isoformat()

                    node_log = NodeExecutionLog(
                        node_id=node_id,
                        node_type=node.type.value,
                        status="skipped",
                        started_at=trace_node.started_at,
                        completed_at=trace_node.completed_at,
                        variables_snapshot=dict(state.variables),
                    )
                    node_logs.append(node_log)
                    execution_log.append({"node_id": node_id, "status": "skipped"})
                    continue

                # Debug: pause before execution if needed
                if is_debug and debug.mode in (DebugMode.STEP_THROUGH, DebugMode.BREAKPOINT):
                    should_pause = (
                        debug.mode == DebugMode.STEP_THROUGH
                        or (debug.mode == DebugMode.BREAKPOINT and node_id in debug.breakpoints)
                    )
                    if should_pause:
                        event = asyncio.Event()
                        debug.step_events[node_id] = event
                        debug.paused_at = node_id
                        try:
                            await event.wait()
                        finally:
                            debug.step_events.pop(node_id, None)
                            if debug.paused_at == node_id:
                                debug.paused_at = None

                node_start = time.time()
                node_started_at = datetime.now(timezone.utc).isoformat()
                input_snap = dict(state.variables) if is_debug else {}
                try:
                    result = await self._execute_with_retry(node, state)
                    duration_ms = (time.time() - node_start) * 1000

                    state.node_outputs[node_id] = result
                    state.node_status[node_id] = NodeStatus.SUCCESS
                    trace_node.status = "success"
                    trace_node.completed_at = datetime.now(timezone.utc).isoformat()

                    output_snap = dict(result) if is_debug and isinstance(result, dict) else {}

                    node_log = NodeExecutionLog(
                        node_id=node_id,
                        node_type=node.type.value,
                        input_data=dict(state.variables),
                        output_data=str(result)[:500] if result else None,
                        status="success",
                        duration_ms=round(duration_ms, 2),
                        started_at=node_started_at,
                        completed_at=trace_node.completed_at,
                        variables_snapshot=dict(state.variables),
                        input_snapshot=input_snap,
                        output_snapshot=output_snap,
                        debug_notes=f"Node {node_id} executed successfully" if is_debug else None,
                    )
                    node_logs.append(node_log)
                    execution_log.append({"node_id": node_id, "status": "success", "output": str(result)[:200]})

                    if is_debug:
                        debug.history.append({
                            "node_id": node_id,
                            "status": "success",
                            "timestamp": trace_node.completed_at,
                            "duration_ms": round(duration_ms, 2),
                            "variables_snapshot": dict(state.variables),
                        })
                except Exception as node_err:
                    duration_ms = (time.time() - node_start) * 1000
                    state.node_status[node_id] = NodeStatus.FAILED
                    trace_node.status = "failed"
                    trace_node.completed_at = datetime.now(timezone.utc).isoformat()

                    node_log = NodeExecutionLog(
                        node_id=node_id,
                        node_type=node.type.value,
                        input_data=dict(state.variables),
                        output_data=None,
                        status="failed",
                        duration_ms=round(duration_ms, 2),
                        error_message=str(node_err),
                        started_at=node_started_at,
                        completed_at=trace_node.completed_at,
                        variables_snapshot=dict(state.variables),
                        input_snapshot=input_snap,
                        output_snapshot={},
                        debug_notes=f"Node {node_id} failed: {node_err}" if is_debug else None,
                    )
                    node_logs.append(node_log)
                    execution_log.append({"node_id": node_id, "status": "failed", "error": str(node_err)})

                    if is_debug:
                        debug.history.append({
                            "node_id": node_id,
                            "status": "failed",
                            "timestamp": trace_node.completed_at,
                            "duration_ms": round(duration_ms, 2),
                            "error": str(node_err),
                            "variables_snapshot": dict(state.variables),
                        })
                    raise
        except Exception as e:
            return {
                "status": "failed",
                "output": state.variables,
                "error": str(e),
                "execution_log": execution_log,
                "trace_id": trace_id,
                "node_logs": [nl.to_dict() for nl in node_logs],
                "trace_tree": self._build_trace_tree(trace_nodes, order),
            }

        return {
            "status": "success",
            "output": state.variables,
            "execution_log": execution_log,
            "trace_id": trace_id,
            "node_logs": [nl.to_dict() for nl in node_logs],
            "trace_tree": self._build_trace_tree(trace_nodes, order),
        }

    def _build_trace_tree(self, trace_nodes: dict[str, TraceNode], order: list[str]) -> dict:
        """Build a nested trace tree from flat trace nodes using DAG adjacency."""
        if not trace_nodes:
            return {}

        # Find root nodes (no predecessors in the execution order)
        root_ids = [nid for nid in order if nid in trace_nodes]
        if not root_ids:
            return {}

        # Build parent->children relationships from the DAG edges
        for node_id in order:
            tn = trace_nodes.get(node_id)
            if not tn:
                continue
            # Find children: nodes whose parent_trace_id matches this node's trace
            for child_id in order:
                child_tn = trace_nodes.get(child_id)
                if child_tn and child_tn.parent_trace_id == tn.trace_id and child_id != node_id:
                    tn.children.append(child_tn)

        # Return the first root as the tree root
        root = trace_nodes[root_ids[0]]
        return root.to_dict()

    async def _execute_with_retry(self, node: WorkflowNode, state: WorkflowState) -> Any:
        max_retries = node.retry_count
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                executor = self._node_executors.get(node.type)
                if not executor:
                    raise ValueError(f"No executor for node type: {node.type}")

                return await asyncio.wait_for(executor(node, state), timeout=node.timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Node {node.id} timed out after {node.timeout}s")
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise last_error

    async def _execute_llm(self, node: WorkflowNode, state: WorkflowState) -> Any:
        if not self._llm_adapter:
            return {"content": "LLM adapter not configured"}

        config = node.config
        prompt = config.get("prompt", "")
        # Replace variables in prompt
        for key, value in state.variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        messages = config.get("messages", [{"role": "user", "content": prompt}])
        response = await self._llm_adapter.chat(
            messages=messages,
            model=config.get("model", ""),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000)
        )
        return {"content": response.content, "usage": response.usage.dict()}

    async def _execute_condition(self, node: WorkflowNode, state: WorkflowState) -> Any:
        expr = node.config.get("expression", "True")
        result = state.evaluate_expression(expr)
        return {"condition_result": bool(result)}

    async def _execute_parallel(self, node: WorkflowNode, state: WorkflowState) -> Any:
        tasks_config = node.config.get("tasks", [])
        timeout = node.config.get("timeout", 60)

        async def run_task(task_config):
            # Simplified - would create sub-nodes in production
            return {"result": "completed", "config": task_config}

        tasks = [run_task(t) for t in tasks_config]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {"results": [str(r) for r in results]}

    async def _execute_loop(self, node: WorkflowNode, state: WorkflowState) -> Any:
        max_iterations = node.config.get("max_iterations", 5)
        exit_condition = node.config.get("exit_condition", "False")
        results = []

        for i in range(max_iterations):
            try:
                if state.evaluate_expression(exit_condition):
                    break
            except Exception as e:
                logger.warning(
                    "Loop exit condition evaluation failed at iteration %d: %s", i, e
                )
                break
            results.append({"iteration": i})

        return {"iterations": len(results), "results": results}

    async def _execute_http(self, node: WorkflowNode, state: WorkflowState) -> Any:
        config = node.config
        url = config.get("url", "")
        method = config.get("method", "GET").upper()

        # Replace variables in URL BEFORE SSRF check to prevent bypass via state variables
        for key, value in state.variables.items():
            url = url.replace(f"{{{key}}}", str(value))

        headers = config.get("headers", {})
        body = config.get("body", {})

        from app.core.ssrf import safe_request
        try:
            kwargs = {}
            if method not in ("GET", "HEAD", "DELETE"):
                kwargs["json"] = body

            resp = await safe_request(
                method, url,
                timeout=node.timeout,
                headers=headers,
                **kwargs,
            )
            return {"status_code": resp.status_code, "body": resp.text[:5000]}
        except ValueError as e:
            return {"error": f"URL blocked: {e}", "status_code": 0}

    async def _execute_code(self, node: WorkflowNode, state: WorkflowState) -> dict:
        """Execute code in isolated subprocess with process group and resource limits.

        If the code references ``state``, a lightweight proxy dict is injected so
        that ``state.set_var(k, v)`` / ``state.get_var(k)`` work inside the
        subprocess.  After execution, any variables written via the proxy are
        merged back into the real WorkflowState.
        """
        code = node.config.get("code", "")
        timeout = node.config.get("timeout", 30)
        if not code:
            return {"output": None, "error": "No code provided"}

        import json as _json

        needs_state = "state" in code
        if needs_state:
            # Build a wrapper that provides a minimal state proxy
            state_json = _json.dumps(dict(state.variables), ensure_ascii=False)
            wrapper = (
                "import json as _json, sys as _sys\n"
                f"_vars = _json.loads({state_json!r})\n\n"
                "class _StateProxy:\n"
                "    def set_var(self, k, v): _vars[k] = v\n"
                "    def get_var(self, k, default=None): return _vars.get(k, default)\n\n"
                "state = _StateProxy()\n"
                "try:\n"
                "    exec(compile("
                + repr(code)
                + ', "<code-node>", "exec"), {"state": state, "__builtins__": __builtins__})\n'
                "except SystemExit:\n"
                "    pass\n"
                "_sys.stdout.write(_json.dumps(_vars, ensure_ascii=False))\n"
            )
            exec_code = wrapper
        else:
            exec_code = code

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(exec_code)
            script_path = f.name

        def _sandbox_preexec():
            """Create new process group and set resource limits for sandboxing."""
            os.setpgrp()
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))

        # Minimal environment to reduce attack surface
        safe_env = {
            k: os.environ.get(k, "")
            for k in ("PATH", "HOME", "TMPDIR") if k in os.environ or k == "PATH"
        }

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=_sandbox_preexec,
                env=safe_env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
                if proc.returncode != 0:
                    err_msg = stderr.decode("utf-8", errors="replace")[:2000]
                    raise RuntimeError(f"Code execution failed (exit {proc.returncode}): {err_msg}")
                raw = stdout.decode("utf-8", errors="replace")
                if needs_state:
                    try:
                        updated_vars = _json.loads(raw.strip())
                        for k, v in updated_vars.items():
                            state.set_var(k, v)
                    except _json.JSONDecodeError as e:
                        logger.debug("Code node output not valid JSON, skipping state update: %s", e)
                return {
                    "output": raw[:5000],
                    "error": None,
                    "exit_code": proc.returncode,
                }
            except asyncio.TimeoutError:
                # Kill entire process group to clean up any child processes
                if proc.returncode is None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        proc.kill()
                return {"output": None, "error": f"Code execution timed out after {timeout}s"}
        finally:
            if proc and proc.returncode is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    proc.kill()
            os.unlink(script_path)

    async def _execute_human(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Human approval node: store request, provide callback, await decision.

        Creates an asyncio.Event registered in the module-level _pending_approvals
        dict, then blocks until resume_human_approval signals the event or the
        timeout expires.

        Config keys:
            approvers: list[str] - user IDs who can approve
            timeout_minutes: int - auto-reject after this (default 60)
            callback_url: str - external notification endpoint
        """
        import json
        approval_id = str(uuid.uuid4())
        timeout_minutes = node.config.get("timeout_minutes", 60)
        approvers = node.config.get("approvers", [])
        callback_url = node.config.get("callback_url", "")

        # 构建审批请求记录
        approval_request = {
            "approval_id": approval_id,
            "node_id": node.id,
            "status": "pending_approval",
            "approvers": approvers,
            "input_snapshot": dict(state.variables),
            "callback_url": callback_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
            ).isoformat(),
        }

        # 存入 state 以便外部系统读取
        state.set_var(
            f"_approval_{node.id}", json.dumps(approval_request, ensure_ascii=False)
        )

        # 注册 asyncio.Event，阻塞等待审批决策
        event = asyncio.Event()
        _pending_approvals[approval_id] = event

        try:
            # 如果配置了 callback_url，发送通知
            if callback_url:
                await self._notify_approval_callback(callback_url, approval_request)

            # If blocking mode is not explicitly requested, return immediately
            # with pending_approval status (fire-and-forget pattern).
            blocking = node.config.get("blocking", False)
            if not blocking:
                return {
                    "status": "pending_approval",
                    "node_id": node.id,
                    "approval_id": approval_id,
                    "approvers": approvers,
                    "expires_at": approval_request["expires_at"],
                }

            # 阻塞等待：要么 resume_human_approval 设置 event，要么超时
            await asyncio.wait_for(event.wait(), timeout=timeout_minutes * 60)
        except asyncio.TimeoutError:
            # 超时视为拒绝，清理注册表
            _approval_decisions[approval_id] = {
                "decision": "rejected",
                "comment": "Approval timed out",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
            # Clean stale entries from both registries
            _pending_approvals.pop(approval_id, None)
            _cleanup_stale_approval_entries()
            raise TimeoutError(
                f"Human approval {approval_id} timed out after {timeout_minutes} minutes"
            )
        finally:
            # 无论如何清理注册表中的 Event
            _pending_approvals.pop(approval_id, None)

        # 读取审批结果
        decision_data = _approval_decisions.pop(approval_id, {})
        decision = decision_data.get("decision", "rejected")

        # 更新 state 中的审批记录
        approval_request["status"] = decision
        approval_request["resolved_at"] = decision_data.get("resolved_at")
        approval_request["comment"] = decision_data.get("comment", "")
        state.set_var(
            f"_approval_{node.id}", json.dumps(approval_request, ensure_ascii=False)
        )

        if decision != "approved":
            raise ValueError(f"Human approval {approval_id} was {decision}")

        return {
            "status": decision,
            "node_id": node.id,
            "approval_id": approval_id,
            "approvers": approvers,
            "resolved_at": decision_data.get("resolved_at"),
            "comment": decision_data.get("comment", ""),
        }

    async def _notify_approval_callback(
        self, callback_url: str, approval_request: dict
    ) -> None:
        """向回调 URL 发送审批请求通知（fire-and-forget）。"""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    callback_url,
                    json={
                        "event": "approval_required",
                        "approval_id": approval_request["approval_id"],
                        "node_id": approval_request["node_id"],
                        "approvers": approval_request["approvers"],
                        "expires_at": approval_request["expires_at"],
                    },
                )
        except Exception as exc:
            logger.warning(f"Approval callback failed: {exc}")

    async def resume_human_approval(
        self, approval_id: str, decision: str, comment: str = ""
    ) -> dict:
        """外部回调：根据 approval_id 恢复审批节点。

        Stores the decision in _approval_decisions and sets the asyncio.Event
        to unblock the coroutine waiting in _execute_human.

        Args:
            approval_id: 审批请求 ID
            decision: 'approved' 或 'rejected'
            comment: 审批人备注

        Raises:
            KeyError: 如果 approval_id 不在等待列表中
            ValueError: 如果 decision 不是合法值
        """
        if decision not in ("approved", "rejected"):
            raise ValueError(f"Invalid decision: {decision!r}, must be 'approved' or 'rejected'")

        # 存储决策数据供等待中的 _execute_human 读取
        resolved_at = datetime.now(timezone.utc).isoformat()
        _approval_decisions[approval_id] = {
            "decision": decision,
            "comment": comment,
            "resolved_at": resolved_at,
        }

        # 唤醒等待中的协程
        event = _pending_approvals.get(approval_id)
        if event is not None:
            event.set()

        return {
            "approval_id": approval_id,
            "decision": decision,
            "comment": comment,
            "resolved_at": resolved_at,
        }

    async def _execute_sub_workflow(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Execute a sub-workflow by ID with variable mapping.

        Config keys:
            workflow_id: str - ID of the sub-workflow to load
            input_mapping: dict[str, str] - parent_var -> child_var mapping
            output_mapping: dict[str, str] - child_var -> parent_var mapping

        Raises:
            ValueError: if workflow_id is missing or loader is not set
            RuntimeError: if the sub-workflow fails
        """
        config = node.config
        workflow_id = config.get("workflow_id")
        input_mapping = config.get("input_mapping", {})
        output_mapping = config.get("output_mapping", {})

        if not workflow_id:
            raise ValueError("SUB_WORKFLOW node requires 'workflow_id' in config")

        if not self._sub_workflow_loader:
            raise ValueError(
                "SUB_WORKFLOW node requires a sub_workflow_loader. "
                "Call engine.set_sub_workflow_loader(loader) before executing."
            )

        # Map input variables: parent_var -> child_var
        child_vars = {}
        for parent_key, child_key in input_mapping.items():
            value = state.get_var(parent_key)
            if value is not None:
                child_vars[child_key] = value

        # Load sub-workflow definition via the loader
        logger.info(f"Loading sub-workflow {workflow_id} for node {node.id}")
        try:
            definition = await self._sub_workflow_loader(workflow_id)
        except Exception as e:
            raise RuntimeError(f"Failed to load sub-workflow {workflow_id}: {e}") from e

        if not definition or "nodes" not in definition:
            raise RuntimeError(
                f"Sub-workflow {workflow_id} returned invalid definition: missing 'nodes'"
            )

        # Build DAG from the sub-workflow definition
        child_dag = DAG()
        for node_def in definition["nodes"]:
            node_type_str = node_def.get("type", "code")
            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                raise ValueError(
                    f"Sub-workflow {workflow_id} has unsupported node type: {node_type_str}"
                )
            child_dag.add_node(WorkflowNode(
                id=node_def["id"],
                type=node_type,
                config=node_def.get("config", {}),
                retry_count=node_def.get("retry_count", 0),
                timeout=node_def.get("timeout", 60),
            ))

        for edge_def in definition.get("edges", []):
            edge_kwargs = {
                "source": edge_def["source"],
                "target": edge_def["target"],
            }
            if edge_def.get("condition") is not None:
                edge_kwargs["condition"] = edge_def["condition"]
            child_dag.add_edge(WorkflowEdge(**edge_kwargs))

        # Create a child engine with the same adapter and loader (supports nested sub-workflows)
        child_engine = WorkflowEngine()
        child_engine._llm_adapter = self._llm_adapter
        child_engine._sub_workflow_loader = self._sub_workflow_loader
        child_engine._timeout = self._timeout

        # Execute the sub-workflow
        logger.info(
            f"Executing sub-workflow {workflow_id} with {len(definition['nodes'])} nodes, "
            f"input vars: {list(child_vars.keys())}"
        )
        result = await child_engine.execute(child_dag, initial_vars=child_vars)

        # Map output variables: child_var -> parent_var
        output = result.get("output", {})
        for child_key, parent_key in output_mapping.items():
            value = output.get(child_key)
            if value is not None:
                state.set_var(parent_key, value)

        if result.get("status") == "failed":
            raise RuntimeError(
                f"Sub-workflow {workflow_id} failed: {result.get('error', 'unknown error')}"
            )

        logger.info(f"Sub-workflow {workflow_id} completed with status: {result.get('status')}")
        return {
            "status": "sub_workflow_completed",
            "node_id": node.id,
            "sub_workflow_id": workflow_id,
            "sub_status": result.get("status"),
            "sub_trace_id": result.get("trace_id"),
            "sub_output": output,
        }

    async def _execute_template(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Render a Jinja2 template using state variables.

        Config keys:
            template: str - Jinja2 template string
            variables_key: str - optional key in state to use as template context
        """
        from jinja2 import Environment, BaseLoader

        config = node.config
        template_str = config.get("template", "")
        if not template_str:
            return {"rendered": ""}

        variables_key = config.get("variables_key")
        if variables_key:
            context = state.get_var(variables_key, {})
            if not isinstance(context, dict):
                context = {"value": context}
        else:
            context = dict(state.variables)

        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        rendered = template.render(**context)
        return {"rendered": rendered}

    async def _execute_question_classifier(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Classify a question into predefined categories using LLM.

        Config keys:
            categories: list[str] - valid classification categories
            input_key: str - state variable containing the question
            model: str - optional model override
        """
        config = node.config
        categories = config.get("categories", [])
        input_key = config.get("input_key", "question")
        model = config.get("model", "")

        question = state.get_var(input_key, "")
        if not question:
            return {"category": categories[0] if categories else "unknown", "confidence": 0.0}

        if not self._llm_adapter:
            return {"category": categories[0] if categories else "unknown", "confidence": 0.0}

        categories_str = ", ".join(f'"{c}"' for c in categories)
        prompt = (
            f"Classify the following question into exactly one of these categories: [{categories_str}]. "
            f"Respond with ONLY the category name, nothing else.\n\n"
            f"Question: {question}"
        )

        try:
            response = await self._llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                max_tokens=50,
            )
            result = response.content.strip().strip('"').strip("'")
            if result in categories:
                return {"category": result, "confidence": 1.0}
            return {"category": categories[0] if categories else "unknown", "confidence": 0.5}
        except Exception:
            return {"category": categories[0] if categories else "unknown", "confidence": 0.0}

    async def _execute_parameter_extractor(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Extract structured parameters from natural language using LLM.

        Config keys:
            input_key: str - state variable containing the text
            parameters_schema: dict - mapping of parameter names to types
            model: str - optional model override
        """
        import json

        config = node.config
        input_key = config.get("input_key", "text")
        parameters_schema = config.get("parameters_schema", {})
        model = config.get("model", "")

        text = state.get_var(input_key, "")
        if not text:
            return {"parameters": {k: None for k in parameters_schema}}

        if not self._llm_adapter:
            return {"parameters": {k: None for k in parameters_schema}}

        schema_desc = json.dumps(parameters_schema, indent=2)
        prompt = (
            f"Extract the following parameters from the text below as JSON.\n"
            f"Parameters schema:\n{schema_desc}\n\n"
            f"Text: {text}\n\n"
            f"Respond with ONLY a valid JSON object matching the schema."
        )

        try:
            response = await self._llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                max_tokens=500,
            )
            result_text = response.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            extracted = json.loads(result_text)
            return {"parameters": extracted}
        except (json.JSONDecodeError, Exception):
            return {"parameters": {k: None for k in parameters_schema}}

    async def _execute_variable_aggregator(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Merge variables from multiple branches.

        Config keys:
            branches: list[dict] - each with "variable" (str) and "default" (Any)
        """
        config = node.config
        branches = config.get("branches", [])
        merged = {}

        for branch in branches:
            var_name = branch.get("variable", "")
            default = branch.get("default")
            merged[var_name] = state.get_var(var_name, default)

        return merged

    async def _execute_variable_assigner(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Modify runtime variables with various operations.

        Config keys:
            assignments: list[dict] - each with:
                variable: str - target variable name
                value: Any - the value to assign
                operation: str - "set", "append", or "merge"
        """
        config = node.config
        assignments = config.get("assignments", [])
        assigned = {}

        for assignment in assignments:
            var_name = assignment.get("variable", "")
            value = assignment.get("value")
            operation = assignment.get("operation", "set")

            if operation == "set":
                if isinstance(value, str) and value.startswith("$"):
                    value = state.evaluate_expression(value[1:])
                state.set_var(var_name, value)
                assigned[var_name] = value

            elif operation == "append":
                existing = state.get_var(var_name)
                if existing is None:
                    new_value = [value]
                elif isinstance(existing, list):
                    new_value = existing + [value]
                else:
                    new_value = [existing, value]
                state.set_var(var_name, new_value)
                assigned[var_name] = new_value

            elif operation == "merge":
                existing = state.get_var(var_name)
                if existing is None:
                    new_value = value if isinstance(value, dict) else {"value": value}
                elif isinstance(existing, dict) and isinstance(value, dict):
                    new_value = {**existing, **value}
                else:
                    new_value = value
                state.set_var(var_name, new_value)
                assigned[var_name] = new_value

            else:
                raise ValueError(f"Unknown operation: {operation}")

        return {"assigned": assigned}

    async def _execute_start(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Start node — pass through input variables."""
        return {"status": "started", "variables": dict(state.variables)}

    async def _execute_end(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """End node — collect output variables."""
        config = node.config
        output_vars = config.get("output_variables", [])
        if isinstance(output_vars, str):
            try:
                output_vars = json.loads(output_vars)
            except (json.JSONDecodeError, TypeError):
                output_vars = []
        result = {}
        if isinstance(output_vars, list):
            for var_def in output_vars:
                name = var_def.get("name", "") if isinstance(var_def, dict) else str(var_def)
                if name:
                    result[name] = state.get_var(name)
        else:
            result = dict(state.variables)
        return {"output": result}

    async def _execute_knowledge(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Knowledge/RAG retrieval node."""
        config = node.config
        kb_ids = config.get("knowledge_base_ids", [])
        query_var = config.get("query_variable", "{{input}}")
        top_k = config.get("top_k", 5)
        score_threshold = config.get("score_threshold", 0.5)

        query = self._resolve_variable(query_var, state)
        if not query:
            return {"documents": [], "query": ""}

        try:
            from app.engines.knowledge_engine.retriever.retriever import HybridRetriever
            retriever = HybridRetriever()
            results = []
            for kb_id in kb_ids:
                retrieved = await retriever.retrieve(
                    kb_id=kb_id, query=str(query), top_k=top_k
                )
                for r in retrieved:
                    if r.get("score", 0) >= score_threshold:
                        results.append(r)
            return {"documents": results, "query": str(query)}
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")
            return {"documents": [], "query": str(query), "error": str(e)}

    async def _execute_tool(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Tool execution node."""
        config = node.config
        tool_name = config.get("tool_name", "")
        tool_params = config.get("tool_params", {})
        if isinstance(tool_params, str):
            try:
                tool_params = json.loads(tool_params)
            except (json.JSONDecodeError, TypeError):
                tool_params = {}
        resolved_params = {}
        for k, v in tool_params.items():
            resolved_params[k] = self._resolve_variable(v, state) if isinstance(v, str) and "{{" in v else v
        try:
            from app.engines.tool_engine.executor import ToolExecutor
            executor = ToolExecutor()
            result = await executor.execute(tool_name, resolved_params)
            return {"result": result, "tool": tool_name}
        except Exception as e:
            return {"error": str(e), "tool": tool_name}

    async def _execute_answer(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Answer node for chatflow — formats the response."""
        config = node.config
        template = config.get("answer_template", "{{output}}")
        answer = self._resolve_variable(template, state)
        return {"answer": answer}

    async def _execute_variable(self, node: WorkflowNode, state: WorkflowState) -> Any:
        """Variable assignment/transformation node."""
        config = node.config
        operations = config.get("operations", [])
        if isinstance(operations, str):
            try:
                operations = json.loads(operations)
            except (json.JSONDecodeError, TypeError):
                operations = []
        results = {}
        for op in operations:
            var_name = op.get("variable", "")
            operator = op.get("operator", "assign")
            value = op.get("value", "")
            resolved_value = self._resolve_variable(value, state) if isinstance(value, str) and "{{" in value else value
            if operator == "assign":
                state.set_var(var_name, resolved_value)
            elif operator == "add":
                current = state.get_var(var_name) or 0
                state.set_var(var_name, current + resolved_value)
            elif operator == "append":
                current = state.get_var(var_name) or []
                if isinstance(current, list):
                    current.append(resolved_value)
                    state.set_var(var_name, current)
            results[var_name] = state.get_var(var_name)
        return {"variables": results}


def _cleanup_stale_approval_entries() -> None:
    """Remove entries older than 1 hour from _pending_approvals and _approval_decisions."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    stale_pending = [
        aid for aid, evt in _pending_approvals.items()
        # Events with no waiters and no corresponding decision are orphaned
        if aid not in _approval_decisions
    ]
    for aid in stale_pending:
        _pending_approvals.pop(aid, None)

    stale_decisions = []
    for aid, data in _approval_decisions.items():
        resolved_str = data.get("resolved_at")
        if resolved_str:
            try:
                resolved_dt = datetime.fromisoformat(resolved_str)
                if resolved_dt.tzinfo is None:
                    resolved_dt = resolved_dt.replace(tzinfo=timezone.utc)
                if resolved_dt < cutoff:
                    stale_decisions.append(aid)
            except (ValueError, TypeError):
                stale_decisions.append(aid)
        else:
            stale_decisions.append(aid)
    for aid in stale_decisions:
        _approval_decisions.pop(aid, None)


def cancel_pending_approval(approval_id: str) -> bool:
    """取消一个正在等待的审批，用于工作流异常终止时的清理。

    将审批标记为 rejected 并唤醒等待中的协程，使其能正常退出。

    Args:
        approval_id: 审批请求 ID

    Returns:
        True 如果找到并取消了对应的等待审批，False 如果该 ID 不存在
    """
    event = _pending_approvals.get(approval_id)
    if event is None:
        return False

    _approval_decisions[approval_id] = {
        "decision": "rejected",
        "comment": "Approval cancelled (workflow terminated)",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    event.set()
    return True

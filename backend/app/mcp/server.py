"""FastMCP-based MCP server exposing platform capabilities.

Tools (LLM-controlled):
- create_agent, update_agent, delete_agent, list_agents, send_message
- search_knowledge, list_knowledge_bases, evaluate_rag
- run_workflow, list_workflows
- get_audit_logs

Resources (app-controlled, read-only):
- agent://{agent_id}, kb://{kb_id}, workflow://{workflow_id}

Transport: stdio (for local clients like Claude Desktop)
"""
import asyncio
import hashlib
import hmac
import json
import logging
import sys
from datetime import datetime, UTC
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP protocol helpers (minimal JSON-RPC 2.0 implementation)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "create_agent",
        "description": "Create a new agent in the platform with specified configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name (required, max 100 chars)"
                },
                "description": {
                    "type": "string",
                    "description": "Agent description (optional)"
                },
                "model_provider": {
                    "type": "string",
                    "description": "Model provider (e.g., anthropic, openai)"
                },
                "model_name": {
                    "type": "string",
                    "description": "Model name (e.g., claude-3-5-sonnet-20241022)"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "System prompt for the agent"
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tool names available to the agent"
                },
                "knowledge_base_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of knowledge base IDs to attach"
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_agent",
        "description": "Update an existing agent's configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to update (required)"
                },
                "name": {
                    "type": "string",
                    "description": "New agent name"
                },
                "description": {
                    "type": "string",
                    "description": "New agent description"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Updated system prompt"
                },
                "model_provider": {
                    "type": "string",
                    "description": "Updated model provider"
                },
                "model_name": {
                    "type": "string",
                    "description": "Updated model name"
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Updated tool list"
                },
                "knowledge_base_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Updated knowledge base list"
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "delete_agent",
        "description": "Delete an agent from the platform",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to delete (required)"
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "list_agents",
        "description": "List all available agents with pagination support",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "Page number (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
                "size": {
                    "type": "integer",
                    "description": "Page size (default: 20, max: 100)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
        },
    },
    {
        "name": "send_message",
        "description": "Send a message to an agent and get a response",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to send message to (required)"
                },
                "message": {
                    "type": "string",
                    "description": "Message content to send (required)"
                },
            },
            "required": ["agent_id", "message"],
        },
    },
    {
        "name": "search_knowledge",
        "description": "Search a knowledge base for relevant documents using RAG",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (required)"
                },
                "kb_id": {
                    "type": "string",
                    "description": "Knowledge base ID to search (required)"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "strategy": {
                    "type": "string",
                    "description": "Retrieval strategy: vector, fulltext, hybrid, or graph_rag",
                    "enum": ["vector", "fulltext", "hybrid", "graph_rag"],
                    "default": "hybrid",
                },
            },
            "required": ["query", "kb_id"],
        },
    },
    {
        "name": "list_knowledge_bases",
        "description": "List all knowledge bases with their metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "Page number (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
                "size": {
                    "type": "integer",
                    "description": "Page size (default: 20, max: 100)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
        },
    },
    {
        "name": "evaluate_rag",
        "description": "Execute RAG evaluation on a knowledge base with test questions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_id": {
                    "type": "string",
                    "description": "Knowledge base ID to evaluate (required)"
                },
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of test questions to evaluate (required)",
                    "minItems": 1,
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to retrieve per question (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["kb_id", "questions"],
        },
    },
    {
        "name": "run_workflow",
        "description": "Execute a workflow with given input variables",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID to execute (required)"
                },
                "inputs": {
                    "type": "object",
                    "description": "Input variables for the workflow (key-value pairs)",
                    "additionalProperties": True,
                },
            },
            "required": ["workflow_id"],
        },
    },
    {
        "name": "list_workflows",
        "description": "List all workflows with their configurations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "Page number (default: 1)",
                    "default": 1,
                    "minimum": 1,
                },
                "size": {
                    "type": "integer",
                    "description": "Page size (default: 20, max: 100)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status: draft, active, or archived",
                    "enum": ["draft", "active", "archived"],
                },
            },
        },
    },
    {
        "name": "get_audit_logs",
        "description": "Retrieve audit logs for security and compliance monitoring",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Filter by action type: create, update, delete, login, logout"
                },
                "resource_type": {
                    "type": "string",
                    "description": "Filter by resource type: agent, knowledge_base, workflow, user"
                },
                "resource_id": {
                    "type": "string",
                    "description": "Filter by specific resource ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of logs to return (default: 50, max: 500)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                },
            },
        },
    },
    {
        "name": "check_safety",
        "description": "Check text for prompt injection, PII, and sensitive content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to check for safety issues (required)"
                },
                "check_type": {
                    "type": "string",
                    "description": "Type of check: injection, pii, sensitive, all",
                    "enum": ["injection", "pii", "sensitive", "all"],
                    "default": "all",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "manage_memory",
        "description": "Manage agent memory: store, retrieve, clear",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID (required)"
                },
                "operation": {
                    "type": "string",
                    "description": "Memory operation",
                    "enum": ["store", "retrieve", "clear", "summary"],
                },
                "key": {
                    "type": "string",
                    "description": "Memory key for store/retrieve"
                },
                "value": {
                    "type": "string",
                    "description": "Value to store"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of memories to retrieve",
                    "default": 10,
                },
            },
            "required": ["agent_id", "operation"],
        },
    },
    {
        "name": "list_models",
        "description": "List available model providers and configurations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider_type": {
                    "type": "string",
                    "description": "Filter by provider type",
                    "enum": ["openai", "anthropic", "azure_openai", "deepseek", "ollama", "custom"],
                },
                "model_type": {
                    "type": "string",
                    "description": "Filter by model type",
                    "enum": ["llm", "embedding", "reranker"],
                },
            },
        },
    },
    {
        "name": "manage_multi_agent",
        "description": "Manage multi-agent crews: create, list, execute",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["create_crew", "list_crews", "execute_crew", "get_crew"],
                },
                "crew_id": {
                    "type": "string",
                    "description": "Crew ID for execute/get operations"
                },
                "name": {
                    "type": "string",
                    "description": "Crew name for create operation"
                },
                "mode": {
                    "type": "string",
                    "description": "Crew execution mode",
                    "enum": ["sequential", "hierarchical", "parallel", "consensus"],
                    "default": "sequential",
                },
                "agent_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent IDs for the crew"
                },
                "task": {
                    "type": "string",
                    "description": "Task description for execute operation"
                },
            },
            "required": ["operation"],
        },
    },
    {
        "name": "get_platform_stats",
        "description": "Get platform usage statistics and metrics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metric_type": {
                    "type": "string",
                    "description": "Type of metrics to retrieve",
                    "enum": ["overview", "agents", "workflows", "knowledge", "usage"],
                    "default": "overview",
                },
                "period": {
                    "type": "string",
                    "description": "Time period for metrics",
                    "enum": ["today", "week", "month", "year"],
                    "default": "month",
                },
            },
        },
    },
]

RESOURCE_TEMPLATES = [
    {
        "uriTemplate": "agent://{agent_id}",
        "name": "Agent Configuration",
        "description": "Get agent configuration by ID",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "kb://{kb_id}",
        "name": "Knowledge Base Info",
        "description": "Get knowledge base information by ID",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "workflow://{workflow_id}",
        "name": "Workflow Definition",
        "description": "Get workflow definition by ID",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "audit://{limit}",
        "name": "Audit Logs",
        "description": "Get recent audit logs",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "memory://{agent_id}",
        "name": "Agent Memory",
        "description": "Get agent memory state",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "stats://{metric_type}",
        "name": "Platform Statistics",
        "description": "Get platform usage statistics",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "models://{provider_type}",
        "name": "Model Providers",
        "description": "List model providers and configurations",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "crew://{crew_id}",
        "name": "Multi-Agent Crew",
        "description": "Get crew configuration and status",
        "mimeType": "application/json",
    },
]


# ---------------------------------------------------------------------------
# MCP Server implementation
# ---------------------------------------------------------------------------

class MCPServer:
    """Minimal MCP server using JSON-RPC 2.0 over stdio."""

    def __init__(self) -> None:
        self._handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "resources/templates/list": self._handle_resource_templates,
            "ping": self._handle_ping,
        }
        self._start_time = datetime.now(UTC)
        self._authenticated = False

    async def run_stdio(self) -> None:
        """Run the MCP server over stdio."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout.buffer
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, asyncio.get_event_loop())

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                message = json.loads(line.decode("utf-8").strip())
                response = await self._dispatch(message)

                if response is not None:
                    response_bytes = json.dumps(response).encode("utf-8") + b"\n"
                    writer.write(response_bytes)
                    await writer.drain()

            except json.JSONDecodeError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("MCP server error: %s", exc)

    async def _dispatch(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Dispatch a JSON-RPC message to the appropriate handler."""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        # Notifications (no id) don't get responses
        if msg_id is None:
            return None

        handler = self._handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        # Authentication gate: "initialize" is the only unauthenticated method.
        # After initialize, the client must provide a valid API key via the
        # "apiKey" field in the initialize params, or send an "auth" method.
        if method == "initialize":
            # Extract API key from initialize params if present
            api_key = params.get("apiKey", "")
            self._authenticated = self._verify_api_key(api_key)
        elif not self._authenticated:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32001,
                    "message": "Authentication required. Provide apiKey in initialize params.",
                },
            }

        try:
            result = await handler(params)
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        except Exception as exc:
            logger.exception("Handler error for method %s", method)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(exc)},
            }

    @staticmethod
    def _verify_api_key(api_key: str) -> bool:
        """Verify the provided MCP API key using constant-time comparison.

        Returns True if the key matches the configured MCP_API_KEY.
        Rejects empty or missing keys.
        """
        if not api_key:
            return False
        from app.config import settings
        configured_key = settings.MCP_API_KEY
        if not configured_key:
            logger.error("MCP_API_KEY is not configured; rejecting all MCP access")
            return False
        return hmac.compare_digest(api_key.encode("utf-8"), configured_key.encode("utf-8"))

    async def _handle_initialize(self, params: dict) -> dict:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "serverInfo": {
                "name": "agent-engine-platform",
                "version": "1.0.0",
            },
        }

    async def _handle_tools_list(self, params: dict) -> dict:
        return {"tools": TOOL_DEFINITIONS}

    async def _handle_tools_call(self, params: dict) -> dict:
        """Handle tool calls by dispatching to platform services."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = await self._execute_tool(tool_name, arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
            }
        except Exception as exc:
            logger.exception("Tool execution error: %s", tool_name)
            return {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            }

    async def _execute_tool(self, name: str, args: dict) -> Any:
        """Execute a tool by name with proper error handling."""
        from app.core.database import async_session

        try:
            if name == "create_agent":
                async with async_session() as db:
                    from app.platform.agent_service.agent_service import AgentService
                    svc = AgentService(db)
                    return await svc.create(
                        tenant_id="mcp",
                        data={
                            "name": args["name"],
                            "description": args.get("description", ""),
                            "model_provider": args.get("model_provider", ""),
                            "model_name": args.get("model_name", ""),
                            "system_prompt": args.get("system_prompt", ""),
                            "tools": args.get("tools", []),
                            "knowledge_base_ids": args.get("knowledge_base_ids", []),
                        },
                    )

            elif name == "update_agent":
                async with async_session() as db:
                    from app.platform.agent_service.agent_service import AgentService
                    svc = AgentService(db)
                    if "agent_id" not in args:
                        raise ValueError("agent_id is required for update_agent")
                    update_data = {k: v for k, v in args.items() if k != "agent_id"}
                    return await svc.update(
                        agent_id=args["agent_id"],
                        tenant_id="mcp",
                        data=update_data,
                    )

            elif name == "delete_agent":
                async with async_session() as db:
                    from app.platform.agent_service.agent_service import AgentService
                    svc = AgentService(db)
                    if "agent_id" not in args:
                        raise ValueError("agent_id is required for delete_agent")
                    await svc.delete(
                        agent_id=args["agent_id"],
                        tenant_id="mcp",
                    )
                    return {"success": True, "message": "Agent deleted successfully"}

            elif name == "list_agents":
                async with async_session() as db:
                    from app.platform.agent_service.agent_service import AgentService
                    svc = AgentService(db)
                    page = args.get("page", 1)
                    size = min(args.get("size", 20), 100)
                    return await svc.list(tenant_id="mcp", page=page, size=size)

            elif name == "send_message":
                async with async_session() as db:
                    from app.platform.conversation_service.conversation_service import ConversationService
                    svc = ConversationService(db)
                    return await svc.send_message(
                        agent_id=args["agent_id"],
                        content=args["message"],
                        tenant_id="mcp",
                        user_id="mcp",
                    )

            elif name == "search_knowledge":
                async with async_session() as db:
                    from app.engines.knowledge_engine.rag_pipeline import RAGPipeline
                    pipeline = RAGPipeline(db)
                    kb_id = args.get("kb_id")
                    if not kb_id:
                        raise ValueError("kb_id is required for search_knowledge")
                    return await pipeline.query(
                        query=args["query"],
                        knowledge_base_id=kb_id,
                        collection_name=f"kb_{kb_id}",
                        es_index=f"kb_{kb_id}",
                        strategy=args.get("strategy", "hybrid"),
                        top_k=args.get("top_k", 5),
                    )

            elif name == "list_knowledge_bases":
                async with async_session() as db:
                    from sqlalchemy import select, func
                    from app.models.base import KnowledgeBaseModel
                    page = args.get("page", 1)
                    size = min(args.get("size", 20), 100)

                    count_result = await db.execute(
                        select(func.count()).where(KnowledgeBaseModel.tenant_id == "mcp")
                    )
                    total = count_result.scalar()

                    stmt = (
                        select(KnowledgeBaseModel)
                        .where(KnowledgeBaseModel.tenant_id == "mcp")
                        .offset((page - 1) * size)
                        .limit(size)
                    )
                    result = await db.execute(stmt)
                    kbs = result.scalars().all()

                    return {
                        "items": [
                            {
                                "id": kb.id,
                                "name": kb.name,
                                "description": kb.description,
                                "document_count": kb.document_count,
                                "embedding_model": kb.embedding_model,
                                "retrieval_mode": kb.retrieval_mode,
                                "status": kb.status,
                                "created_at": kb.created_at.isoformat() if kb.created_at else None,
                            }
                            for kb in kbs
                        ],
                        "total": total,
                        "page": page,
                        "size": size,
                    }

            elif name == "evaluate_rag":
                async with async_session() as db:
                    from app.engines.knowledge_engine.rag_pipeline import RAGPipeline
                    pipeline = RAGPipeline(db)
                    kb_id = args.get("kb_id")
                    questions = args.get("questions", [])
                    top_k = args.get("top_k", 5)

                    if not kb_id:
                        raise ValueError("kb_id is required for evaluate_rag")
                    if not questions:
                        raise ValueError("questions list is required for evaluate_rag")

                    results = []
                    for question in questions:
                        try:
                            response = await pipeline.query(
                                query=question,
                                knowledge_base_id=kb_id,
                                collection_name=f"kb_{kb_id}",
                                es_index=f"kb_{kb_id}",
                                top_k=top_k,
                            )
                            results.append({
                                "question": question,
                                "answer": response.get("answer", ""),
                                "source_count": len(response.get("sources", [])),
                                "confidence": response.get("confidence", 0),
                            })
                        except Exception as e:
                            results.append({
                                "question": question,
                                "error": str(e),
                            })

                    return {
                        "kb_id": kb_id,
                        "evaluations": results,
                        "total_questions": len(questions),
                        "successful": sum(1 for r in results if "error" not in r),
                    }

            elif name == "run_workflow":
                async with async_session() as db:
                    from app.platform.workflow_service.workflow_service import WorkflowExecutionService
                    svc = WorkflowExecutionService(db)
                    return await svc.start_execution(
                        workflow_id=args["workflow_id"],
                        tenant_id="mcp",
                        variables=args.get("inputs", {}),
                    )

            elif name == "list_workflows":
                async with async_session() as db:
                    from sqlalchemy import select, func, and_
                    from app.models.base import WorkflowModel
                    page = args.get("page", 1)
                    size = min(args.get("size", 20), 100)
                    status_filter = args.get("status")

                    filters = [WorkflowModel.tenant_id == "mcp"]
                    if status_filter:
                        filters.append(WorkflowModel.status == status_filter)

                    count_result = await db.execute(
                        select(func.count()).where(and_(*filters))
                    )
                    total = count_result.scalar()

                    stmt = (
                        select(WorkflowModel)
                        .where(and_(*filters))
                        .offset((page - 1) * size)
                        .limit(size)
                    )
                    result = await db.execute(stmt)
                    workflows = result.scalars().all()

                    return {
                        "items": [
                            {
                                "id": wf.id,
                                "name": wf.name,
                                "description": wf.description,
                                "status": wf.status,
                                "version": wf.version,
                                "node_count": len(wf.nodes) if wf.nodes else 0,
                                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                            }
                            for wf in workflows
                        ],
                        "total": total,
                        "page": page,
                        "size": size,
                    }

            elif name == "get_audit_logs":
                async with async_session() as db:
                    from sqlalchemy import select, and_, desc
                    from app.models.base import OperationLogModel

                    limit = min(args.get("limit", 50), 500)
                    filters = [OperationLogModel.tenant_id == "mcp"]

                    if "action" in args:
                        filters.append(OperationLogModel.action == args["action"])
                    if "resource_type" in args:
                        filters.append(OperationLogModel.resource_type == args["resource_type"])
                    if "resource_id" in args:
                        filters.append(OperationLogModel.resource_id == args["resource_id"])

                    stmt = (
                        select(OperationLogModel)
                        .where(and_(*filters))
                        .order_by(desc(OperationLogModel.created_at))
                        .limit(limit)
                    )
                    result = await db.execute(stmt)
                    logs = result.scalars().all()

                    return {
                        "items": [
                            {
                                "id": log.id,
                                "action": log.action,
                                "resource_type": log.resource_type,
                                "resource_id": log.resource_id,
                                "user_id": log.user_id,
                                "details": log.details or {},
                                "ip_address": log.ip_address,
                                "created_at": log.created_at.isoformat() if log.created_at else None,
                            }
                            for log in logs
                        ],
                        "count": len(logs),
                        "limit": limit,
                    }

            elif name == "check_safety":
                from app.engines.safety_engine import SafetyEngine
                engine = SafetyEngine()
                text = args.get("text", "")
                check_type = args.get("check_type", "all")

                if not text:
                    raise ValueError("text is required for check_safety")

                results = {}
                if check_type in ["injection", "all"]:
                    results["injection"] = await engine.check_injection(text)
                if check_type in ["pii", "all"]:
                    results["pii"] = await engine.detect_pii(text)
                if check_type in ["sensitive", "all"]:
                    results["sensitive"] = await engine.check_sensitive(text)

                return {
                    "text_length": len(text),
                    "check_type": check_type,
                    "results": results,
                    "is_safe": all(
                        r.get("is_safe", True) if isinstance(r, dict) else True
                        for r in results.values()
                    ),
                }

            elif name == "manage_memory":
                from app.engines.memory_engine import MemoryEngine
                engine = MemoryEngine()
                agent_id = args.get("agent_id")
                operation = args.get("operation")

                if not agent_id:
                    raise ValueError("agent_id is required")

                if operation == "store":
                    key = args.get("key", "")
                    value = args.get("value", "")
                    if not key or not value:
                        raise ValueError("key and value are required for store operation")
                    await engine.store(agent_id=agent_id, key=key, value=value)
                    return {"success": True, "message": f"Memory stored: {key}"}

                elif operation == "retrieve":
                    limit = args.get("limit", 10)
                    memories = await engine.retrieve(agent_id=agent_id, limit=limit)
                    return {"memories": memories, "count": len(memories)}

                elif operation == "clear":
                    await engine.clear(agent_id=agent_id)
                    return {"success": True, "message": "Memory cleared"}

                elif operation == "summary":
                    summary = await engine.get_summary(agent_id=agent_id)
                    return {"summary": summary}

                else:
                    raise ValueError(f"Unknown memory operation: {operation}")

            elif name == "list_models":
                async with async_session() as db:
                    from sqlalchemy import select, and_
                    from app.models.base import ModelProviderModel, ModelConfigModel

                    provider_type = args.get("provider_type")
                    model_type = args.get("model_type")

                    # Get providers
                    provider_filters = [ModelProviderModel.tenant_id == "mcp"]
                    if provider_type:
                        provider_filters.append(ModelProviderModel.provider_type == provider_type)

                    stmt = select(ModelProviderModel).where(and_(*provider_filters))
                    result = await db.execute(stmt)
                    providers = result.scalars().all()

                    # Get configs
                    config_filters = []
                    if model_type:
                        config_filters.append(ModelConfigModel.model_type == model_type)

                    stmt = select(ModelConfigModel).where(and_(*config_filters)) if config_filters else select(ModelConfigModel)
                    result = await db.execute(stmt)
                    configs = result.scalars().all()

                    return {
                        "providers": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "provider_type": p.provider_type,
                                "status": p.status,
                            }
                            for p in providers
                        ],
                        "configs": [
                            {
                                "id": c.id,
                                "model_name": c.model_name,
                                "model_type": c.model_type,
                                "display_name": c.display_name,
                                "is_default": c.is_default,
                                "enabled": c.enabled,
                            }
                            for c in configs
                        ],
                    }

            elif name == "manage_multi_agent":
                from app.engines.multi_agent import MultiAgentEngine
                engine = MultiAgentEngine()
                operation = args.get("operation")

                if operation == "create_crew":
                    name = args.get("name", "")
                    mode = args.get("mode", "sequential")
                    agent_ids = args.get("agent_ids", [])
                    if not name or not agent_ids:
                        raise ValueError("name and agent_ids are required for create_crew")
                    crew = await engine.create_crew(
                        name=name,
                        mode=mode,
                        agent_ids=agent_ids,
                        tenant_id="mcp",
                    )
                    return {"crew": crew, "message": "Crew created successfully"}

                elif operation == "list_crews":
                    crews = await engine.list_crews(tenant_id="mcp")
                    return {"crews": crews, "count": len(crews)}

                elif operation == "execute_crew":
                    crew_id = args.get("crew_id")
                    task = args.get("task", "")
                    if not crew_id or not task:
                        raise ValueError("crew_id and task are required for execute_crew")
                    result = await engine.execute_crew(
                        crew_id=crew_id,
                        task=task,
                        tenant_id="mcp",
                    )
                    return {"result": result, "crew_id": crew_id}

                elif operation == "get_crew":
                    crew_id = args.get("crew_id")
                    if not crew_id:
                        raise ValueError("crew_id is required for get_crew")
                    crew = await engine.get_crew(crew_id=crew_id, tenant_id="mcp")
                    return {"crew": crew}

                else:
                    raise ValueError(f"Unknown multi-agent operation: {operation}")

            elif name == "get_platform_stats":
                async with async_session() as db:
                    from sqlalchemy import select, func, and_
                    from app.models.base import AgentModel, WorkflowModel, KnowledgeBaseModel, ConversationModel
                    from datetime import datetime, timedelta, UTC

                    metric_type = args.get("metric_type", "overview")
                    period = args.get("period", "month")

                    # Calculate date range
                    now = datetime.now(UTC)
                    if period == "today":
                        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif period == "week":
                        start_date = now - timedelta(days=7)
                    elif period == "month":
                        start_date = now - timedelta(days=30)
                    elif period == "year":
                        start_date = now - timedelta(days=365)
                    else:
                        start_date = now - timedelta(days=30)

                    stats = {}

                    if metric_type in ["overview", "agents"]:
                        result = await db.execute(
                            select(func.count()).where(AgentModel.tenant_id == "mcp")
                        )
                        stats["total_agents"] = result.scalar() or 0

                    if metric_type in ["overview", "workflows"]:
                        result = await db.execute(
                            select(func.count()).where(WorkflowModel.tenant_id == "mcp")
                        )
                        stats["total_workflows"] = result.scalar() or 0

                    if metric_type in ["overview", "knowledge"]:
                        result = await db.execute(
                            select(func.count()).where(KnowledgeBaseModel.tenant_id == "mcp")
                        )
                        stats["total_knowledge_bases"] = result.scalar() or 0

                    if metric_type in ["overview", "usage"]:
                        result = await db.execute(
                            select(func.count()).where(ConversationModel.tenant_id == "mcp")
                        )
                        stats["total_conversations"] = result.scalar() or 0

                    return {
                        "metric_type": metric_type,
                        "period": period,
                        "stats": stats,
                        "generated_at": now.isoformat(),
                    }

            raise ValueError(f"Unknown tool: {name}")

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error("Error executing tool %s: %s", name, e)
            raise RuntimeError(f"Tool execution failed: {str(e)}") from e

    async def _handle_resources_list(self, params: dict) -> dict:
        return {"resources": []}

    async def _handle_resources_read(self, params: dict) -> dict:
        """Read a resource by URI."""
        uri = params.get("uri", "")
        from app.core.database import async_session

        try:
            if uri.startswith("agent://"):
                agent_id = uri[len("agent://"):]
                async with async_session() as db:
                    from sqlalchemy import select
                    from app.models.base import AgentModel
                    stmt = select(AgentModel).where(AgentModel.id == agent_id)
                    result = await db.execute(stmt)
                    agent = result.scalar_one_or_none()
                    if not agent:
                        raise ValueError(f"Agent not found: {agent_id}")
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "id": agent.id,
                                "name": agent.name,
                                "description": agent.description,
                                "model_provider": agent.model_provider,
                                "model_name": agent.model_name,
                                "tools": agent.tools,
                                "status": agent.status,
                            }, ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("kb://"):
                kb_id = uri[len("kb://"):]
                async with async_session() as db:
                    from sqlalchemy import select
                    from app.models.base import KnowledgeBaseModel
                    stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
                    result = await db.execute(stmt)
                    kb = result.scalar_one_or_none()
                    if not kb:
                        raise ValueError(f"Knowledge base not found: {kb_id}")
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "id": kb.id,
                                "name": kb.name,
                                "description": kb.description,
                                "document_count": kb.document_count,
                                "status": kb.status,
                                "embedding_model": kb.embedding_model,
                                "retrieval_mode": kb.retrieval_mode,
                            }, ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("workflow://"):
                wf_id = uri[len("workflow://"):]
                async with async_session() as db:
                    from sqlalchemy import select
                    from app.models.base import WorkflowModel
                    stmt = select(WorkflowModel).where(WorkflowModel.id == wf_id)
                    result = await db.execute(stmt)
                    wf = result.scalar_one_or_none()
                    if not wf:
                        raise ValueError(f"Workflow not found: {wf_id}")
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "id": wf.id,
                                "name": wf.name,
                                "description": wf.description,
                                "dag_config": wf.dag_config,
                                "status": wf.status,
                                "version": wf.version,
                            }, ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("audit://"):
                limit = int(uri[len("audit://"):]) if uri[len("audit://"):].isdigit() else 50
                async with async_session() as db:
                    from sqlalchemy import select, desc
                    from app.models.base import OperationLogModel
                    stmt = (
                        select(OperationLogModel)
                        .order_by(desc(OperationLogModel.created_at))
                        .limit(min(limit, 500))
                    )
                    result = await db.execute(stmt)
                    logs = result.scalars().all()
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps([
                                {
                                    "id": log.id,
                                    "action": log.action,
                                    "resource_type": log.resource_type,
                                    "resource_id": log.resource_id,
                                    "user_id": log.user_id,
                                    "created_at": log.created_at.isoformat() if log.created_at else None,
                                }
                                for log in logs
                            ], ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("memory://"):
                agent_id = uri[len("memory://"):]
                from app.engines.memory_engine import MemoryEngine
                engine = MemoryEngine()
                memories = await engine.retrieve(agent_id=agent_id, limit=20)
                summary = await engine.get_summary(agent_id=agent_id)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "agent_id": agent_id,
                            "memories": memories,
                            "summary": summary,
                            "count": len(memories),
                        }, ensure_ascii=False),
                    }]
                }

            elif uri.startswith("stats://"):
                metric_type = uri[len("stats://"):] or "overview"
                async with async_session() as db:
                    from sqlalchemy import select, func
                    from app.models.base import AgentModel, WorkflowModel, KnowledgeBaseModel
                    stats = {}
                    if metric_type in ["overview", "agents"]:
                        result = await db.execute(select(func.count()).where(AgentModel.tenant_id == "mcp"))
                        stats["total_agents"] = result.scalar() or 0
                    if metric_type in ["overview", "workflows"]:
                        result = await db.execute(select(func.count()).where(WorkflowModel.tenant_id == "mcp"))
                        stats["total_workflows"] = result.scalar() or 0
                    if metric_type in ["overview", "knowledge"]:
                        result = await db.execute(select(func.count()).where(KnowledgeBaseModel.tenant_id == "mcp"))
                        stats["total_knowledge_bases"] = result.scalar() or 0
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({"metric_type": metric_type, "stats": stats}, ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("models://"):
                provider_type = uri[len("models://"):] or None
                async with async_session() as db:
                    from sqlalchemy import select
                    from app.models.base import ModelProviderModel
                    filters = [ModelProviderModel.tenant_id == "mcp"]
                    if provider_type:
                        filters.append(ModelProviderModel.provider_type == provider_type)
                    from sqlalchemy import and_
                    stmt = select(ModelProviderModel).where(and_(*filters))
                    result = await db.execute(stmt)
                    providers = result.scalars().all()
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps([
                                {"id": p.id, "name": p.name, "type": p.provider_type, "status": p.status}
                                for p in providers
                            ], ensure_ascii=False),
                        }]
                    }

            elif uri.startswith("crew://"):
                crew_id = uri[len("crew://"):]
                from app.engines.multi_agent import MultiAgentEngine
                engine = MultiAgentEngine()
                crew = await engine.get_crew(crew_id=crew_id, tenant_id="mcp")
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(crew, ensure_ascii=False),
                    }]
                }

            raise ValueError(f"Unsupported resource URI: {uri}")

        except Exception as exc:
            logger.exception("Resource read error: %s", uri)
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Error: {exc}",
                }]
            }

    async def _handle_resource_templates(self, params: dict) -> dict:
        return {"resourceTemplates": RESOURCE_TEMPLATES}

    async def _handle_ping(self, params: dict) -> dict:
        uptime = datetime.now(UTC) - self._start_time
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "server": "agent-engine-platform",
            "version": "1.0.0",
        }

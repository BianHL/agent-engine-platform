"""Unified API schemas - Common and re-exports.

This file now only contains common schemas and re-exports domain-specific schemas
for backward compatibility.

For new code, prefer importing from domain-specific modules:
- from app.schemas.auth import LoginRequest, TokenResponse
- from app.schemas.agent import CreateAgentRequest, AgentResponse
- from app.schemas.knowledge import CreateKnowledgeBaseRequest
etc.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Common Schemas
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int


class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class StatusResponse(BaseModel):
    status: str


class LogoutResponse(BaseModel):
    message: str
    revoked_at: Optional[str] = None


class MCPServerConfig(BaseModel):
    name: str
    transport: str = "stdio"  # stdio / sse
    tools: list = []
    resources: list = []


class SSOProviderRequest(BaseModel):
    provider_name: str
    config: dict = {}
    enabled: bool = True


class SSOProviderResponse(BaseModel):
    id: str
    provider_name: str
    config: dict
    enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Re-exports for backward compatibility
# ---------------------------------------------------------------------------

# Auth
from app.schemas.auth import (  # noqa: E402, F401
    LoginRequest,
    RegisterUserRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
)

# Agent
from app.schemas.agent import (  # noqa: E402, F401
    AgentResponse,
    CreateAgentRequest,
    UpdateAgentRequest,
)

# Knowledge
from app.schemas.knowledge import (  # noqa: E402, F401
    CreateKnowledgeBaseRequest,
    DocumentResponse,
    KnowledgeBaseResponse,
)

# Conversation
from app.schemas.conversation import (  # noqa: E402, F401
    AddMessageRequest,
    ChatCompletionResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)

# Workflow
from app.schemas.workflow import (  # noqa: E402, F401
    CreateTriggerRequest,
    CreateWorkflowRequest,
    RunWorkflowRequest,
    TriggerResponse,
    UpdateWorkflowRequest,
    WorkflowExecutionResponse,
    WorkflowResponse,
)

# Task
from app.schemas.task import (  # noqa: E402, F401
    StatusResponse as TaskStatusResponseClass,
    TaskStatusResponse,
)

# Tenant
from app.schemas.user import (  # noqa: E402, F401
    CreateTenantRequest,
    TenantResponse,
    UpdateTenantFeaturesRequest,
    UpdateTenantQuotaRequest,
)

# Memory
from app.schemas.memory import (  # noqa: E402, F401
    MemoryContextResponse,
    MemorySearchRequest,
)

# Usage & Models
from app.schemas.usage import (  # noqa: E402, F401
    CreateModelConfigRequest,
    CreateProviderRequest,
    DailyUsageResponse,
    ModelConfigResponse,
    ModelProviderResponse,
    ModelUsageResponse,
    UsageSummaryResponse,
)

# Tool
from app.schemas.tool import (  # noqa: E402, F401
    CreateToolRequest,
    ExecuteToolRequest,
    ToolResponse,
)

# Feedback
from app.schemas.feedback import (  # noqa: E402, F401
    CreateAnnotationRequest,
    CreateFeedbackRequest,
    UpdateFeedbackRequest,
)

# Audit
from app.schemas.audit import (  # noqa: E402, F401
    OperationLogResponse,
)

# RBAC
from app.schemas.rbac import (  # noqa: E402, F401
    CreateRoleRequest,
    RolePermissionResponse,
    RoleResponse,
    UpdateRolePermissionsRequest,
)

# Token
from app.schemas.token import (  # noqa: E402, F401
    CreateTokenRequest,
    TokenCreatedResponse,
    TokenResponseItem,
    UpdateTokenRequest,
)

# Webhook
from app.schemas.webhook import (  # noqa: E402, F401
    CreateWebhookRequest,
    WebhookEventResponse,
    WebhookResponse,
)

# Evaluation
from app.schemas.evaluation import (  # noqa: E402, F401
    CreateEvaluationRequest,
    EvaluationResponse,
    EvaluationResultResponse,
    EvaluationRunResponse,
)

# Multi-Agent
from app.schemas.multi_agent import (  # noqa: E402, F401
    CreateCrewRequest,
    CrewResponse,
    HandoffRequest,
)

"""API Schemas - Unified exports.

This module re-exports all schemas for backward compatibility.
Existing imports like `from app.schemas.api import AgentResponse` will continue to work.

New code can use:
- `from app.schemas import AgentResponse` (recommended)
- `from app.schemas.agent import AgentResponse` (domain-specific)
"""

# Common
from app.schemas.api import (  # noqa: F401
    ErrorResponse,
    MCPServerConfig,
    PaginatedResponse,
    StatusResponse,
)

# Auth
from app.schemas.auth import (  # noqa: F401
    LoginRequest,
    RegisterUserRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
)

# Agent
from app.schemas.agent import (  # noqa: F401
    AgentResponse,
    CreateAgentRequest,
    UpdateAgentRequest,
)

# Knowledge
from app.schemas.knowledge import (  # noqa: F401
    CreateKnowledgeBaseRequest,
    DocumentResponse,
    KnowledgeBaseResponse,
)

# Conversation
from app.schemas.conversation import (  # noqa: F401
    AddMessageRequest,
    ChatCompletionResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)

# Workflow
from app.schemas.workflow import (  # noqa: F401
    CreateTriggerRequest,
    CreateWorkflowRequest,
    RunWorkflowRequest,
    TriggerResponse,
    UpdateWorkflowRequest,
    WorkflowExecutionResponse,
    WorkflowResponse,
)

# Task
from app.schemas.task import (  # noqa: F401
    StatusResponse,
    TaskStatusResponse,
)

# Tenant
from app.schemas.user import (  # noqa: F401
    CreateTenantRequest,
    TenantResponse,
    UpdateTenantFeaturesRequest,
    UpdateTenantQuotaRequest,
)

# Memory
from app.schemas.memory import (  # noqa: F401
    MemoryContextResponse,
    MemorySearchRequest,
)

# Usage & Models
from app.schemas.usage import (  # noqa: F401
    CreateModelConfigRequest,
    CreateProviderRequest,
    DailyUsageResponse,
    ModelConfigResponse,
    ModelProviderResponse,
    ModelUsageResponse,
    UsageSummaryResponse,
)

# Tool
from app.schemas.tool import (  # noqa: F401
    CreateToolRequest,
    ExecuteToolRequest,
    ToolResponse,
)

# Feedback
from app.schemas.feedback import (  # noqa: F401
    CreateAnnotationRequest,
    CreateFeedbackRequest,
    UpdateFeedbackRequest,
)

# Audit
from app.schemas.audit import (  # noqa: F401
    OperationLogResponse,
)

# RBAC
from app.schemas.rbac import (  # noqa: F401
    CreateRoleRequest,
    RolePermissionResponse,
    RoleResponse,
    UpdateRolePermissionsRequest,
)

# Token
from app.schemas.token import (  # noqa: F401
    CreateTokenRequest,
    TokenCreatedResponse,
    TokenResponseItem,
    UpdateTokenRequest,
)

# Webhook
from app.schemas.webhook import (  # noqa: F401
    CreateWebhookRequest,
    WebhookEventResponse,
    WebhookResponse,
)

# Evaluation
from app.schemas.evaluation import (  # noqa: F401
    CreateEvaluationRequest,
    EvaluationResponse,
    EvaluationResultResponse,
    EvaluationRunResponse,
)

# Multi-Agent
from app.schemas.multi_agent import (  # noqa: F401
    CreateCrewRequest,
    CrewResponse,
    HandoffRequest,
)

# Marketplace
from app.schemas.marketplace import (  # noqa: F401
    CloneResponse,
    CreateMarketplaceItemRequest,
    CreateRatingRequest,
    FreezeRequest,
    MarketplaceItemResponse,
    MarketplaceListItemResponse,
    MarketplaceRatingResponse,
    MarketplaceReviewResponse,
    MarketplaceStatsResponse,
    PromoteRequest,
    ReviewActionRequest,
    SubmitForReviewRequest,
    TakedownRequest,
    UpdateMarketplaceItemRequest,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "ErrorResponse",
    "StatusResponse",
    "MCPServerConfig",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "RegisterUserRequest",
    "UpdateUserRequest",
    # Agent
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "AgentResponse",
    # Knowledge
    "CreateKnowledgeBaseRequest",
    "KnowledgeBaseResponse",
    "DocumentResponse",
    # Conversation
    "CreateConversationRequest",
    "ConversationResponse",
    "MessageResponse",
    "AddMessageRequest",
    "ChatCompletionResponse",
    # Workflow
    "CreateWorkflowRequest",
    "UpdateWorkflowRequest",
    "WorkflowResponse",
    "WorkflowExecutionResponse",
    "RunWorkflowRequest",
    "CreateTriggerRequest",
    "TriggerResponse",
    # Task
    "TaskStatusResponse",
    "StatusResponse",
    # Tenant
    "CreateTenantRequest",
    "TenantResponse",
    "UpdateTenantFeaturesRequest",
    "UpdateTenantQuotaRequest",
    # Memory
    "MemoryContextResponse",
    "MemorySearchRequest",
    # Usage & Models
    "UsageSummaryResponse",
    "DailyUsageResponse",
    "ModelUsageResponse",
    "CreateProviderRequest",
    "CreateModelConfigRequest",
    "ModelProviderResponse",
    "ModelConfigResponse",
    # Tool
    "CreateToolRequest",
    "ToolResponse",
    "ExecuteToolRequest",
    # Feedback
    "CreateFeedbackRequest",
    "UpdateFeedbackRequest",
    "CreateAnnotationRequest",
    # Audit
    "OperationLogResponse",
    # RBAC
    "CreateRoleRequest",
    "RoleResponse",
    "UpdateRolePermissionsRequest",
    "RolePermissionResponse",
    # Token
    "CreateTokenRequest",
    "TokenResponseItem",
    "TokenCreatedResponse",
    "UpdateTokenRequest",
    # Webhook
    "CreateWebhookRequest",
    "WebhookResponse",
    "WebhookEventResponse",
    # Evaluation
    "CreateEvaluationRequest",
    "EvaluationResponse",
    "EvaluationRunResponse",
    "EvaluationResultResponse",
    # Multi-Agent
    "CreateCrewRequest",
    "CrewResponse",
    "HandoffRequest",
    # Marketplace
    "CloneResponse",
    "CreateMarketplaceItemRequest",
    "CreateRatingRequest",
    "FreezeRequest",
    "MarketplaceItemResponse",
    "MarketplaceListItemResponse",
    "MarketplaceRatingResponse",
    "MarketplaceReviewResponse",
    "MarketplaceStatsResponse",
    "PromoteRequest",
    "ReviewActionRequest",
    "SubmitForReviewRequest",
    "TakedownRequest",
    "UpdateMarketplaceItemRequest",
]

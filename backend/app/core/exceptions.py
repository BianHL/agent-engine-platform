class AgentEngineError(Exception):
    """Base exception for all Agent Engine errors."""
    pass


class ModelNotFoundError(AgentEngineError):
    """Requested model does not exist or is not configured."""
    pass


class AllProvidersUnavailableError(AgentEngineError):
    """All configured providers for a model are currently unavailable."""
    pass


class RateLimitExceededError(AgentEngineError):
    """Rate limit has been exceeded for the tenant or user."""
    pass


class NoFallbackModelError(AgentEngineError):
    """No fallback model is configured when the primary model fails."""
    pass


class UnsupportedFileTypeError(AgentEngineError):
    """The provided file type is not supported."""
    pass


class ToolNotFoundError(AgentEngineError):
    """Requested tool does not exist in the agent's tool registry."""
    pass


class KnowledgeBaseNotFoundError(AgentEngineError):
    """Requested knowledge base does not exist."""
    pass


class DocumentNotFoundError(AgentEngineError):
    """Requested document does not exist in the knowledge base."""
    pass


class PermissionDeniedError(AgentEngineError):
    """User does not have permission to perform the requested action."""
    pass


class TenantNotFoundError(AgentEngineError):
    """Requested tenant does not exist."""
    pass

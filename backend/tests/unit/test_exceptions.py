"""Unit tests for Exception hierarchy"""
import pytest
from app.core.exceptions import (
    AgentEngineError,
    ModelNotFoundError,
    AllProvidersUnavailableError,
    RateLimitExceededError,
    NoFallbackModelError,
    UnsupportedFileTypeError,
    ToolNotFoundError,
    KnowledgeBaseNotFoundError,
    DocumentNotFoundError,
    PermissionDeniedError,
    TenantNotFoundError,
)


def test_base_exception():
    with pytest.raises(AgentEngineError):
        raise AgentEngineError("test")


def test_model_not_found():
    with pytest.raises(ModelNotFoundError):
        raise ModelNotFoundError("model not found")
    with pytest.raises(AgentEngineError):
        raise ModelNotFoundError("model not found")


def test_all_providers_unavailable():
    with pytest.raises(AllProvidersUnavailableError):
        raise AllProvidersUnavailableError("no providers")


def test_rate_limit_exceeded():
    with pytest.raises(RateLimitExceededError):
        raise RateLimitExceededError("rate limited")


def test_no_fallback_model():
    with pytest.raises(NoFallbackModelError):
        raise NoFallbackModelError("no fallback")


def test_unsupported_file_type():
    with pytest.raises(UnsupportedFileTypeError):
        raise UnsupportedFileTypeError("unsupported")


def test_tool_not_found():
    with pytest.raises(ToolNotFoundError):
        raise ToolNotFoundError("tool not found")


def test_knowledge_base_not_found():
    with pytest.raises(KnowledgeBaseNotFoundError):
        raise KnowledgeBaseNotFoundError("kb not found")


def test_document_not_found():
    with pytest.raises(DocumentNotFoundError):
        raise DocumentNotFoundError("doc not found")


def test_permission_denied():
    with pytest.raises(PermissionDeniedError):
        raise PermissionDeniedError("access denied")


def test_tenant_not_found():
    with pytest.raises(TenantNotFoundError):
        raise TenantNotFoundError("tenant not found")


def test_all_inherit_from_base():
    exceptions = [
        ModelNotFoundError, AllProvidersUnavailableError,
        RateLimitExceededError, NoFallbackModelError,
        UnsupportedFileTypeError, ToolNotFoundError,
        KnowledgeBaseNotFoundError, DocumentNotFoundError,
        PermissionDeniedError, TenantNotFoundError,
    ]
    for exc in exceptions:
        assert issubclass(exc, AgentEngineError)
        assert issubclass(exc, Exception)

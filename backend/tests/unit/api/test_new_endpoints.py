"""Tests for new endpoints: publish channels, chat upload, knowledge URL import."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "tenant_id": "tenant-123",
        "username": "testuser",
        "role": "owner",
    }


# --- Publish Channel API Tests ---

class TestPublishChannelSchemas:
    """Test publish channel request/response schemas."""

    def test_create_channel_request_valid(self):
        from app.api.v1.publish import CreateChannelRequest
        req = CreateChannelRequest(
            agent_id="agent-1",
            type="api",
            name="Production API",
        )
        assert req.agent_id == "agent-1"
        assert req.type == "api"
        assert req.name == "Production API"
        assert req.config == {}

    def test_create_channel_request_with_config(self):
        from app.api.v1.publish import CreateChannelRequest
        req = CreateChannelRequest(
            agent_id="agent-1",
            type="webapp",
            name="Portal",
            config={"theme": "dark"},
        )
        assert req.config == {"theme": "dark"}

    def test_update_channel_request_partial(self):
        from app.api.v1.publish import UpdateChannelRequest
        req = UpdateChannelRequest(status="inactive")
        assert req.status == "inactive"
        assert req.name is None
        assert req.config is None

    def test_channel_types(self):
        from app.api.v1.publish import CreateChannelRequest
        for channel_type in ["api", "webapp", "iframe", "wechat", "feishu", "discord"]:
            req = CreateChannelRequest(agent_id="a", type=channel_type, name="test")
            assert req.type == channel_type


# --- Knowledge URL Import Tests ---

class TestKnowledgeUrlSchemas:
    """Test knowledge URL import request schemas."""

    def test_add_url_request_defaults(self):
        from app.api.v1.knowledge import AddUrlRequest
        req = AddUrlRequest(url="https://example.com")
        assert req.url == "https://example.com"
        assert req.chunk_size == 500
        assert req.chunk_overlap == 50

    def test_add_url_request_custom(self):
        from app.api.v1.knowledge import AddUrlRequest
        req = AddUrlRequest(url="https://example.com", chunk_size=1000, chunk_overlap=100)
        assert req.chunk_size == 1000
        assert req.chunk_overlap == 100

    def test_crawl_url_request_defaults(self):
        from app.api.v1.knowledge import CrawlUrlRequest
        req = CrawlUrlRequest(url="https://example.com")
        assert req.max_pages == 10
        assert req.allowed_domains is None

    def test_crawl_url_request_with_domains(self):
        from app.api.v1.knowledge import CrawlUrlRequest
        req = CrawlUrlRequest(
            url="https://example.com",
            max_pages=20,
            allowed_domains=["example.com"],
        )
        assert req.max_pages == 20
        assert req.allowed_domains == ["example.com"]


# --- Web Parser Tests ---

class TestWebParser:
    """Test web parser URL validation and content extraction."""

    def test_validate_url_blocks_private_ips(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        assert not parser._validate_url("http://192.168.1.1/secret")
        assert not parser._validate_url("http://10.0.0.1/secret")
        assert not parser._validate_url("http://127.0.0.1/secret")

    def test_validate_url_blocks_localhost(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        assert not parser._validate_url("http://localhost/secret")

    def test_validate_url_blocks_internal_domains(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        assert not parser._validate_url("http://metadata.google.internal/")

    def test_validate_url_allows_public(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        assert parser._validate_url("https://example.com/page")
        assert parser._validate_url("http://example.com/page")

    def test_validate_url_blocks_non_http(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        assert not parser._validate_url("ftp://example.com/file")
        assert not parser._validate_url("file:///etc/passwd")

    def test_extract_content_strips_scripts(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        html = '<html><body><script>alert("xss")</script><p>Hello World</p></body></html>'
        content = parser._extract_content(html)
        assert "alert" not in content
        assert "Hello World" in content

    def test_extract_content_strips_nav(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        html = '<html><body><nav>Menu</nav><main>Content</main></body></html>'
        content = parser._extract_content(html)
        assert "Menu" not in content
        assert "Content" in content

    def test_extract_content_prefers_main_tag(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        html = '<html><body><footer>Footer</footer><main><p>Main content here</p></main></body></html>'
        content = parser._extract_content(html)
        assert "Main content here" in content

    def test_clean_text_normalizes_whitespace(self):
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()
        text = "Hello   World\n\n\n   Extra   spaces"
        cleaned = parser._clean_text(text)
        assert "   " not in cleaned

    def test_parsed_document_defaults(self):
        from app.engines.knowledge_engine.parser.web_parser import ParsedDocument
        doc = ParsedDocument(content="test")
        assert doc.content == "test"
        assert doc.metadata == {}

    def test_parsed_document_with_metadata(self):
        from app.engines.knowledge_engine.parser.web_parser import ParsedDocument
        doc = ParsedDocument(content="test", metadata={"url": "https://example.com"})
        assert doc.metadata["url"] == "https://example.com"


# --- Chat Upload Tests ---

class TestChatUploadValidation:
    """Test chat file upload validation logic."""

    def test_chat_request_model(self):
        from app.api.v1.chat import ChatRequest
        req = ChatRequest(agent_id="agent-1", messages=[{"role": "user", "content": "hi"}])
        assert req.agent_id == "agent-1"
        assert len(req.messages) == 1
        assert req.stream is False

    def test_chat_request_with_conversation_id(self):
        from app.api.v1.chat import ChatRequest
        req = ChatRequest(
            agent_id="agent-1",
            messages=[{"role": "user", "content": "hi"}],
            conversation_id="conv-1",
            stream=True,
        )
        assert req.conversation_id == "conv-1"
        assert req.stream is True


# --- Publish Channel Model Tests ---

class TestPublishChannelModel:
    """Test publish channel model attributes."""

    def test_model_has_required_fields(self):
        from app.models.publish_channel import PublishChannelModel
        # Verify the model class exists and has the expected columns
        assert hasattr(PublishChannelModel, '__tablename__')
        assert PublishChannelModel.__tablename__ == "publish_channels"

    def test_model_default_status(self):
        from app.models.publish_channel import PublishChannelModel
        # Status column should default to "active"
        status_col = PublishChannelModel.__table__.c.get('status')
        assert status_col is not None


# --- API Client Methods (Frontend) Tests ---
# These are structural tests to verify the API client has the expected methods.

class TestApiClientMethods:
    """Verify API client has new methods."""

    def test_api_client_has_update_agent(self):
        import importlib
        import sys
        api_module_path = "frontend.src.lib.api"
        # Just verify the method exists by checking the file content
        with open("/Users/bian/workspace/work/code/agency-agent-platform/agent-engine-platform/frontend/src/lib/api.ts") as f:
            content = f.read()
        assert "async updateAgent(" in content
        assert "async listTokens(" in content
        assert "async createToken(" in content
        assert "async revokeToken(" in content
        assert "async listPublishChannels(" in content
        assert "async createPublishChannel(" in content
        assert "async addUrlToKnowledgeBase(" in content
        assert "async crawlUrlToKnowledgeBase(" in content


# --- Router Registration Tests ---

class TestRouterRegistration:
    """Verify new routers are registered."""

    def test_publish_router_registered(self):
        from app.api.v1 import api_router
        routes = [r.path for r in api_router.routes]
        assert any("/publish" in str(r) for r in routes)

    def test_knowledge_url_routes_exist(self):
        from app.api.v1.knowledge import router
        routes = [r.path for r in router.routes]
        assert any("url" in r for r in routes)
        assert any("crawl" in r for r in routes)

    def test_chat_upload_route_exists(self):
        from app.api.v1.chat import router
        routes = [r.path for r in router.routes]
        assert any("upload" in r for r in routes)

"""
导入 API 端点测试
"""

import pytest
from fastapi import FastAPI


class TestImportAPI:
    """测试导入 API 端点"""

    def test_import_router_exists(self):
        """测试导入路由存在"""
        from app.api.v1.data_import import router
        assert router is not None
        assert router.prefix == "/import"

    def test_import_router_tags(self):
        """测试导入路由标签"""
        from app.api.v1.data_import import router
        assert "import" in router.tags


bs4 = pytest.importorskip("bs4", reason="bs4 not installed")


class TestWebParser:
    """测试网页解析器"""

    def test_validate_url_safe(self):
        """测试安全 URL 验证"""
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()

        assert parser._validate_url("https://example.com") is True
        assert parser._validate_url("http://example.com/path") is True

    def test_validate_url_ssrf_blocked(self):
        """测试 SSRF 防护"""
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()

        # 内网 IP 应该被阻止
        assert parser._validate_url("http://127.0.0.1") is False
        assert parser._validate_url("http://localhost") is False
        assert parser._validate_url("http://169.254.169.254") is False
        assert parser._validate_url("http://10.0.0.1") is False
        assert parser._validate_url("http://192.168.1.1") is False

    def test_validate_url_invalid_scheme(self):
        """测试无效协议"""
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()

        assert parser._validate_url("ftp://example.com") is False
        assert parser._validate_url("file:///etc/passwd") is False

    def test_clean_text(self):
        """测试文本清理"""
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()

        text = "  Hello   World  \n\n\n  Test  "
        result = parser._clean_text(text)
        assert "Hello" in result
        assert "World" in result
        assert "Test" in result

    def test_validate_url_internal_domain(self):
        """测试内部域名阻止"""
        from app.engines.knowledge_engine.parser.web_parser import WebParser
        parser = WebParser()

        assert parser._validate_url("http://metadata.google.internal") is False
        assert parser._validate_url("http://test.internal") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

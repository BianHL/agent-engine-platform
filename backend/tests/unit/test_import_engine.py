"""
导入引擎单元测试
测试 Dify/Coze 数据导入功能
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.engines.import_engine.base_importer import (
    BaseImporter, ImportAssetType, ImportTask, ImportResult
)
from app.engines.import_engine.dify_importer import DifyImporter
from app.engines.import_engine.coze_importer import CozeImporter
from app.engines.import_engine.importer import ImportEngine


class TestImportAssetType:
    """测试导入资产类型枚举"""

    def test_asset_types(self):
        assert ImportAssetType.AGENT.value == "agent"
        assert ImportAssetType.KNOWLEDGE.value == "knowledge"
        assert ImportAssetType.TOOL.value == "tool"
        assert ImportAssetType.WORKFLOW.value == "workflow"
        assert ImportAssetType.DATASET.value == "dataset"


class TestImportTask:
    """测试导入任务数据类"""

    def test_create_task(self):
        task = ImportTask(
            id="test-123",
            source_platform="dify",
            asset_type=ImportAssetType.AGENT,
            status="pending",
            progress=0.0,
            total_items=10,
            processed_items=0,
            failed_items=0,
            errors=[]
        )
        assert task.id == "test-123"
        assert task.source_platform == "dify"
        assert task.status == "pending"
        assert task.total_items == 10


class TestImportResult:
    """测试导入结果数据类"""

    def test_success_result(self):
        result = ImportResult(
            success=True,
            asset_type=ImportAssetType.AGENT,
            source_id="src-123",
            target_id="tgt-456",
            name="Test Agent",
            errors=[],
            warnings=[],
            metadata={"source": "dify"}
        )
        assert result.success is True
        assert result.target_id == "tgt-456"

    def test_failure_result(self):
        result = ImportResult(
            success=False,
            asset_type=ImportAssetType.KNOWLEDGE,
            source_id="src-789",
            target_id=None,
            name="Failed KB",
            errors=["Connection timeout"],
            warnings=[],
            metadata={}
        )
        assert result.success is False
        assert len(result.errors) == 1


class TestDifyImporter:
    """测试 Dify 导入器"""

    @pytest.fixture
    def importer(self):
        return DifyImporter()

    @pytest.mark.asyncio
    async def test_validate_config_valid(self, importer):
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}
        result = await importer.validate_config(config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_key(self, importer):
        config = {"api_url": "https://api.dify.ai"}
        result = await importer.validate_config(config)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_config_missing_url(self, importer):
        config = {"api_key": "app-xxx"}
        result = await importer.validate_config(config)
        assert result is False

    def test_supported_asset_types(self, importer):
        assert ImportAssetType.AGENT in importer.supported_asset_types
        assert ImportAssetType.KNOWLEDGE in importer.supported_asset_types
        assert ImportAssetType.TOOL in importer.supported_asset_types
        assert ImportAssetType.WORKFLOW in importer.supported_asset_types

    @pytest.mark.asyncio
    async def test_import_agent_success(self, importer):
        agent_data = {
            "id": "agent-123",
            "name": "Test Agent",
            "description": "A test agent",
            "model": {"provider": "openai", "name": "gpt-4", "temperature": 0.7},
            "prompt_template": "You are a helpful assistant",
            "tools": [{"name": "search", "type": "builtin"}],
            "datasets": [{"id": "kb-1"}]
        }
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await importer.import_agent(agent_data, config)

        assert result.success is True
        assert result.asset_type == ImportAssetType.AGENT
        assert result.source_id == "agent-123"
        assert result.target_id is not None
        assert result.name == "Test Agent"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_agent_with_tools(self, importer):
        agent_data = {
            "id": "agent-456",
            "name": "Agent with Tools",
            "model": {"provider": "openai", "name": "gpt-4"},
            "tools": [
                {"name": "calculator", "type": "builtin"},
                {"name": "web_search", "type": "custom"}
            ]
        }
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await importer.import_agent(agent_data, config)

        assert result.success is True
        assert "converted_data" in result.metadata
        assert len(result.metadata["converted_data"]["tools"]) == 2

    @pytest.mark.asyncio
    async def test_import_knowledge_success(self, importer):
        kb_data = {
            "id": "kb-123",
            "name": "Test Knowledge Base",
            "description": "A test KB",
            "embedding_model": "text-embedding-ada-002",
            "chunk_size": 500,
            "document_count": 10
        }
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await importer.import_knowledge(kb_data, config)

        assert result.success is True
        assert result.asset_type == ImportAssetType.KNOWLEDGE
        assert result.name == "Test Knowledge Base"

    @pytest.mark.asyncio
    async def test_import_tool_success(self, importer):
        tool_data = {
            "id": "tool-123",
            "name": "Custom Tool",
            "description": "A custom tool",
            "type": "api",
            "parameters": {"url": {"type": "string"}},
            "endpoint": "https://api.example.com"
        }
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await importer.import_tool(tool_data, config)

        assert result.success is True
        assert result.asset_type == ImportAssetType.TOOL

    @pytest.mark.asyncio
    async def test_import_workflow_success(self, importer):
        wf_data = {
            "id": "wf-123",
            "name": "Test Workflow",
            "description": "A test workflow",
            "nodes": [
                {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}},
                {"id": "n2", "type": "llm", "data": {"model": "gpt-4"}, "position": {"x": 100, "y": 100}}
            ],
            "edges": [
                {"source": "n1", "target": "n2"}
            ]
        }
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await importer.import_workflow(wf_data, config)

        assert result.success is True
        assert result.asset_type == ImportAssetType.WORKFLOW
        assert "dag_config" in result.metadata["converted_data"]

    def test_convert_agent_format(self, importer):
        dify_agent = {
            "id": "agent-123",
            "name": "Test Agent",
            "description": "Description",
            "model": {"provider": "openai", "name": "gpt-4", "temperature": 0.8},
            "prompt_template": "You are helpful",
            "tools": [],
            "datasets": []
        }
        result = importer._convert_agent_format(dify_agent)

        assert result["name"] == "Test Agent"
        assert result["model_provider"] == "openai"
        assert result["model_name"] == "gpt-4"
        assert result["config"]["temperature"] == 0.8

    def test_map_node_type(self, importer):
        assert importer._map_node_type("llm") == "llm"
        assert importer._map_node_type("if_else") == "condition"
        assert importer._map_node_type("code") == "code"
        assert importer._map_node_type("unknown") == "llm"  # default


class TestCozeImporter:
    """测试 Coze 导入器"""

    @pytest.fixture
    def importer(self):
        return CozeImporter()

    @pytest.mark.asyncio
    async def test_validate_config_valid(self, importer):
        config = {"api_token": "pat-xxx"}
        result = await importer.validate_config(config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_token(self, importer):
        config = {}
        result = await importer.validate_config(config)
        assert result is False

    def test_supported_asset_types(self, importer):
        assert ImportAssetType.AGENT in importer.supported_asset_types
        assert ImportAssetType.KNOWLEDGE in importer.supported_asset_types

    @pytest.mark.asyncio
    async def test_import_bot_success(self, importer):
        bot_data = {
            "bot_id": "bot-123",
            "name": "Test Bot",
            "description": "A test bot",
            "model": "gpt-4",
            "prompt": "You are helpful",
            "plugins": [{"name": "search", "parameters": {}}],
            "knowledge_bases": [{"id": "kb-1"}]
        }
        config = {"api_token": "pat-xxx"}

        result = await importer.import_agent(bot_data, config)

        assert result.success is True
        assert result.source_id == "bot-123"
        assert result.name == "Test Bot"

    def test_convert_bot_format(self, importer):
        coze_bot = {
            "bot_id": "bot-123",
            "name": "Test Bot",
            "description": "Description",
            "model": "gpt-4",
            "prompt": "You are helpful",
            "temperature": 0.9,
            "plugins": [{"name": "search", "parameters": {}}],
            "knowledge_bases": [{"id": "kb-1"}]
        }
        result = importer._convert_bot_format(coze_bot)

        assert result["name"] == "Test Bot"
        assert result["model_provider"] == "openai"
        assert result["config"]["temperature"] == 0.9

    def test_map_node_type(self, importer):
        assert importer._map_node_type("llm") == "llm"
        assert importer._map_node_type("if") == "condition"
        assert importer._map_node_type("plugin") == "tool"
        assert importer._map_node_type("unknown") == "llm"


class TestImportEngine:
    """测试导入引擎"""

    @pytest.fixture
    def engine(self):
        return ImportEngine()

    def test_supported_platforms(self, engine):
        platforms = engine.supported_platforms
        assert "dify" in platforms
        assert "coze" in platforms

    def test_get_importer(self, engine):
        dify = engine.get_importer("dify")
        assert dify is not None
        assert isinstance(dify, DifyImporter)

        coze = engine.get_importer("coze")
        assert coze is not None
        assert isinstance(coze, CozeImporter)

        unknown = engine.get_importer("unknown")
        assert unknown is None

    @pytest.mark.asyncio
    async def test_validate_config(self, engine):
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}
        result = await engine.validate_config("dify", config)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_unknown_platform(self, engine):
        with pytest.raises(ValueError, match="Unsupported platform"):
            await engine.validate_config("unknown", {})

    @pytest.mark.asyncio
    async def test_create_import_task(self, engine):
        task = await engine.create_import_task(
            "dify",
            ImportAssetType.AGENT,
            ["id1", "id2", "id3"],
            {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}
        )
        assert task.status == "pending"
        assert task.total_items == 3
        assert task.id is not None

    @pytest.mark.asyncio
    async def test_execute_import(self, engine):
        assets = [
            {"id": "1", "name": "Agent 1"},
            {"id": "2", "name": "Agent 2"}
        ]
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        task = await engine.create_import_task("dify", ImportAssetType.AGENT, ["1", "2"], config)
        result = await engine.execute_import(task.id, assets, config)

        assert result.status in ["completed", "failed"]
        assert result.processed_items + result.failed_items == 2

    @pytest.mark.asyncio
    async def test_import_single(self, engine):
        asset_data = {"id": "agent-1", "name": "Test Agent"}
        config = {"api_url": "https://api.dify.ai", "api_key": "app-xxx"}

        result = await engine.import_single("dify", ImportAssetType.AGENT, asset_data, config)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_import_single_unknown_platform(self, engine):
        result = await engine.import_single("unknown", ImportAssetType.AGENT, {}, {})
        assert result.success is False
        assert "Unsupported platform" in result.errors[0]

    def test_get_nonexistent_task(self, engine):
        task = engine.get_task("nonexistent")
        assert task is None

    def test_list_tasks(self, engine):
        tasks = engine.list_tasks()
        assert isinstance(tasks, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Coze 数据导入器
支持从 Coze 平台导入 Bot、知识库、插件等数据
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_importer import BaseImporter, ImportAssetType, ImportResult


class CozeImporter(BaseImporter):
    """Coze 数据导入器"""

    def __init__(self):
        super().__init__("coze")
        self.supported_asset_types = [
            ImportAssetType.AGENT,
            ImportAssetType.KNOWLEDGE,
            ImportAssetType.TOOL,
            ImportAssetType.WORKFLOW
        ]

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证 Coze 导入配置"""
        return "api_token" in config

    async def list_assets(
        self,
        asset_type: ImportAssetType,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """列出 Coze 可导入的资产"""
        if asset_type == ImportAssetType.AGENT:
            return await self._list_bots(config)
        elif asset_type == ImportAssetType.KNOWLEDGE:
            return await self._list_knowledge_bases(config)
        elif asset_type == ImportAssetType.TOOL:
            return await self._list_plugins(config)
        elif asset_type == ImportAssetType.WORKFLOW:
            return await self._list_workflows(config)
        return []

    async def import_agent(self, agent_data: Dict[str, Any], config: Dict[str, Any]) -> ImportResult:
        """导入 Coze Bot"""
        try:
            converted = self._convert_bot_format(agent_data)
            return ImportResult(
                success=True, asset_type=ImportAssetType.AGENT,
                source_id=agent_data.get("bot_id", ""), target_id=str(uuid.uuid4()),
                name=converted.get("name", ""), errors=[], warnings=[],
                metadata={"source_platform": "coze", "original_data": agent_data, "converted_data": converted}
            )
        except Exception as e:
            return ImportResult(
                success=False, asset_type=ImportAssetType.AGENT,
                source_id=agent_data.get("bot_id", ""), target_id=None,
                name=agent_data.get("name", ""), errors=[str(e)], warnings=[],
                metadata={"source_platform": "coze"}
            )

    async def import_knowledge(self, knowledge_data: Dict[str, Any], config: Dict[str, Any]) -> ImportResult:
        """导入 Coze 知识库"""
        try:
            converted = self._convert_knowledge_format(knowledge_data)
            return ImportResult(
                success=True, asset_type=ImportAssetType.KNOWLEDGE,
                source_id=knowledge_data.get("dataset_id", ""), target_id=str(uuid.uuid4()),
                name=converted.get("name", ""), errors=[], warnings=[],
                metadata={"source_platform": "coze", "original_data": knowledge_data, "converted_data": converted}
            )
        except Exception as e:
            return ImportResult(
                success=False, asset_type=ImportAssetType.KNOWLEDGE,
                source_id=knowledge_data.get("dataset_id", ""), target_id=None,
                name=knowledge_data.get("name", ""), errors=[str(e)], warnings=[],
                metadata={"source_platform": "coze"}
            )

    async def import_tool(self, tool_data: Dict[str, Any], config: Dict[str, Any]) -> ImportResult:
        """导入 Coze 插件"""
        try:
            converted = self._convert_plugin_format(tool_data)
            return ImportResult(
                success=True, asset_type=ImportAssetType.TOOL,
                source_id=tool_data.get("plugin_id", ""), target_id=str(uuid.uuid4()),
                name=converted.get("name", ""), errors=[], warnings=[],
                metadata={"source_platform": "coze", "original_data": tool_data, "converted_data": converted}
            )
        except Exception as e:
            return ImportResult(
                success=False, asset_type=ImportAssetType.TOOL,
                source_id=tool_data.get("plugin_id", ""), target_id=None,
                name=tool_data.get("name", ""), errors=[str(e)], warnings=[],
                metadata={"source_platform": "coze"}
            )

    async def import_workflow(self, workflow_data: Dict[str, Any], config: Dict[str, Any]) -> ImportResult:
        """导入 Coze 工作流"""
        try:
            converted = self._convert_workflow_format(workflow_data)
            return ImportResult(
                success=True, asset_type=ImportAssetType.WORKFLOW,
                source_id=workflow_data.get("workflow_id", ""), target_id=str(uuid.uuid4()),
                name=converted.get("name", ""), errors=[], warnings=[],
                metadata={"source_platform": "coze", "original_data": workflow_data, "converted_data": converted}
            )
        except Exception as e:
            return ImportResult(
                success=False, asset_type=ImportAssetType.WORKFLOW,
                source_id=workflow_data.get("workflow_id", ""), target_id=None,
                name=workflow_data.get("name", ""), errors=[str(e)], warnings=[],
                metadata={"source_platform": "coze"}
            )

    def _convert_bot_format(self, coze_bot: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Coze Bot 格式"""
        return {
            "name": coze_bot.get("name", ""),
            "description": coze_bot.get("description", ""),
            "model_provider": "openai",
            "model_name": coze_bot.get("model", "gpt-4"),
            "system_prompt": coze_bot.get("prompt", ""),
            "tools": self._extract_plugins(coze_bot),
            "knowledge_base_ids": self._extract_knowledge_bases(coze_bot),
            "config": {
                "temperature": coze_bot.get("temperature", 0.7),
                "max_tokens": coze_bot.get("max_tokens", 4096),
                "variables": coze_bot.get("variables", {})
            },
            "metadata": {"source": "coze", "original_id": coze_bot.get("bot_id"), "imported_at": datetime.utcnow().isoformat()}
        }

    def _convert_knowledge_format(self, coze_kb: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Coze 知识库格式"""
        return {
            "name": coze_kb.get("name", ""),
            "description": coze_kb.get("description", ""),
            "embedding_model": "text-embedding-ada-002",
            "chunk_size": 500, "chunk_overlap": 50, "retrieval_mode": "hybrid",
            "metadata": {"source": "coze", "original_id": coze_kb.get("dataset_id"),
                         "document_count": coze_kb.get("doc_count", 0), "imported_at": datetime.utcnow().isoformat()}
        }

    def _convert_plugin_format(self, coze_plugin: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Coze 插件格式"""
        return {
            "name": coze_plugin.get("name", ""),
            "description": coze_plugin.get("description", ""),
            "tool_type": "api",
            "input_schema": coze_plugin.get("api_schema", {}),
            "handler": coze_plugin.get("api_url", ""),
            "config": {"auth_type": coze_plugin.get("auth_type", "none"), "headers": coze_plugin.get("headers", {})},
            "metadata": {"source": "coze", "original_id": coze_plugin.get("plugin_id"), "imported_at": datetime.utcnow().isoformat()}
        }

    def _convert_workflow_format(self, coze_wf: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Coze 工作流格式"""
        nodes = [{"node_id": n.get("node_id", str(uuid.uuid4())), "node_type": self._map_node_type(n.get("type", "")),
                  "config": n.get("config", {}), "position_x": n.get("position", {}).get("x", 0),
                  "position_y": n.get("position", {}).get("y", 0)} for n in coze_wf.get("nodes", [])]
        edges = [{"source_node_id": e.get("from_node", ""), "target_node_id": e.get("to_node", ""),
                  "condition_expression": e.get("condition", "")} for e in coze_wf.get("edges", [])]
        return {
            "name": coze_wf.get("name", ""), "description": coze_wf.get("description", ""),
            "dag_config": {"nodes": nodes, "edges": edges},
            "metadata": {"source": "coze", "original_id": coze_wf.get("workflow_id"), "imported_at": datetime.utcnow().isoformat()}
        }

    def _map_node_type(self, coze_type: str) -> str:
        """映射 Coze 节点类型"""
        return {"llm": "llm", "if": "condition", "code": "code", "http": "http",
                "start": "start", "end": "end", "database": "database",
                "knowledge": "knowledge", "plugin": "tool", "variable": "variable"}.get(coze_type, "llm")

    def _extract_plugins(self, bot_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"name": p.get("name", ""), "type": "api", "config": p.get("parameters", {})} for p in bot_data.get("plugins", [])]

    def _extract_knowledge_bases(self, bot_data: Dict[str, Any]) -> List[str]:
        return [kb.get("id") for kb in bot_data.get("knowledge_bases", []) if kb.get("id")]

    async def _list_bots(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """GET https://api.coze.cn/v1/bots"""
        return []

    async def _list_knowledge_bases(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """GET https://api.coze.cn/v1/knowledge/list"""
        return []

    async def _list_plugins(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """GET https://api.coze.cn/v1/plugins"""
        return []

    async def _list_workflows(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """GET https://api.coze.cn/v1/workflows"""
        return []

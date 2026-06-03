"""
Dify 数据导入器
支持从 Dify 平台导入 Agent、知识库、工具等数据
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import UTC, datetime

from .base_importer import BaseImporter, ImportAssetType, ImportResult


class DifyImporter(BaseImporter):
    """Dify 数据导入器"""

    def __init__(self):
        super().__init__("dify")
        self.supported_asset_types = [
            ImportAssetType.AGENT,
            ImportAssetType.KNOWLEDGE,
            ImportAssetType.TOOL,
            ImportAssetType.WORKFLOW
        ]

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证 Dify 导入配置"""
        required_fields = ["api_url", "api_key"]
        return all(field in config for field in required_fields)

    async def list_assets(
        self,
        asset_type: ImportAssetType,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """列出 Dify 可导入的资产"""
        if asset_type == ImportAssetType.AGENT:
            return await self._list_agents(config)
        elif asset_type == ImportAssetType.KNOWLEDGE:
            return await self._list_knowledge_bases(config)
        elif asset_type == ImportAssetType.TOOL:
            return await self._list_tools(config)
        elif asset_type == ImportAssetType.WORKFLOW:
            return await self._list_workflows(config)
        return []

    async def import_agent(
        self,
        agent_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入 Dify Agent"""
        try:
            converted = self._convert_agent_format(agent_data)
            return ImportResult(
                success=True,
                asset_type=ImportAssetType.AGENT,
                source_id=agent_data.get("id", ""),
                target_id=str(uuid.uuid4()),
                name=converted.get("name", ""),
                errors=[],
                warnings=[],
                metadata={
                    "source_platform": "dify",
                    "original_data": agent_data,
                    "converted_data": converted
                }
            )
        except Exception as e:
            return ImportResult(
                success=False,
                asset_type=ImportAssetType.AGENT,
                source_id=agent_data.get("id", ""),
                target_id=None,
                name=agent_data.get("name", ""),
                errors=[str(e)],
                warnings=[],
                metadata={"source_platform": "dify"}
            )

    async def import_knowledge(
        self,
        knowledge_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入 Dify 知识库"""
        try:
            converted = self._convert_knowledge_format(knowledge_data)
            return ImportResult(
                success=True,
                asset_type=ImportAssetType.KNOWLEDGE,
                source_id=knowledge_data.get("id", ""),
                target_id=str(uuid.uuid4()),
                name=converted.get("name", ""),
                errors=[],
                warnings=[],
                metadata={
                    "source_platform": "dify",
                    "original_data": knowledge_data,
                    "converted_data": converted
                }
            )
        except Exception as e:
            return ImportResult(
                success=False,
                asset_type=ImportAssetType.KNOWLEDGE,
                source_id=knowledge_data.get("id", ""),
                target_id=None,
                name=knowledge_data.get("name", ""),
                errors=[str(e)],
                warnings=[],
                metadata={"source_platform": "dify"}
            )

    async def import_tool(
        self,
        tool_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入 Dify 工具"""
        try:
            converted = self._convert_tool_format(tool_data)
            return ImportResult(
                success=True,
                asset_type=ImportAssetType.TOOL,
                source_id=tool_data.get("id", ""),
                target_id=str(uuid.uuid4()),
                name=converted.get("name", ""),
                errors=[],
                warnings=[],
                metadata={
                    "source_platform": "dify",
                    "original_data": tool_data,
                    "converted_data": converted
                }
            )
        except Exception as e:
            return ImportResult(
                success=False,
                asset_type=ImportAssetType.TOOL,
                source_id=tool_data.get("id", ""),
                target_id=None,
                name=tool_data.get("name", ""),
                errors=[str(e)],
                warnings=[],
                metadata={"source_platform": "dify"}
            )

    async def import_workflow(
        self,
        workflow_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入 Dify 工作流"""
        try:
            converted = self._convert_workflow_format(workflow_data)
            return ImportResult(
                success=True,
                asset_type=ImportAssetType.WORKFLOW,
                source_id=workflow_data.get("id", ""),
                target_id=str(uuid.uuid4()),
                name=converted.get("name", ""),
                errors=[],
                warnings=[],
                metadata={
                    "source_platform": "dify",
                    "original_data": workflow_data,
                    "converted_data": converted
                }
            )
        except Exception as e:
            return ImportResult(
                success=False,
                asset_type=ImportAssetType.WORKFLOW,
                source_id=workflow_data.get("id", ""),
                target_id=None,
                name=workflow_data.get("name", ""),
                errors=[str(e)],
                warnings=[],
                metadata={"source_platform": "dify"}
            )

    def _convert_agent_format(self, dify_agent: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Dify Agent 格式"""
        return {
            "name": dify_agent.get("name", ""),
            "description": dify_agent.get("description", ""),
            "model_provider": dify_agent.get("model", {}).get("provider", "openai"),
            "model_name": dify_agent.get("model", {}).get("name", "gpt-4"),
            "system_prompt": dify_agent.get("prompt_template", ""),
            "tools": self._extract_tools(dify_agent),
            "knowledge_base_ids": self._extract_knowledge_bases(dify_agent),
            "config": {
                "temperature": dify_agent.get("model", {}).get("temperature", 0.7),
                "max_tokens": dify_agent.get("model", {}).get("max_tokens", 4096),
                "top_p": dify_agent.get("model", {}).get("top_p", 1.0)
            },
            "metadata": {
                "source": "dify",
                "original_id": dify_agent.get("id"),
                "imported_at": datetime.now(UTC).replace(tzinfo=None).isoformat()
            }
        }

    def _convert_knowledge_format(self, dify_kb: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Dify 知识库格式"""
        return {
            "name": dify_kb.get("name", ""),
            "description": dify_kb.get("description", ""),
            "embedding_model": dify_kb.get("embedding_model", "text-embedding-ada-002"),
            "chunk_size": dify_kb.get("chunk_size", 500),
            "chunk_overlap": dify_kb.get("chunk_overlap", 50),
            "retrieval_mode": "hybrid",
            "metadata": {
                "source": "dify",
                "original_id": dify_kb.get("id"),
                "document_count": dify_kb.get("document_count", 0),
                "imported_at": datetime.now(UTC).replace(tzinfo=None).isoformat()
            }
        }

    def _convert_tool_format(self, dify_tool: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Dify 工具格式"""
        return {
            "name": dify_tool.get("name", ""),
            "description": dify_tool.get("description", ""),
            "tool_type": dify_tool.get("type", "custom"),
            "input_schema": dify_tool.get("parameters", {}),
            "handler": dify_tool.get("endpoint", ""),
            "config": {
                "timeout": dify_tool.get("timeout", 30),
                "retry_count": dify_tool.get("retry_count", 3)
            },
            "metadata": {
                "source": "dify",
                "original_id": dify_tool.get("id"),
                "imported_at": datetime.now(UTC).replace(tzinfo=None).isoformat()
            }
        }

    def _convert_workflow_format(self, dify_wf: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Dify 工作流格式"""
        nodes = []
        edges = []
        for node in dify_wf.get("nodes", []):
            nodes.append({
                "node_id": node.get("id", str(uuid.uuid4())),
                "node_type": self._map_node_type(node.get("type", "")),
                "config": node.get("data", {}),
                "position_x": node.get("position", {}).get("x", 0),
                "position_y": node.get("position", {}).get("y", 0)
            })
        for edge in dify_wf.get("edges", []):
            edges.append({
                "source_node_id": edge.get("source", ""),
                "target_node_id": edge.get("target", ""),
                "condition_expression": edge.get("sourceHandle", "")
            })
        return {
            "name": dify_wf.get("name", ""),
            "description": dify_wf.get("description", ""),
            "dag_config": {"nodes": nodes, "edges": edges},
            "metadata": {
                "source": "dify",
                "original_id": dify_wf.get("id"),
                "imported_at": datetime.now(UTC).replace(tzinfo=None).isoformat()
            }
        }

    def _map_node_type(self, dify_type: str) -> str:
        """映射 Dify 节点类型到平台节点类型"""
        type_mapping = {
            "llm": "llm", "if_else": "condition", "code": "code",
            "http_request": "http", "start": "start", "end": "end",
            "variable_aggregator": "aggregator", "knowledge_retrieval": "knowledge",
            "question_classifier": "classifier"
        }
        return type_mapping.get(dify_type, "llm")

    def _extract_tools(self, agent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取 Agent 使用的工具"""
        return [{"name": t.get("name", ""), "type": t.get("type", "custom"), "config": t.get("configuration", {})} for t in agent_data.get("tools", [])]

    def _extract_knowledge_bases(self, agent_data: Dict[str, Any]) -> List[str]:
        """提取 Agent 关联的知识库 ID"""
        return [kb.get("id") for kb in agent_data.get("datasets", []) if kb.get("id")]

    async def _list_agents(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """列出 Dify Agent - GET {api_url}/v1/apps"""
        return []

    async def _list_knowledge_bases(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """列出 Dify 知识库 - GET {api_url}/v1/datasets"""
        return []

    async def _list_tools(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """列出 Dify 工具 - GET {api_url}/v1/tools"""
        return []

    async def _list_workflows(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """列出 Dify 工作流 - GET {api_url}/v1/workflows"""
        return []

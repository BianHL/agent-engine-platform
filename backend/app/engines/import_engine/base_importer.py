"""
基础导入器抽象类
定义竞品数据导入的标准接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ImportAssetType(Enum):
    """导入资产类型"""
    AGENT = "agent"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    WORKFLOW = "workflow"
    DATASET = "dataset"


@dataclass
class ImportTask:
    """导入任务"""
    id: str
    source_platform: str
    asset_type: ImportAssetType
    status: str  # pending, processing, completed, failed
    progress: float  # 0-100
    total_items: int
    processed_items: int
    failed_items: int
    errors: List[str]
    result: Optional[Dict[str, Any]] = None


@dataclass
class ImportResult:
    """导入结果"""
    success: bool
    asset_type: ImportAssetType
    source_id: str
    target_id: Optional[str]
    name: str
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class BaseImporter(ABC):
    """基础导入器抽象类"""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.supported_asset_types: List[ImportAssetType] = []

    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证导入配置"""
        pass

    @abstractmethod
    async def list_assets(
        self,
        asset_type: ImportAssetType,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """列出可导入的资产"""
        pass

    @abstractmethod
    async def import_agent(
        self,
        agent_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入 Agent"""
        pass

    @abstractmethod
    async def import_knowledge(
        self,
        knowledge_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入知识库"""
        pass

    @abstractmethod
    async def import_tool(
        self,
        tool_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入工具"""
        pass

    @abstractmethod
    async def import_workflow(
        self,
        workflow_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入工作流"""
        pass

    async def import_batch(
        self,
        assets: List[Dict[str, Any]],
        asset_type: ImportAssetType,
        config: Dict[str, Any]
    ) -> List[ImportResult]:
        """批量导入资产"""
        results = []
        for asset in assets:
            try:
                if asset_type == ImportAssetType.AGENT:
                    result = await self.import_agent(asset, config)
                elif asset_type == ImportAssetType.KNOWLEDGE:
                    result = await self.import_knowledge(asset, config)
                elif asset_type == ImportAssetType.TOOL:
                    result = await self.import_tool(asset, config)
                elif asset_type == ImportAssetType.WORKFLOW:
                    result = await self.import_workflow(asset, config)
                else:
                    result = ImportResult(
                        success=False,
                        asset_type=asset_type,
                        source_id=asset.get("id", "unknown"),
                        target_id=None,
                        name=asset.get("name", "unknown"),
                        errors=[f"Unsupported asset type: {asset_type}"],
                        warnings=[],
                        metadata={}
                    )
                results.append(result)
            except Exception as e:
                results.append(ImportResult(
                    success=False,
                    asset_type=asset_type,
                    source_id=asset.get("id", "unknown"),
                    target_id=None,
                    name=asset.get("name", "unknown"),
                    errors=[str(e)],
                    warnings=[],
                    metadata={}
                ))
        return results

    def _convert_to_standard_format(
        self,
        data: Dict[str, Any],
        asset_type: ImportAssetType
    ) -> Dict[str, Any]:
        """将竞品数据转换为标准格式"""
        # 子类实现具体的转换逻辑
        return data

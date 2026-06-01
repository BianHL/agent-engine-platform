"""
导入引擎主入口
统一管理所有竞品数据导入器
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_importer import BaseImporter, ImportAssetType, ImportTask, ImportResult
from .dify_importer import DifyImporter
from .coze_importer import CozeImporter


class ImportEngine:
    """导入引擎 - 统一管理竞品数据导入"""

    def __init__(self):
        self._importers: Dict[str, BaseImporter] = {
            "dify": DifyImporter(),
            "coze": CozeImporter()
        }
        self._tasks: Dict[str, ImportTask] = {}

    @property
    def supported_platforms(self) -> List[str]:
        """支持的平台列表"""
        return list(self._importers.keys())

    def get_importer(self, platform: str) -> Optional[BaseImporter]:
        """获取指定平台的导入器"""
        return self._importers.get(platform)

    async def validate_config(self, platform: str, config: Dict[str, Any]) -> bool:
        """验证导入配置"""
        importer = self.get_importer(platform)
        if not importer:
            raise ValueError(f"Unsupported platform: {platform}")
        return await importer.validate_config(config)

    async def list_assets(
        self,
        platform: str,
        asset_type: ImportAssetType,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """列出可导入的资产"""
        importer = self.get_importer(platform)
        if not importer:
            raise ValueError(f"Unsupported platform: {platform}")
        return await importer.list_assets(asset_type, config)

    async def create_import_task(
        self,
        platform: str,
        asset_type: ImportAssetType,
        asset_ids: List[str],
        config: Dict[str, Any]
    ) -> ImportTask:
        """创建导入任务"""
        task_id = str(uuid.uuid4())
        task = ImportTask(
            id=task_id,
            source_platform=platform,
            asset_type=asset_type,
            status="pending",
            progress=0.0,
            total_items=len(asset_ids),
            processed_items=0,
            failed_items=0,
            errors=[],
            result=None
        )
        self._tasks[task_id] = task
        return task

    async def execute_import(
        self,
        task_id: str,
        assets: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> ImportTask:
        """执行导入任务"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        importer = self.get_importer(task.source_platform)
        if not importer:
            raise ValueError(f"Unsupported platform: {task.source_platform}")

        task.status = "processing"
        results = []

        for i, asset in enumerate(assets):
            try:
                if task.asset_type == ImportAssetType.AGENT:
                    result = await importer.import_agent(asset, config)
                elif task.asset_type == ImportAssetType.KNOWLEDGE:
                    result = await importer.import_knowledge(asset, config)
                elif task.asset_type == ImportAssetType.TOOL:
                    result = await importer.import_tool(asset, config)
                elif task.asset_type == ImportAssetType.WORKFLOW:
                    result = await importer.import_workflow(asset, config)
                else:
                    result = ImportResult(
                        success=False, asset_type=task.asset_type,
                        source_id=asset.get("id", ""), target_id=None,
                        name=asset.get("name", ""),
                        errors=[f"Unsupported type: {task.asset_type}"],
                        warnings=[], metadata={}
                    )

                results.append(result)
                if result.success:
                    task.processed_items += 1
                else:
                    task.failed_items += 1
                    task.errors.extend(result.errors)

            except Exception as e:
                task.failed_items += 1
                task.errors.append(str(e))

            task.progress = ((i + 1) / len(assets)) * 100

        task.status = "completed" if task.failed_items == 0 else "failed"
        task.result = {
            "total": len(assets),
            "success": task.processed_items,
            "failed": task.failed_items,
            "errors": task.errors,
            "results": [
                {
                    "success": r.success,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "name": r.name,
                    "errors": r.errors
                } for r in results
            ]
        }
        return task

    def get_task(self, task_id: str) -> Optional[ImportTask]:
        """获取导入任务状态"""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[ImportTask]:
        """列出所有导入任务"""
        return list(self._tasks.values())

    async def import_single(
        self,
        platform: str,
        asset_type: ImportAssetType,
        asset_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> ImportResult:
        """导入单个资产"""
        importer = self.get_importer(platform)
        if not importer:
            return ImportResult(
                success=False, asset_type=asset_type,
                source_id=asset_data.get("id", ""), target_id=None,
                name=asset_data.get("name", ""),
                errors=[f"Unsupported platform: {platform}"],
                warnings=[], metadata={}
            )

        if asset_type == ImportAssetType.AGENT:
            return await importer.import_agent(asset_data, config)
        elif asset_type == ImportAssetType.KNOWLEDGE:
            return await importer.import_knowledge(asset_data, config)
        elif asset_type == ImportAssetType.TOOL:
            return await importer.import_tool(asset_data, config)
        elif asset_type == ImportAssetType.WORKFLOW:
            return await importer.import_workflow(asset_data, config)
        else:
            return ImportResult(
                success=False, asset_type=asset_type,
                source_id=asset_data.get("id", ""), target_id=None,
                name=asset_data.get("name", ""),
                errors=[f"Unsupported type: {asset_type}"],
                warnings=[], metadata={}
            )


# 全局导入引擎实例
import_engine = ImportEngine()

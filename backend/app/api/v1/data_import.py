"""
竞品数据导入 API
支持从 Dify、Coze 等平台导入 Agent、知识库、工具等数据
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.engines.import_engine.importer import import_engine
from app.engines.import_engine.base_importer import ImportAssetType

router = APIRouter(prefix="/import", tags=["import"])


class ImportConfig(BaseModel):
    """导入配置"""
    platform: str = Field(..., description="平台名称: dify, coze")
    api_url: Optional[str] = Field(None, description="平台 API 地址")
    api_key: Optional[str] = Field(None, description="API Key")
    api_token: Optional[str] = Field(None, description="API Token")


class ListAssetsRequest(BaseModel):
    """列出资产请求"""
    platform: str
    asset_type: str  # agent, knowledge, tool, workflow
    config: ImportConfig


class ImportRequest(BaseModel):
    """导入请求"""
    platform: str
    asset_type: str
    assets: List[Dict[str, Any]]
    config: ImportConfig


class SingleImportRequest(BaseModel):
    """单个导入请求"""
    platform: str
    asset_type: str
    asset_data: Dict[str, Any]
    config: ImportConfig


@router.get("/platforms")
async def list_platforms():
    """列出支持的平台"""
    return {
        "platforms": [
            {
                "name": "dify",
                "display_name": "Dify",
                "description": "Dify AI 平台",
                "asset_types": ["agent", "knowledge", "tool", "workflow"],
                "config_fields": ["api_url", "api_key"]
            },
            {
                "name": "coze",
                "display_name": "Coze",
                "description": "Coze AI 平台",
                "asset_types": ["agent", "knowledge", "tool", "workflow"],
                "config_fields": ["api_token"]
            }
        ]
    }


@router.post("/validate")
async def validate_config(
    request: ImportConfig,
    current_user: Dict = Depends(require_permission("data_import", "create"))
):
    """验证导入配置"""
    try:
        config = {}
        if request.api_url:
            config["api_url"] = request.api_url
        if request.api_key:
            config["api_key"] = request.api_key
        if request.api_token:
            config["api_token"] = request.api_token

        is_valid = await import_engine.validate_config(request.platform, config)
        return {"valid": is_valid, "platform": request.platform}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assets")
async def list_assets(
    request: ListAssetsRequest,
    current_user: Dict = Depends(require_permission("data_import", "create"))
):
    """列出可导入的资产"""
    try:
        asset_type = ImportAssetType(request.asset_type)
        config = {}
        if request.config.api_url:
            config["api_url"] = request.config.api_url
        if request.config.api_key:
            config["api_key"] = request.config.api_key
        if request.config.api_token:
            config["api_token"] = request.config.api_token

        assets = await import_engine.list_assets(request.platform, asset_type, config)
        return {"assets": assets, "total": len(assets)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
async def execute_import(
    request: ImportRequest,
    current_user: Dict = Depends(require_permission("data_import", "create"))
):
    """执行批量导入"""
    try:
        asset_type = ImportAssetType(request.asset_type)
        config = {}
        if request.config.api_url:
            config["api_url"] = request.config.api_url
        if request.config.api_key:
            config["api_key"] = request.config.api_key
        if request.config.api_token:
            config["api_token"] = request.config.api_token

        asset_ids = [a.get("id", "") for a in request.assets]
        task = await import_engine.create_import_task(
            request.platform, asset_type, asset_ids, config
        )
        task = await import_engine.execute_import(task.id, request.assets, config)

        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "total": task.total_items,
            "processed": task.processed_items,
            "failed": task.failed_items,
            "errors": task.errors,
            "result": task.result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/single")
async def import_single(
    request: SingleImportRequest,
    current_user: Dict = Depends(require_permission("data_import", "create"))
):
    """导入单个资产"""
    try:
        asset_type = ImportAssetType(request.asset_type)
        config = {}
        if request.config.api_url:
            config["api_url"] = request.config.api_url
        if request.config.api_key:
            config["api_key"] = request.config.api_key
        if request.config.api_token:
            config["api_token"] = request.config.api_token

        result = await import_engine.import_single(
            request.platform, asset_type, request.asset_data, config
        )

        return {
            "success": result.success,
            "asset_type": result.asset_type.value,
            "source_id": result.source_id,
            "target_id": result.target_id,
            "name": result.name,
            "errors": result.errors,
            "warnings": result.warnings
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks")
async def list_tasks(current_user: Dict = Depends(get_current_user)):
    """列出所有导入任务"""
    tasks = import_engine.list_tasks()
    return {
        "tasks": [
            {
                "id": t.id,
                "platform": t.source_platform,
                "asset_type": t.asset_type.value,
                "status": t.status,
                "progress": t.progress,
                "total": t.total_items,
                "processed": t.processed_items,
                "failed": t.failed_items
            } for t in tasks
        ]
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, current_user: Dict = Depends(get_current_user)):
    """获取导入任务详情"""
    task = import_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "platform": task.source_platform,
        "asset_type": task.asset_type.value,
        "status": task.status,
        "progress": task.progress,
        "total": task.total_items,
        "processed": task.processed_items,
        "failed": task.failed_items,
        "errors": task.errors,
        "result": task.result
    }


@router.post("/upload")
async def upload_import_file(
    platform: str = Form(...),
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: Dict = Depends(require_permission("data_import", "create"))
):
    """上传文件导入"""
    try:
        import json

        # 文件大小限制 (10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")

        data = json.loads(content)

        asset_type_enum = ImportAssetType(asset_type)

        if isinstance(data, list):
            assets = data
        elif isinstance(data, dict):
            assets = [data]
        else:
            raise HTTPException(status_code=400, detail="Invalid file format")

        task = await import_engine.create_import_task(
            platform, asset_type_enum, [a.get("id", "") for a in assets], {}
        )
        task = await import_engine.execute_import(task.id, assets, {})

        return {
            "task_id": task.id,
            "status": task.status,
            "total": task.total_items,
            "processed": task.processed_items,
            "failed": task.failed_items,
            "errors": task.errors
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

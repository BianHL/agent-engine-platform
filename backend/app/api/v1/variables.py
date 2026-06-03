"""
变量和 KV 存储 API
支持会话级、用户级、全局级变量存储
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from datetime import UTC, datetime

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db

router = APIRouter(prefix="/variables", tags=["variables"])


class VariableCreate(BaseModel):
    """创建变量"""
    key: str = Field(..., min_length=1, max_length=255)
    value: Any = Field(...)
    scope: str = Field("global", pattern="^(session|user|global)$")
    description: Optional[str] = None


class VariableUpdate(BaseModel):
    """更新变量"""
    value: Any = Field(...)
    description: Optional[str] = None


class VariableResponse(BaseModel):
    """变量响应"""
    id: str
    key: str
    value: Any
    scope: str
    description: Optional[str]
    created_at: str
    updated_at: str


# 模拟变量存储（实际应使用数据库）
# TODO: 生产环境需要使用 Redis 或 MySQL 存储
_variables_store: Dict[str, Dict[str, Any]] = {}


@router.post("", response_model=VariableResponse)
async def create_variable(
    request: VariableCreate,
    current_user: Dict = Depends(require_permission("variable", "create"))
):
    """创建变量"""
    var_key = f"{request.scope}:{current_user['id']}:{request.key}"

    if var_key in _variables_store:
        raise HTTPException(status_code=400, detail="Variable already exists")

    now = datetime.now(UTC).replace(tzinfo=None).isoformat()
    _variables_store[var_key] = {
        "id": var_key,
        "key": request.key,
        "value": request.value,
        "scope": request.scope,
        "description": request.description,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }

    return VariableResponse(**_variables_store[var_key])


@router.get("", response_model=List[VariableResponse])
async def list_variables(
    scope: Optional[str] = Query(None, pattern="^(session|user|global)$"),
    key_prefix: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """列出变量"""
    results = []
    for var_key, var in _variables_store.items():
        # 用户只能看到自己创建的变量和全局变量
        if var["created_by"] != current_user["id"] and var["scope"] != "global":
            continue
        if scope and var["scope"] != scope:
            continue
        if key_prefix and not var["key"].startswith(key_prefix):
            continue
        results.append(VariableResponse(**var))
    return results


@router.get("/{key}")
async def get_variable(
    key: str,
    scope: str = Query("global", pattern="^(session|user|global)$"),
    current_user: Dict = Depends(get_current_user)
):
    """获取变量值"""
    var_key = f"{scope}:{current_user['id']}:{key}"

    if var_key not in _variables_store:
        # 尝试查找全局变量
        global_key = f"global:{current_user['id']}:{key}"
        if global_key not in _variables_store:
            raise HTTPException(status_code=404, detail="Variable not found")
        var_key = global_key

    var = _variables_store[var_key]
    return {"key": var["key"], "value": var["value"], "scope": var["scope"]}


@router.put("/{key}", response_model=VariableResponse)
async def update_variable(
    key: str,
    request: VariableUpdate,
    scope: str = Query("global", pattern="^(session|user|global)$"),
    current_user: Dict = Depends(require_permission("variable", "update"))
):
    """更新变量"""
    var_key = f"{scope}:{current_user['id']}:{key}"

    if var_key not in _variables_store:
        raise HTTPException(status_code=404, detail="Variable not found")

    var = _variables_store[var_key]
    var["value"] = request.value
    if request.description is not None:
        var["description"] = request.description
    var["updated_at"] = datetime.now(UTC).replace(tzinfo=None).isoformat()

    return VariableResponse(**var)


@router.delete("/{key}")
async def delete_variable(
    key: str,
    scope: str = Query("global", pattern="^(session|user|global)$"),
    current_user: Dict = Depends(require_permission("variable", "delete"))
):
    """删除变量"""
    var_key = f"{scope}:{current_user['id']}:{key}"

    if var_key not in _variables_store:
        raise HTTPException(status_code=404, detail="Variable not found")

    del _variables_store[var_key]
    return {"message": "Variable deleted"}


@router.post("/batch")
async def batch_get_variables(
    keys: List[str],
    scope: str = Query("global", pattern="^(session|user|global)$"),
    current_user: Dict = Depends(get_current_user)
):
    """批量获取变量"""
    results = {}
    for key in keys:
        var_key = f"{scope}:{current_user['id']}:{key}"
        if var_key in _variables_store:
            results[key] = _variables_store[var_key]["value"]
    return results

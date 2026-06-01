from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.platform.model_service.model_service import ModelService
from app.schemas.api import (
    CreateModelConfigRequest,
    CreateProviderRequest,
    ModelConfigResponse,
    ModelProviderResponse,
    StatusResponse,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/providers")
async def create_provider(
    body: CreateProviderRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    return await svc.create_provider(tenant_id=user["tenant_id"], data=body.model_dump())


@router.get("/providers")
async def list_providers(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    return await svc.list_providers(tenant_id=user["tenant_id"])


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    result = await svc.get_provider(provider_id, tenant_id=user["tenant_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Provider not found")
    return result


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    await svc.delete_provider(provider_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}


@router.post("/configs")
async def create_model_config(
    body: CreateModelConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    data = body.model_dump()
    if data.get("display_name") is None:
        data["display_name"] = data["model_name"]
    return await svc.create_model_config(tenant_id=user["tenant_id"], data=data)


@router.get("/configs")
async def list_model_configs(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    return await svc.list_model_configs(tenant_id=user["tenant_id"])


@router.post("/configs/{config_id}/default")
async def set_default_model(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    await svc.set_default(config_id, tenant_id=user["tenant_id"])
    return {"status": "ok"}


@router.delete("/configs/{config_id}")
async def delete_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = ModelService(db)
    await svc.delete_model_config(config_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}

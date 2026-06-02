from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.models.system import ModelProviderModel
from app.platform.model_service.model_service import ModelService
from app.schemas.api import (
    CreateModelConfigRequest,
    CreateProviderRequest,
    ModelConfigResponse,
    ModelProviderResponse,
    StatusResponse,
)

router = APIRouter(prefix="/models", tags=["models"])

# Well-known model catalogs per provider type
_PROVIDER_MODELS: dict[str, list[dict]] = {
    "openai": [
        {"model_name": "gpt-4o", "display_name": "GPT-4o", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "gpt-4o-mini", "display_name": "GPT-4o Mini", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "gpt-4.1", "display_name": "GPT-4.1", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "gpt-4.1-mini", "display_name": "GPT-4.1 Mini", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "o3", "display_name": "o3", "capabilities": {"reasoning": True, "function_calling": True, "streaming": True}},
        {"model_name": "o4-mini", "display_name": "o4-mini", "capabilities": {"reasoning": True, "function_calling": True, "streaming": True}},
        {"model_name": "gpt-4o-audio-preview", "display_name": "GPT-4o Audio", "capabilities": {"audio": True, "vision": True, "function_calling": True}},
    ],
    "anthropic": [
        {"model_name": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "claude-opus-4-20250514", "display_name": "Claude Opus 4", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
        {"model_name": "claude-3-5-haiku-20241022", "display_name": "Claude 3.5 Haiku", "capabilities": {"vision": True, "function_calling": True, "streaming": True}},
    ],
    "deepseek": [
        {"model_name": "deepseek-chat", "display_name": "DeepSeek V3", "capabilities": {"function_calling": True, "streaming": True}},
        {"model_name": "deepseek-reasoner", "display_name": "DeepSeek R1", "capabilities": {"reasoning": True, "streaming": True}},
    ],
    "ollama": [
        {"model_name": "llama3.1:8b", "display_name": "Llama 3.1 8B", "capabilities": {"streaming": True}},
        {"model_name": "llama3.1:70b", "display_name": "Llama 3.1 70B", "capabilities": {"streaming": True}},
        {"model_name": "qwen2.5:7b", "display_name": "Qwen 2.5 7B", "capabilities": {"streaming": True}},
        {"model_name": "mistral:7b", "display_name": "Mistral 7B", "capabilities": {"streaming": True}},
        {"model_name": "codellama:13b", "display_name": "Code Llama 13B", "capabilities": {"streaming": True}},
    ],
}


@router.get("/discover/{provider_id}")
async def discover_models(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Auto-discover available models for a provider."""
    stmt = select(ModelProviderModel).where(
        ModelProviderModel.id == provider_id,
        ModelProviderModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_type = provider.provider_type or ""
    models = _PROVIDER_MODELS.get(provider_type, [])

    if not models:
        return {
            "provider_id": provider_id,
            "provider_type": provider_type,
            "models": [],
            "message": f"No catalog for provider type '{provider_type}'. Add models manually.",
        }

    # Check which models are already configured
    svc = ModelService(db)
    existing = await svc.list_model_configs(tenant_id=user["tenant_id"])
    existing_names = {c.get("model_name") for c in existing} if existing else set()

    available = []
    for m in models:
        available.append({
            **m,
            "already_configured": m["model_name"] in existing_names,
        })

    return {
        "provider_id": provider_id,
        "provider_type": provider_type,
        "models": available,
    }


@router.post("/providers")
async def create_provider(
    body: CreateProviderRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("model", "create"))):
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
    user: dict = Depends(require_permission("model", "delete"))):
    svc = ModelService(db)
    await svc.delete_provider(provider_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}


@router.post("/configs")
async def create_model_config(
    body: CreateModelConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("model", "create"))):
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
    user: dict = Depends(require_permission("model", "update"))):
    svc = ModelService(db)
    await svc.set_default(config_id, tenant_id=user["tenant_id"])
    return {"status": "ok"}


@router.delete("/configs/{config_id}")
async def delete_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("model", "delete"))):
    svc = ModelService(db)
    await svc.delete_model_config(config_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}

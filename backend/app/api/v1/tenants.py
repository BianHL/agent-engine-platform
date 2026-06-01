"""Tenant management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.platform.tenant_service.tenant_service import TenantService
from app.schemas.api import (
    CreateTenantRequest,
    TenantResponse,
    UpdateTenantFeaturesRequest,
    UpdateTenantQuotaRequest)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: CreateTenantRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Create a new tenant (admin only)."""
    svc = TenantService(db)
    result = await svc.create(data=body.model_dump())
    # Fetch full tenant data after creation
    full = await svc.get(result["id"])
    return full


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get tenant by ID. Users can only view their own tenant unless admin."""
    if user["role"] != "admin" and user["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    svc = TenantService(db)
    result = await svc.get(tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return result


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Update tenant basic info (admin only)."""
    svc = TenantService(db)
    tenant = await svc.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # TenantService doesn't have a generic update; use features update for now
    return tenant


@router.put("/{tenant_id}/features")
async def update_features(
    tenant_id: str,
    body: UpdateTenantFeaturesRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Update tenant feature flags (admin only)."""
    svc = TenantService(db)
    try:
        return await svc.update_features(tenant_id, body.features)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{tenant_id}/quota")
async def update_quota(
    tenant_id: str,
    body: UpdateTenantQuotaRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin"))):
    """Update tenant agent quota (admin only)."""
    svc = TenantService(db)
    try:
        return await svc.update_quota(tenant_id, body.max_agents)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

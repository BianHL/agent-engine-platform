"""Usage and Model related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UsageSummaryResponse(BaseModel):
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0


class DailyUsageResponse(BaseModel):
    date: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    cost: float
    requests: int


class ModelUsageResponse(BaseModel):
    model_name: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost: float
    requests: int


class CreateProviderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., min_length=1)
    api_key: str = ""
    api_base: str = ""
    api_version: Optional[str] = None
    config: dict = {}


class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None


class CreateModelConfigRequest(BaseModel):
    provider_id: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    model_type: str = "llm"
    display_name: Optional[str] = None
    config: dict = {}
    is_default: bool = False
    max_context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    input_price_per_1k: Optional[Decimal] = None
    output_price_per_1k: Optional[Decimal] = None


class UpdateModelConfigRequest(BaseModel):
    display_name: Optional[str] = None
    config: Optional[dict] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None
    max_context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    input_price_per_1k: Optional[Decimal] = None
    output_price_per_1k: Optional[Decimal] = None


class ModelProviderResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    provider_type: str
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    status: str
    last_health_check_at: Optional[datetime] = None
    health_status: Optional[str] = None
    health_error_message: Optional[str] = None
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ModelConfigResponse(BaseModel):
    id: str
    tenant_id: str
    provider_id: str
    model_name: str
    model_type: str
    display_name: Optional[str] = None
    config: dict = {}
    is_default: bool
    enabled: bool
    max_context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    input_price_per_1k: Optional[Decimal] = None
    output_price_per_1k: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenantUsageMonthlyResponse(BaseModel):
    id: str
    tenant_id: str
    year_month: str
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    cost_by_model: Optional[dict] = None
    cost_by_user: Optional[dict] = None
    storage_used_gb: Decimal = Decimal("0")
    bandwidth_used_gb: Decimal = Decimal("0")
    status: str = "draft"
    confirmed_at: Optional[datetime] = None
    invoiced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

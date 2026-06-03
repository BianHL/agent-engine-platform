"""Agent related schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateAgentRequest(BaseModel):
    name: str
    description: str = ""
    icon_url: Optional[str] = None
    category: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    llm_config: Optional[dict] = Field(None, alias="model_config")
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    tools: List[dict] = []
    knowledge_base_ids: List[str] = []
    safety_config: Optional[dict] = None
    visibility: str = "private"

    model_config = {"populate_by_name": True}


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    llm_config: Optional[dict] = Field(None, alias="model_config")
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    tools: Optional[List[dict]] = None
    knowledge_base_ids: Optional[List[str]] = None
    safety_config: Optional[dict] = None
    visibility: Optional[str] = None

    model_config = {"populate_by_name": True}


class AgentResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    icon_url: Optional[str] = None
    category: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    llm_config: dict = {}
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    tools: list = []
    knowledge_base_ids: list = []
    safety_config: dict = {}
    status: str
    visibility: str = "private"
    version: int
    marketplace_item_id: Optional[str] = None
    total_conversations: int = 0
    total_messages: int = 0
    avg_rating: float = 0.0
    last_used_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _map_model_config(cls, data: Any) -> Any:
        if hasattr(data, "model_config") and not isinstance(data, dict):
            # ORM object: copy model_config attribute to llm_config
            values = {}
            for field in cls.model_fields:
                if field == "llm_config":
                    values["llm_config"] = getattr(data, "model_config", {})
                else:
                    values[field] = getattr(data, field, None)
            return values
        return data


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version: int
    config_snapshot: dict
    change_log: Optional[str] = None
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

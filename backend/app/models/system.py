"""System configuration models (RBAC, Webhooks, Triggers, Model Providers, Usage, etc)."""
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, OptimisticLockMixin, generate_uuid


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

class RoleModel(Base, EnterpriseMixin):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, default="")
    is_system = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    data_scope = Column(String(20), default="self")
    version = Column(Integer, default=1)

    # relationships
    tenant = relationship("TenantModel", back_populates="roles")
    role_permissions = relationship("RolePermissionModel", back_populates="role", cascade="all, delete-orphan")


class PermissionModel(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    module = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    role_permissions = relationship("RolePermissionModel", back_populates="permission", cascade="all, delete-orphan")


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    role_id = Column(String(36), ForeignKey("roles.id"), index=True, nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    role = relationship("RoleModel", back_populates="role_permissions")
    permission = relationship("PermissionModel", back_populates="role_permissions")


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class WebhookModel(Base, EnterpriseMixin):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(200))
    events = Column(JSON, default=list)
    headers = Column(JSON, nullable=True)
    max_retries = Column(Integer, default=3)
    retry_interval_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)
    filter_conditions = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)
    total_deliveries = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_delivered_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)

    # relationships
    webhook_events = relationship("WebhookEventModel", back_populates="webhook", cascade="all, delete-orphan")


class WebhookEventModel(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    webhook_id = Column(String(36), ForeignKey("webhooks.id"), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String(20), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivered_at = Column(DateTime)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    # relationships
    webhook = relationship("WebhookModel", back_populates="webhook_events")


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------

class TriggerModel(Base, EnterpriseMixin):
    __tablename__ = "triggers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    trigger_type = Column(String(20), nullable=False)
    config = Column(JSON, default=dict)
    filter_conditions = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)
    total_triggered = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    last_error_message = Column(Text, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)

    # relationships
    workflow = relationship("WorkflowModel", back_populates="triggers")


# ---------------------------------------------------------------------------
# Model Providers & Configs
# ---------------------------------------------------------------------------

class ModelProviderModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "model_providers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(50), nullable=False)
    provider_type = Column(String(50), nullable=False)
    _api_key_encrypted = Column("api_key", String(500), nullable=True)

    @property
    def api_key(self):
        if not self._api_key_encrypted:
            return None
        try:
            from app.core.security import decrypt
            return decrypt(self._api_key_encrypted)
        except Exception:
            return self._api_key_encrypted

    @api_key.setter
    def api_key(self, value):
        if value:
            from app.core.security import encrypt
            self._api_key_encrypted = encrypt(value)
        else:
            self._api_key_encrypted = None

    api_base = Column(String(500))
    api_version = Column(String(20), nullable=True)
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active", index=True)
    last_health_check_at = Column(DateTime, nullable=True)
    health_status = Column(String(20), nullable=True)
    health_error_message = Column(Text, nullable=True)
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(12, 4), default=0.0)
    version = Column(Integer, default=1)

    # relationships
    tenant = relationship("TenantModel", back_populates="model_providers")
    configs = relationship("ModelConfigModel", back_populates="provider", cascade="all, delete-orphan")


class ModelConfigModel(Base, OptimisticLockMixin):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), index=True, nullable=False)
    provider_id = Column(String(36), ForeignKey("model_providers.id"), index=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(20), nullable=False, index=True)
    display_name = Column(String(100))
    config = Column(JSON, default=dict)
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    max_context_tokens = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)
    supports_streaming = Column(Boolean, default=True)
    supports_function_calling = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    input_price_per_1k = Column(Numeric(10, 6), nullable=True)
    output_price_per_1k = Column(Numeric(10, 6), nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    provider = relationship("ModelProviderModel", back_populates="configs")


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

class UsageLogModel(Base):
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), index=True, nullable=False)
    user_id = Column(String(36), index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    conversation_id = Column(String(36), nullable=True)
    message_id = Column(String(36), nullable=True)
    model_provider = Column(String(50))
    model_name = Column(String(100))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cached_tokens = Column(Integer, default=0)
    cost = Column(Numeric(10, 6), default=0.0)
    request_type = Column(String(20))
    status = Column(String(20), default="success")
    latency_ms = Column(Integer, nullable=True)
    trace_id = Column(String(36), nullable=True, index=True)
    parent_trace_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


class ModelUsageDailyModel(Base):
    __tablename__ = "model_usage_daily"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    user_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    date = Column(DateTime, nullable=False)
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cached_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    avg_latency_ms = Column(Integer, nullable=True)
    p99_latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    __table_args__ = (
        UniqueConstraint("tenant_id", "date", "model_provider", "model_name", "user_id", "agent_id", name="uq_model_usage_daily"),
    )


class TenantUsageMonthlyModel(Base):
    """Tenant monthly usage aggregation for billing."""
    __tablename__ = "tenant_usage_monthly"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False)
    year_month = Column(String(7), nullable=False)
    total_requests = Column(Integer, default=0)
    total_input_tokens = Column(BigInteger, default=0)
    total_output_tokens = Column(BigInteger, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    cost_by_model = Column(JSON, nullable=True)
    cost_by_user = Column(JSON, nullable=True)
    storage_used_gb = Column(Numeric(10, 2), default=0.0)
    bandwidth_used_gb = Column(Numeric(10, 2), default=0.0)
    status = Column(String(20), default="draft")
    confirmed_at = Column(DateTime, nullable=True)
    invoiced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    __table_args__ = (
        UniqueConstraint("tenant_id", "year_month", name="uk_tenant_month"),
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

class ToolModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "tools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon_url = Column(String(500), nullable=True)
    tool_type = Column(String(20), nullable=False, index=True)
    api_schema = Column(JSON, default=dict)
    api_endpoint = Column(String(500), nullable=True)
    api_method = Column(String(10), nullable=True)
    api_headers = Column(JSON, nullable=True)
    mcp_server_url = Column(String(500), nullable=True)
    mcp_tool_name = Column(String(100), nullable=True)
    config = Column(JSON, default=dict)
    timeout = Column(Integer, default=30)
    retry_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    total_executions = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_duration_ms = Column(Integer, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)

    # relationships
    executions = relationship("ToolExecutionModel", back_populates="tool", cascade="all, delete-orphan")


class ToolExecutionModel(Base):
    __tablename__ = "tool_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tool_id = Column(String(36), ForeignKey("tools.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    message_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    status = Column(String(20), default="pending")
    duration_ms = Column(Integer)
    error_message = Column(Text)
    trace_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    # relationships
    tool = relationship("ToolModel", back_populates="executions")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationModel(Base, EnterpriseMixin):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True)
    dataset = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    eval_config = Column(JSON, nullable=True)
    status = Column(String(20), default="draft")
    total_runs = Column(Integer, default=0)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)

    # relationships
    runs = relationship("EvaluationRunModel", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationRunModel(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    status = Column(String(20), default="pending", index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer, nullable=True)
    summary = Column(JSON, default=dict)
    avg_scores = Column(JSON, nullable=True)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    evaluation = relationship("EvaluationModel", back_populates="runs")
    results = relationship("EvaluationResultModel", back_populates="run", cascade="all, delete-orphan")


class EvaluationResultModel(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("evaluation_runs.id"), index=True, nullable=False)
    evaluation_id = Column(String(36), nullable=False, index=True)
    test_case_index = Column(Integer, nullable=False)
    input_text = Column(Text)
    expected_output = Column(Text)
    actual_output = Column(Text)
    scores = Column(JSON, default=dict)
    overall_score = Column(Float, nullable=True)
    latency_ms = Column(Integer)
    token_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    run = relationship("EvaluationRunModel", back_populates="results")


# ---------------------------------------------------------------------------
# OAuth & Account Integration
# ---------------------------------------------------------------------------

class OAuthProviderModel(Base, EnterpriseMixin):
    __tablename__ = "oauth_providers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    provider_name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=True)
    config = Column(JSON, default=dict)
    attribute_mapping = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)
    total_logins = Column(Integer, default=0)
    last_login_at = Column(DateTime, nullable=True)

    # relationships
    integrations = relationship("AccountIntegrateModel", back_populates="provider", cascade="all, delete-orphan")


class AccountIntegrateModel(Base):
    __tablename__ = "account_integrates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    provider_id = Column(String(36), ForeignKey("oauth_providers.id"), index=True, nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    external_id = Column(String(200), nullable=False)
    external_username = Column(String(200), nullable=True)
    external_email = Column(String(200), nullable=True)
    _access_token_encrypted = Column("access_token", String(500), nullable=True)
    _refresh_token_encrypted = Column("refresh_token", String(500), nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    raw_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    @property
    def access_token(self):
        if not self._access_token_encrypted:
            return None
        try:
            from app.core.security import decrypt
            return decrypt(self._access_token_encrypted)
        except Exception:
            return self._access_token_encrypted

    @access_token.setter
    def access_token(self, value):
        if value:
            from app.core.security import encrypt
            self._access_token_encrypted = encrypt(value)
        else:
            self._access_token_encrypted = None

    @property
    def refresh_token(self):
        if not self._refresh_token_encrypted:
            return None
        try:
            from app.core.security import decrypt
            return decrypt(self._refresh_token_encrypted)
        except Exception:
            return self._refresh_token_encrypted

    @refresh_token.setter
    def refresh_token(self, value):
        if value:
            from app.core.security import encrypt
            self._refresh_token_encrypted = encrypt(value)
        else:
            self._refresh_token_encrypted = None

    # relationships
    provider = relationship("OAuthProviderModel", back_populates="integrations")


# ---------------------------------------------------------------------------
# App Templates & Marketplace
# ---------------------------------------------------------------------------

class AppTemplateModel(Base, EnterpriseMixin):
    __tablename__ = "app_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), index=True)
    config = Column(JSON, default=dict)
    icon = Column(String(500))
    cover_image = Column(String(500), nullable=True)
    status = Column(String(20), default="active")
    is_system = Column(Boolean, default=False)
    install_count = Column(Integer, default=0)
    version = Column(String(20), default="1.0.0")


class MarketplaceAppModel(Base):
    __tablename__ = "marketplace_apps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50))
    config = Column(JSON, default=dict)
    version = Column(String(20))
    status = Column(String(20), default="pending", index=True)
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    installations = relationship("AppInstallationModel", back_populates="app", cascade="all, delete-orphan")


class AppInstallationModel(Base):
    __tablename__ = "app_installations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    app_id = Column(String(36), ForeignKey("marketplace_apps.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    installed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    installed_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    uninstalled_at = Column(DateTime, nullable=True)

    # relationships
    app = relationship("MarketplaceAppModel", back_populates="installations")


# ---------------------------------------------------------------------------
# Share Links & File Assets
# ---------------------------------------------------------------------------

class ShareLinkModel(Base):
    __tablename__ = "share_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    resource_type = Column(String(30), nullable=False)
    resource_id = Column(String(36), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    permissions = Column(JSON, default=dict)
    password = Column(String(200), nullable=True)
    max_access_count = Column(Integer, nullable=True)
    access_count = Column(Integer, default=0)
    allowed_ips = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class FileAssetModel(Base):
    __tablename__ = "file_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    file_hash = Column(String(64), nullable=True, index=True)
    storage_path = Column(String(500), nullable=False)
    storage_type = Column(String(20), default="local")
    resource_type = Column(String(30), nullable=True)
    resource_id = Column(String(36), nullable=True)
    is_public = Column(Boolean, default=False)
    access_url = Column(String(500), nullable=True)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


# ---------------------------------------------------------------------------
# Tenant Invitations
# ---------------------------------------------------------------------------

class TenantInvitationModel(Base):
    __tablename__ = "tenant_invitations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    email = Column(String(200), nullable=False, index=True)
    role = Column(String(20), default="user")
    role_id = Column(String(36), nullable=True)
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", index=True)
    token = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackModel(Base):
    """Generic feedback model for various entities."""
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    rating = Column(String(10), nullable=False)
    comment = Column(Text)
    tags = Column(JSON, nullable=True)
    meta_info = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


# ---------------------------------------------------------------------------
# Trace Spans (Distributed Tracing)
# ---------------------------------------------------------------------------

class TraceSpanModel(Base):
    """Distributed tracing span model."""
    __tablename__ = "trace_spans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    trace_id = Column(String(36), nullable=False, index=True)
    parent_span_id = Column(String(36), nullable=True, index=True)
    span_type = Column(String(30), nullable=False)
    name = Column(String(200), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    conversation_id = Column(String(36), nullable=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), default="ok")
    error_message = Column(Text, nullable=True)
    input = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    tokens = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

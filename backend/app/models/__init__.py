"""ORM Models - Unified exports.

This module re-exports all models for backward compatibility.
Existing imports like `from app.models.base import AgentModel` will continue to work.

New code can use:
- `from app.models import AgentModel` (recommended)
- `from app.models.agent import AgentModel` (domain-specific)
"""
import sys

# Import all domain models first
from app.models.agent import AgentModel, AgentTagModel, AgentVersionModel
from app.models.audit import OperationLogModel
from app.models.base import Base, generate_uuid
from app.models.conversation import (
    ConversationModel,
    ConversationVariableModel,
    MessageAnnotationModel,
    MessageFeedbackModel,
    MessageModel,
)
from app.models.knowledge import DocumentModel, DocumentSegmentModel, KnowledgeBaseModel
from app.models.extended import ABTestModel, ComplianceReportModel, PluginInstallModel, PluginModel, PluginRatingModel
from app.models.marketplace import MarketplaceChangeLogModel, MarketplaceCloneModel, MarketplaceItem, MarketplaceRatingModel, MarketplaceReviewModel
from app.models.multi_agent import CrewExecutionModel, CrewModel, HandoffModel, TaskModel
from app.models.publish_channel import PublishChannelModel
from app.models.system import (
    AccountIntegrateModel,
    AppInstallationModel,
    AppTemplateModel,
    EvaluationModel,
    EvaluationResultModel,
    EvaluationRunModel,
    FeedbackModel,
    FileAssetModel,
    MarketplaceAppModel,
    ModelConfigModel,
    ModelProviderModel,
    ModelUsageDailyModel,
    OAuthProviderModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    ShareLinkModel,
    TenantInvitationModel,
    TenantUsageMonthlyModel,
    ToolExecutionModel,
    ToolModel,
    TraceSpanModel,
    TriggerModel,
    UsageLogModel,
    WebhookEventModel,
    WebhookModel,
)
from app.models.tenant import DepartmentModel, TagBindingModel, TagModel as TenantTagModel, TenantModel
from app.models.user import ApiTokenModel, UserModel, UserRoleModel, UserSessionModel
from app.models.workflow import (
    WorkflowEdgeModel,
    WorkflowExecutionModel,
    WorkflowModel,
    WorkflowNodeModel,
    WorkflowVersionModel,
)

# Monkey-patch app.models.base to re-export all models for backward compatibility
# This ensures existing imports like `from app.models.base import AgentModel` continue to work
import app.models.base as base_module

# Export all models to base module
base_module.AgentModel = AgentModel
base_module.AgentTagModel = AgentTagModel
base_module.AgentVersionModel = AgentVersionModel
base_module.ApiTokenModel = ApiTokenModel
base_module.CrewExecutionModel = CrewExecutionModel
base_module.CrewModel = CrewModel
base_module.ConversationModel = ConversationModel
base_module.ConversationVariableModel = ConversationVariableModel
base_module.DepartmentModel = DepartmentModel
base_module.DocumentModel = DocumentModel
base_module.DocumentSegmentModel = DocumentSegmentModel
base_module.EvaluationModel = EvaluationModel
base_module.EvaluationResultModel = EvaluationResultModel
base_module.EvaluationRunModel = EvaluationRunModel
base_module.FeedbackModel = FeedbackModel
base_module.FileAssetModel = FileAssetModel
base_module.HandoffModel = HandoffModel
base_module.ABTestModel = ABTestModel
base_module.ComplianceReportModel = ComplianceReportModel
base_module.PluginModel = PluginModel
base_module.PluginInstallModel = PluginInstallModel
base_module.PluginRatingModel = PluginRatingModel
base_module.PublishChannelModel = PublishChannelModel
base_module.KnowledgeBaseModel = KnowledgeBaseModel
base_module.MarketplaceItem = MarketplaceItem
base_module.MarketplaceReviewModel = MarketplaceReviewModel
base_module.MarketplaceRatingModel = MarketplaceRatingModel
base_module.MarketplaceCloneModel = MarketplaceCloneModel
base_module.MarketplaceChangeLogModel = MarketplaceChangeLogModel
base_module.MarketplaceAppModel = MarketplaceAppModel
base_module.MessageAnnotationModel = MessageAnnotationModel
base_module.MessageFeedbackModel = MessageFeedbackModel
base_module.MessageModel = MessageModel
base_module.ModelConfigModel = ModelConfigModel
base_module.ModelProviderModel = ModelProviderModel
base_module.ModelUsageDailyModel = ModelUsageDailyModel
base_module.OperationLogModel = OperationLogModel
base_module.OAuthProviderModel = OAuthProviderModel
base_module.PermissionModel = PermissionModel
base_module.RoleModel = RoleModel
base_module.RolePermissionModel = RolePermissionModel
base_module.ShareLinkModel = ShareLinkModel
base_module.TagBindingModel = TagBindingModel
base_module.TaskModel = TaskModel
base_module.TenantInvitationModel = TenantInvitationModel
base_module.TenantModel = TenantModel
base_module.TenantTagModel = TenantTagModel
base_module.TenantUsageMonthlyModel = TenantUsageMonthlyModel
base_module.ToolExecutionModel = ToolExecutionModel
base_module.ToolModel = ToolModel
base_module.TraceSpanModel = TraceSpanModel
base_module.TriggerModel = TriggerModel
base_module.UsageLogModel = UsageLogModel
base_module.UserModel = UserModel
base_module.UserRoleModel = UserRoleModel
base_module.UserSessionModel = UserSessionModel
base_module.WebhookEventModel = WebhookEventModel
base_module.WebhookModel = WebhookModel
base_module.WorkflowEdgeModel = WorkflowEdgeModel
base_module.WorkflowExecutionModel = WorkflowExecutionModel
base_module.WorkflowModel = WorkflowModel
base_module.WorkflowNodeModel = WorkflowNodeModel
base_module.WorkflowVersionModel = WorkflowVersionModel

# Also export to app.models package
sys.modules[__name__].AgentModel = AgentModel
sys.modules[__name__].AgentTagModel = AgentTagModel
sys.modules[__name__].AgentVersionModel = AgentVersionModel
sys.modules[__name__].ApiTokenModel = ApiTokenModel
sys.modules[__name__].CrewExecutionModel = CrewExecutionModel
sys.modules[__name__].CrewModel = CrewModel
sys.modules[__name__].ConversationModel = ConversationModel
sys.modules[__name__].ConversationVariableModel = ConversationVariableModel
sys.modules[__name__].DepartmentModel = DepartmentModel
sys.modules[__name__].DocumentModel = DocumentModel
sys.modules[__name__].DocumentSegmentModel = DocumentSegmentModel
sys.modules[__name__].EvaluationModel = EvaluationModel
sys.modules[__name__].EvaluationResultModel = EvaluationResultModel
sys.modules[__name__].EvaluationRunModel = EvaluationRunModel
sys.modules[__name__].FeedbackModel = FeedbackModel
sys.modules[__name__].FileAssetModel = FileAssetModel
sys.modules[__name__].HandoffModel = HandoffModel
sys.modules[__name__].ABTestModel = ABTestModel
sys.modules[__name__].ComplianceReportModel = ComplianceReportModel
sys.modules[__name__].PluginModel = PluginModel
sys.modules[__name__].PluginInstallModel = PluginInstallModel
sys.modules[__name__].PluginRatingModel = PluginRatingModel
sys.modules[__name__].PublishChannelModel = PublishChannelModel
sys.modules[__name__].KnowledgeBaseModel = KnowledgeBaseModel
sys.modules[__name__].MarketplaceItem = MarketplaceItem
sys.modules[__name__].MarketplaceReviewModel = MarketplaceReviewModel
sys.modules[__name__].MarketplaceRatingModel = MarketplaceRatingModel
sys.modules[__name__].MarketplaceCloneModel = MarketplaceCloneModel
sys.modules[__name__].MarketplaceChangeLogModel = MarketplaceChangeLogModel
sys.modules[__name__].MarketplaceAppModel = MarketplaceAppModel
sys.modules[__name__].MessageAnnotationModel = MessageAnnotationModel
sys.modules[__name__].MessageFeedbackModel = MessageFeedbackModel
sys.modules[__name__].MessageModel = MessageModel
sys.modules[__name__].ModelConfigModel = ModelConfigModel
sys.modules[__name__].ModelProviderModel = ModelProviderModel
sys.modules[__name__].ModelUsageDailyModel = ModelUsageDailyModel
sys.modules[__name__].OperationLogModel = OperationLogModel
sys.modules[__name__].OAuthProviderModel = OAuthProviderModel
sys.modules[__name__].PermissionModel = PermissionModel
sys.modules[__name__].RoleModel = RoleModel
sys.modules[__name__].RolePermissionModel = RolePermissionModel
sys.modules[__name__].ShareLinkModel = ShareLinkModel
sys.modules[__name__].TagBindingModel = TagBindingModel
sys.modules[__name__].TaskModel = TaskModel
sys.modules[__name__].TenantInvitationModel = TenantInvitationModel
sys.modules[__name__].TenantModel = TenantModel
sys.modules[__name__].TenantTagModel = TenantTagModel
sys.modules[__name__].TenantUsageMonthlyModel = TenantUsageMonthlyModel
sys.modules[__name__].ToolExecutionModel = ToolExecutionModel
sys.modules[__name__].ToolModel = ToolModel
sys.modules[__name__].TraceSpanModel = TraceSpanModel
sys.modules[__name__].TriggerModel = TriggerModel
sys.modules[__name__].UsageLogModel = UsageLogModel
sys.modules[__name__].UserModel = UserModel
sys.modules[__name__].UserRoleModel = UserRoleModel
sys.modules[__name__].UserSessionModel = UserSessionModel
sys.modules[__name__].WebhookEventModel = WebhookEventModel
sys.modules[__name__].WebhookModel = WebhookModel
sys.modules[__name__].WorkflowEdgeModel = WorkflowEdgeModel
sys.modules[__name__].WorkflowExecutionModel = WorkflowExecutionModel
sys.modules[__name__].WorkflowModel = WorkflowModel
sys.modules[__name__].WorkflowNodeModel = WorkflowNodeModel
sys.modules[__name__].WorkflowVersionModel = WorkflowVersionModel

__all__ = [
    # Base
    "Base",
    "generate_uuid",
    # Tenant & Organization
    "TenantModel",
    "DepartmentModel",
    "TenantTagModel",
    "TagBindingModel",
    # User & Auth
    "UserModel",
    "ApiTokenModel",
    "UserRoleModel",
    "UserSessionModel",
    # Agent
    "AgentModel",
    "AgentVersionModel",
    "AgentTagModel",
    # Knowledge
    "KnowledgeBaseModel",
    "DocumentModel",
    "DocumentSegmentModel",
    # Workflow
    "WorkflowModel",
    "WorkflowNodeModel",
    "WorkflowEdgeModel",
    "WorkflowExecutionModel",
    "WorkflowVersionModel",
    # Multi-Agent
    "CrewModel",
    "CrewExecutionModel",
    "TaskModel",
    "HandoffModel",
    # Conversation
    "ConversationModel",
    "MessageModel",
    "ConversationVariableModel",
    "MessageFeedbackModel",
    "MessageAnnotationModel",
    # Audit
    "OperationLogModel",
    # System
    "RoleModel",
    "PermissionModel",
    "RolePermissionModel",
    "WebhookModel",
    "WebhookEventModel",
    "TriggerModel",
    "ModelProviderModel",
    "ModelConfigModel",
    "UsageLogModel",
    "ModelUsageDailyModel",
    "TenantUsageMonthlyModel",
    "ToolModel",
    "ToolExecutionModel",
    "EvaluationModel",
    "EvaluationRunModel",
    "EvaluationResultModel",
    "OAuthProviderModel",
    "AccountIntegrateModel",
    "AppTemplateModel",
    "MarketplaceAppModel",
    "AppInstallationModel",
    "ShareLinkModel",
    "FileAssetModel",
    "TenantInvitationModel",
    "FeedbackModel",
    "TraceSpanModel",
    # Marketplace
    "ABTestModel",
    "PluginModel",
    "PluginInstallModel",
    "PluginRatingModel",
    "PublishChannelModel",
    "ComplianceReportModel",
    "MarketplaceItem",
    "MarketplaceReviewModel",
    "MarketplaceRatingModel",
    "MarketplaceCloneModel",
    "MarketplaceChangeLogModel",
]

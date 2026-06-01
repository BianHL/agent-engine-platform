-- ================================================================
-- Agent Engine Platform - Enterprise Database Initialization
-- Version: 2.0.0
-- Date: 2026-05-29
-- Description: 企业级AI Agent平台数据库表结构
--   - 完整的多租户支持
--   - 软删除 + 审计追踪
--   - 乐观锁版本控制
--   - 业务冗余字段提升查询性能
--   - 支持水平扩展和分区
-- ================================================================

CREATE DATABASE IF NOT EXISTS agent_engine
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE agent_engine;

-- ============================================================
-- 租户与组织架构
-- ============================================================

-- 租户表 - 支持组织层级
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '租户名称',
    code VARCHAR(50) UNIQUE NOT NULL COMMENT '租户编码，用于URL和API标识',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/suspended/deleted',
    parent_id VARCHAR(36) NULL COMMENT '父租户ID，支持集团-子公司层级',
    org_level VARCHAR(20) NOT NULL DEFAULT 'company' COMMENT 'company/division/department/team',
    org_path VARCHAR(500) NOT NULL DEFAULT '' COMMENT '组织路径，如 /root/company1/division1',
    max_agents INT NOT NULL DEFAULT 10 COMMENT '最大Agent数量限制',
    max_users INT NOT NULL DEFAULT 100 COMMENT '最大用户数量限制',
    max_storage_gb INT NOT NULL DEFAULT 10 COMMENT '最大存储空间(GB)',
    features JSON NULL COMMENT '功能开关配置',
    settings JSON NULL COMMENT '租户级系统设置',
    subscription_plan VARCHAR(20) NOT NULL DEFAULT 'free' COMMENT 'free/pro/enterprise',
    subscription_expires_at DATETIME NULL COMMENT '订阅到期时间',
    billing_email VARCHAR(200) NULL COMMENT '账单邮箱',
    contact_name VARCHAR(100) NULL COMMENT '联系人姓名',
    contact_phone VARCHAR(30) NULL COMMENT '联系人电话',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Shanghai' COMMENT '租户时区',
    locale VARCHAR(10) NOT NULL DEFAULT 'zh-CN' COMMENT '语言区域设置',
    created_by VARCHAR(36) NULL COMMENT '创建者用户ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL COMMENT '软删除时间',
    version INT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
    INDEX idx_tenants_parent (parent_id),
    INDEX idx_tenants_status (status),
    INDEX idx_tenants_org_path (org_path),
    INDEX idx_tenants_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户表';

-- 部门表
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL COMMENT '所属租户',
    name VARCHAR(100) NOT NULL COMMENT '部门名称',
    code VARCHAR(50) NULL COMMENT '部门编码',
    parent_id VARCHAR(36) NULL COMMENT '上级部门ID',
    level INT NOT NULL DEFAULT 1 COMMENT '部门层级',
    path VARCHAR(500) NOT NULL DEFAULT '' COMMENT '部门路径',
    leader_id VARCHAR(36) NULL COMMENT '部门负责人用户ID',
    sort_order INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_dept_tenant (tenant_id),
    INDEX idx_dept_parent (parent_id),
    INDEX idx_dept_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- ============================================================
-- 用户与认证
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL COMMENT '所属租户',
    username VARCHAR(50) NOT NULL COMMENT '登录用户名',
    email VARCHAR(200) NULL COMMENT '邮箱，租户内唯一',
    phone VARCHAR(30) NULL COMMENT '手机号',
    hashed_password VARCHAR(200) NOT NULL COMMENT '加密后的密码',
    salt VARCHAR(64) NULL COMMENT '密码盐值',
    nickname VARCHAR(100) NULL COMMENT '用户昵称/显示名',
    avatar_url VARCHAR(500) NULL COMMENT '头像URL',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT 'admin/editor/user - 兼容旧逻辑',
    department_id VARCHAR(36) NULL COMMENT '所属部门',
    position VARCHAR(100) NULL COMMENT '职位',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled/locked/pending',
    last_login_at DATETIME NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) NULL COMMENT '最后登录IP',
    login_count INT NOT NULL DEFAULT 0 COMMENT '累计登录次数',
    password_changed_at DATETIME NULL COMMENT '密码最后修改时间',
    email_verified_at DATETIME NULL COMMENT '邮箱验证时间',
    phone_verified_at DATETIME NULL COMMENT '手机验证时间',
    settings JSON NULL COMMENT '用户个人设置',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    UNIQUE KEY uk_users_tenant_username (tenant_id, username),
    UNIQUE KEY uk_users_tenant_email (tenant_id, email),
    INDEX idx_users_tenant (tenant_id),
    INDEX idx_users_department (department_id),
    INDEX idx_users_status (status),
    INDEX idx_users_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 用户角色关联表（多对多，补充users.role字段）
CREATE TABLE IF NOT EXISTS user_roles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    role_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) NULL,
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_ur_user (user_id),
    INDEX idx_ur_role (role_id),
    INDEX idx_ur_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- API Token表
CREATE TABLE IF NOT EXISTS api_tokens (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT 'Token名称/用途描述',
    token_prefix VARCHAR(10) NOT NULL COMMENT 'Token前缀，用于快速识别',
    token_hash VARCHAR(200) NOT NULL COMMENT 'Token哈希值',
    permissions JSON NULL COMMENT '权限范围',
    rate_limit INT NULL COMMENT '每分钟请求限制',
    allowed_ips JSON NULL COMMENT 'IP白名单',
    expires_at DATETIME NULL COMMENT '过期时间',
    last_used_at DATETIME NULL COMMENT '最后使用时间',
    last_used_ip VARCHAR(45) NULL COMMENT '最后使用IP',
    usage_count INT NOT NULL DEFAULT 0 COMMENT '累计使用次数',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/revoked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at DATETIME NULL,
    INDEX idx_tokens_tenant (tenant_id),
    INDEX idx_tokens_user (user_id),
    INDEX idx_tokens_hash (token_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API Token表';

-- 用户会话表（JWT管理）
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    session_token VARCHAR(500) NOT NULL COMMENT '会话Token哈希',
    refresh_token VARCHAR(500) NULL COMMENT '刷新Token哈希',
    device_type VARCHAR(30) NULL COMMENT 'desktop/mobile/tablet/api',
    device_info VARCHAR(500) NULL COMMENT '设备信息',
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    expires_at DATETIME NOT NULL,
    last_active_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';

-- ============================================================
-- RBAC 权限管理
-- ============================================================

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '角色名称',
    code VARCHAR(50) NOT NULL COMMENT '角色编码',
    description TEXT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否系统内置角色',
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认角色',
    priority INT NOT NULL DEFAULT 0 COMMENT '角色优先级，数值越大优先级越高',
    data_scope VARCHAR(20) NOT NULL DEFAULT 'self' COMMENT 'all/dept/dept_and_children/self',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    UNIQUE KEY uk_roles_tenant_code (tenant_id, code),
    INDEX idx_roles_tenant (tenant_id),
    INDEX idx_roles_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(36) PRIMARY KEY,
    module VARCHAR(50) NOT NULL COMMENT '模块: agent/knowledge/workflow/tool/model/user/tenant/system',
    resource VARCHAR(50) NOT NULL COMMENT '资源: agent/document/workflow/...',
    action VARCHAR(20) NOT NULL COMMENT '操作: create/read/update/delete/execute/publish/export',
    name VARCHAR(100) NOT NULL COMMENT '权限名称，如 agent:create',
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_perm_name (name),
    INDEX idx_perm_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id VARCHAR(36) PRIMARY KEY,
    role_id VARCHAR(36) NOT NULL,
    permission_id VARCHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role_perm (role_id, permission_id),
    INDEX idx_rp_role (role_id),
    INDEX idx_rp_perm (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- ============================================================
-- 标签系统
-- ============================================================

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '标签名称',
    color VARCHAR(7) NULL COMMENT '标签颜色，如 #FF0000',
    category VARCHAR(30) NULL COMMENT '标签分类：system/custom',
    usage_count INT NOT NULL DEFAULT 0 COMMENT '使用次数统计',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tags_tenant_name (tenant_id, name),
    INDEX idx_tags_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- 标签绑定表
CREATE TABLE IF NOT EXISTS tag_bindings (
    id VARCHAR(36) PRIMARY KEY,
    tag_id VARCHAR(36) NOT NULL,
    target_type VARCHAR(30) NOT NULL COMMENT 'agent/knowledge_base/workflow/tool',
    target_id VARCHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tag_target (tag_id, target_type, target_id),
    INDEX idx_tb_tag (tag_id),
    INDEX idx_tb_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签绑定表';

-- ============================================================
-- Agent 智能体
-- ============================================================

-- Agent主表
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL COMMENT '所属租户',
    name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    description TEXT NULL COMMENT 'Agent描述',
    icon_url VARCHAR(500) NULL COMMENT 'Agent图标URL',
    category VARCHAR(50) NULL COMMENT '分类：customer_service/education/code/general',
    -- 模型配置
    model_provider VARCHAR(50) NULL COMMENT '模型提供商',
    model_name VARCHAR(100) NULL COMMENT '模型名称',
    model_config JSON NULL COMMENT '模型参数：temperature, max_tokens等',
    -- 提示词配置
    system_prompt TEXT NULL COMMENT '系统提示词',
    user_prompt_template TEXT NULL COMMENT '用户提示词模板',
    -- 工具与知识库配置
    tools JSON NULL COMMENT '绑定的工具列表',
    knowledge_base_ids JSON NULL COMMENT '绑定的知识库ID列表',
    -- 安全配置
    safety_config JSON NULL COMMENT '安全配置：PII检测、内容审核等',
    -- 状态与版本
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/published/archived',
    visibility VARCHAR(20) NOT NULL DEFAULT 'private' COMMENT 'private/tenant/public',
    version INT NOT NULL DEFAULT 1 COMMENT '当前版本号',
    published_at DATETIME NULL COMMENT '发布时间',
    -- 市场相关
    marketplace_item_id VARCHAR(36) NULL COMMENT '关联的市场应用ID',
    -- 使用统计（冗余字段，定期同步）
    total_conversations INT NOT NULL DEFAULT 0 COMMENT '总会话数',
    total_messages INT NOT NULL DEFAULT 0 COMMENT '总消息数',
    avg_rating FLOAT NOT NULL DEFAULT 0.0 COMMENT '平均评分',
    last_used_at DATETIME NULL COMMENT '最后使用时间',
    -- 审计字段
    created_by VARCHAR(36) NULL COMMENT '创建者用户ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version_lock INT NOT NULL DEFAULT 1 COMMENT '乐观锁',
    INDEX idx_agents_tenant (tenant_id),
    INDEX idx_agents_status (status),
    INDEX idx_agents_category (category),
    INDEX idx_agents_marketplace (marketplace_item_id),
    INDEX idx_agents_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent智能体表';

-- Agent版本历史表
CREATE TABLE IF NOT EXISTS agent_versions (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL COMMENT '所属Agent',
    tenant_id VARCHAR(36) NOT NULL,
    version INT NOT NULL COMMENT '版本号',
    config_snapshot JSON NOT NULL COMMENT '完整配置快照',
    change_log TEXT NULL COMMENT '变更说明',
    published_at DATETIME NULL COMMENT '发布时间',
    published_by VARCHAR(36) NULL COMMENT '发布者',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_av_agent (agent_id),
    INDEX idx_av_version (agent_id, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent版本历史表';

-- Agent标签关联表（兼容旧代码）
CREATE TABLE IF NOT EXISTS agent_tags (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    tag VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_at_agent (agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent标签关联表';

-- ============================================================
-- 模型提供商与配置
-- ============================================================

-- 模型提供商表
CREATE TABLE IF NOT EXISTS model_providers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '提供商名称',
    provider_type VARCHAR(50) NOT NULL COMMENT 'openai/anthropic/custom_openai/ollama',
    api_key VARCHAR(500) NULL COMMENT '加密存储的API Key',
    api_base VARCHAR(500) NULL COMMENT 'API基础URL',
    api_version VARCHAR(20) NULL COMMENT 'API版本',
    config JSON NULL COMMENT '额外配置',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
    -- 健康检查
    last_health_check_at DATETIME NULL,
    health_status VARCHAR(20) NULL COMMENT 'healthy/degraded/down',
    health_error_message TEXT NULL,
    -- 使用统计（冗余）
    total_requests INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(12,4) NOT NULL DEFAULT 0.0000,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_providers_tenant (tenant_id),
    INDEX idx_providers_status (status),
    INDEX idx_providers_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型提供商表';

-- 模型配置表
CREATE TABLE IF NOT EXISTS model_configs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL COMMENT '所属提供商',
    model_name VARCHAR(100) NOT NULL COMMENT '模型标识，如gpt-4o',
    model_type VARCHAR(20) NOT NULL COMMENT 'llm/embedding/rerank/tts/stt/vision',
    display_name VARCHAR(100) NULL COMMENT '显示名称',
    config JSON NULL COMMENT '模型配置参数',
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认模型',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    -- 能力声明
    max_context_tokens INT NULL COMMENT '最大上下文Token数',
    max_output_tokens INT NULL COMMENT '最大输出Token数',
    supports_streaming BOOLEAN NOT NULL DEFAULT TRUE,
    supports_function_calling BOOLEAN NOT NULL DEFAULT FALSE,
    supports_vision BOOLEAN NOT NULL DEFAULT FALSE,
    -- 计费信息
    input_price_per_1k DECIMAL(10,6) NULL COMMENT '输入Token单价(每1K)',
    output_price_per_1k DECIMAL(10,6) NULL COMMENT '输出Token单价(每1K)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_configs_tenant (tenant_id),
    INDEX idx_configs_provider (provider_id),
    INDEX idx_configs_type (model_type),
    INDEX idx_configs_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型配置表';

-- ============================================================
-- 知识库与文档
-- ============================================================

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description TEXT NULL,
    icon_url VARCHAR(500) NULL,
    -- 嵌入模型配置
    embedding_model VARCHAR(100) NULL COMMENT '嵌入模型名称',
    embedding_dimensions INT NULL COMMENT '向量维度',
    -- 存储配置
    vector_collection VARCHAR(200) NULL COMMENT 'Milvus集合名称',
    es_index VARCHAR(200) NULL COMMENT 'ES索引名称',
    graph_enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否启用图谱检索',
    -- 分块配置
    chunk_size INT NOT NULL DEFAULT 500 COMMENT '分块大小(字符数)',
    chunk_overlap INT NOT NULL DEFAULT 50 COMMENT '分块重叠(字符数)',
    chunking_strategy VARCHAR(20) NOT NULL DEFAULT 'recursive' COMMENT 'recursive/semantic/fixed/parent_child',
    -- 检索配置
    retrieval_mode VARCHAR(20) NOT NULL DEFAULT 'hybrid' COMMENT 'naive/local/global/hybrid',
    retrieval_top_k INT NOT NULL DEFAULT 5 COMMENT '默认召回数量',
    score_threshold FLOAT NOT NULL DEFAULT 0.5 COMMENT '相似度阈值',
    rerank_enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否启用重排序',
    rerank_model VARCHAR(100) NULL COMMENT '重排序模型',
    -- 统计（冗余字段）
    document_count INT NOT NULL DEFAULT 0 COMMENT '文档数量',
    segment_count INT NOT NULL DEFAULT 0 COMMENT '分段数量',
    total_tokens INT NOT NULL DEFAULT 0 COMMENT '总Token数',
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/processing/error/archived',
    last_synced_at DATETIME NULL COMMENT '最后同步时间',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_kb_tenant (tenant_id),
    INDEX idx_kb_status (status),
    INDEX idx_kb_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    knowledge_base_id VARCHAR(36) NOT NULL COMMENT '所属知识库',
    filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_type VARCHAR(20) NULL COMMENT '文件类型：pdf/docx/txt/md/html/csv',
    file_size BIGINT NULL COMMENT '文件大小(字节)',
    file_path VARCHAR(500) NULL COMMENT '存储路径',
    file_hash VARCHAR(64) NULL COMMENT '文件内容哈希，用于去重',
    -- 文档元数据
    title VARCHAR(500) NULL COMMENT '文档标题',
    author VARCHAR(200) NULL COMMENT '文档作者',
    language VARCHAR(10) NULL COMMENT '文档语言',
    page_count INT NULL COMMENT '页数',
    -- 处理状态
    chunk_count INT NOT NULL DEFAULT 0 COMMENT '分块数量',
    token_count INT NOT NULL DEFAULT 0 COMMENT 'Token数量',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/processing/completed/failed',
    error_message TEXT NULL,
    task_id VARCHAR(100) NULL COMMENT '异步任务ID',
    processed_at DATETIME NULL COMMENT '处理完成时间',
    -- 索引状态
    vector_indexed BOOLEAN NOT NULL DEFAULT FALSE COMMENT '向量索引是否完成',
    es_indexed BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'ES索引是否完成',
    graph_indexed BOOLEAN NOT NULL DEFAULT FALSE COMMENT '图谱索引是否完成',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_docs_tenant (tenant_id),
    INDEX idx_docs_kb (knowledge_base_id),
    INDEX idx_docs_status (status),
    INDEX idx_docs_hash (file_hash),
    INDEX idx_docs_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';

-- 文档分段表
CREATE TABLE IF NOT EXISTS document_segments (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL COMMENT '所属文档',
    tenant_id VARCHAR(36) NOT NULL,
    knowledge_base_id VARCHAR(36) NOT NULL COMMENT '所属知识库（冗余，加速查询）',
    content TEXT NOT NULL COMMENT '分段内容',
    content_hash VARCHAR(64) NULL COMMENT '内容哈希，用于去重',
    segment_index INT NOT NULL COMMENT '分段序号',
    token_count INT NULL COMMENT 'Token数量',
    -- 向量信息
    vector_id VARCHAR(200) NULL COMMENT 'Milvus向量ID',
    embedding_model VARCHAR(100) NULL COMMENT '使用的嵌入模型',
    -- 层级关系
    parent_id VARCHAR(36) NULL COMMENT '父分段ID（parent-child模式）',
    chunk_type VARCHAR(20) NOT NULL DEFAULT 'text' COMMENT 'text/table/code/image',
    -- 元数据
    chunk_metadata JSON NULL COMMENT '元数据：页码、章节、来源等',
    -- 命中统计（冗余）
    hit_count INT NOT NULL DEFAULT 0 COMMENT '被命中次数',
    last_hit_at DATETIME NULL COMMENT '最后命中时间',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_seg_doc (document_id),
    INDEX idx_seg_kb (knowledge_base_id),
    INDEX idx_seg_parent (parent_id),
    INDEX idx_seg_hash (content_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档分段表';

-- ============================================================
-- 会话与消息
-- ============================================================

-- 会话表
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL COMMENT '发起用户',
    agent_id VARCHAR(36) NOT NULL COMMENT '使用的Agent',
    agent_name VARCHAR(100) NULL COMMENT 'Agent名称（冗余）',
    title VARCHAR(200) NULL COMMENT '会话标题，可自动生成',
    summary TEXT NULL COMMENT '会话摘要',
    -- 会话配置
    model_provider VARCHAR(50) NULL COMMENT '实际使用的模型提供商',
    model_name VARCHAR(100) NULL COMMENT '实际使用的模型名称',
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/archived/deleted',
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否置顶',
    -- 统计（冗余字段）
    message_count INT NOT NULL DEFAULT 0 COMMENT '消息数量',
    total_input_tokens INT NOT NULL DEFAULT 0 COMMENT '总输入Token',
    total_output_tokens INT NOT NULL DEFAULT 0 COMMENT '总输出Token',
    total_cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000 COMMENT '总费用',
    -- 时间戳
    last_message_at DATETIME NULL COMMENT '最后一条消息时间',
    last_message_preview VARCHAR(200) NULL COMMENT '最后消息预览',
    archived_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_conv_tenant (tenant_id),
    INDEX idx_conv_user (user_id),
    INDEX idx_conv_agent (agent_id),
    INDEX idx_conv_status (status),
    INDEX idx_conv_last_msg (last_message_at),
    INDEX idx_conv_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL COMMENT '所属会话',
    tenant_id VARCHAR(36) NOT NULL COMMENT '租户ID（冗余，加速查询）',
    role VARCHAR(20) NOT NULL COMMENT 'user/assistant/system/tool',
    content TEXT NOT NULL COMMENT '消息内容',
    -- Token统计
    input_tokens INT NOT NULL DEFAULT 0 COMMENT '输入Token数',
    output_tokens INT NOT NULL DEFAULT 0 COMMENT '输出Token数',
    total_tokens INT NOT NULL DEFAULT 0 COMMENT '总Token数',
    -- 模型信息
    model_provider VARCHAR(50) NULL COMMENT '模型提供商',
    model_name VARCHAR(100) NULL COMMENT '模型名称',
    -- 工具调用信息
    tool_calls JSON NULL COMMENT '工具调用列表',
    tool_call_id VARCHAR(100) NULL COMMENT '工具调用响应对应的调用ID',
    name VARCHAR(100) NULL COMMENT '工具名称（tool角色时）',
    -- 性能指标
    latency_ms INT NULL COMMENT '响应延迟(毫秒)',
    first_token_ms INT NULL COMMENT '首Token延迟(毫秒)',
    -- 元数据
    message_metadata JSON NULL COMMENT '元数据：finish_reason, usage等',
    -- 引用信息
    citation_sources JSON NULL COMMENT '引用来源列表',
    -- 质量评估
    feedback_score VARCHAR(10) NULL COMMENT 'positive/negative',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_conversation (conversation_id),
    INDEX idx_msg_tenant (tenant_id),
    INDEX idx_msg_role (role),
    INDEX idx_msg_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- 会话变量表
CREATE TABLE IF NOT EXISTS conversation_variables (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    key VARCHAR(100) NOT NULL COMMENT '变量名',
    value TEXT NULL COMMENT '变量值',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cv (conversation_id, `key`),
    INDEX idx_cv_conversation (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话变量表';

-- 消息反馈表
CREATE TABLE IF NOT EXISTS message_feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    rating VARCHAR(10) NOT NULL COMMENT 'positive/negative',
    comment TEXT NULL,
    tags JSON NULL COMMENT '反馈标签：helpful/accurate/creative/etc',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_mf (message_id, user_id),
    INDEX idx_mf_message (message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息反馈表';

-- 消息标注表（用于训练数据优化）
CREATE TABLE IF NOT EXISTS message_annotations (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    question TEXT NULL COMMENT '原始问题',
    corrected_answer TEXT NULL COMMENT '修正后的回答',
    annotation_type VARCHAR(20) NOT NULL DEFAULT 'correction' COMMENT 'correction/addition/verification',
    hit_count INT NOT NULL DEFAULT 0 COMMENT '被命中次数',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ma_message (message_id),
    INDEX idx_ma_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息标注表';

-- ============================================================
-- 工作流
-- ============================================================

-- 工作流表
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36) NULL COMMENT '关联的Agent（可选）',
    name VARCHAR(200) NOT NULL COMMENT '工作流名称',
    description TEXT NULL,
    icon_url VARCHAR(500) NULL,
    category VARCHAR(50) NULL COMMENT '分类',
    -- DAG配置
    dag_config JSON NOT NULL COMMENT 'DAG配置：nodes, edges, viewport',
    -- 执行配置
    max_execution_time INT NULL COMMENT '最大执行时间(秒)',
    max_iterations INT NULL DEFAULT 100 COMMENT '最大迭代次数',
    retry_policy JSON NULL COMMENT '重试策略',
    -- 状态与版本
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/active/archived',
    visibility VARCHAR(20) NOT NULL DEFAULT 'private' COMMENT 'private/tenant/public',
    version INT NOT NULL DEFAULT 1,
    published_at DATETIME NULL,
    -- 统计（冗余）
    total_executions INT NOT NULL DEFAULT 0 COMMENT '总执行次数',
    success_count INT NOT NULL DEFAULT 0 COMMENT '成功次数',
    failure_count INT NOT NULL DEFAULT 0 COMMENT '失败次数',
    avg_duration_ms INT NULL COMMENT '平均执行时长(毫秒)',
    last_executed_at DATETIME NULL,
    -- 审计
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version_lock INT NOT NULL DEFAULT 1 COMMENT '乐观锁',
    INDEX idx_wf_tenant (tenant_id),
    INDEX idx_wf_status (status),
    INDEX idx_wf_agent (agent_id),
    INDEX idx_wf_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流表';

-- 工作流节点表
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    node_id VARCHAR(100) NOT NULL COMMENT '节点ID，工作流内唯一',
    node_type VARCHAR(30) NOT NULL COMMENT 'start/end/llm/condition/parallel/loop/http/code/human_approval/sub_workflow/variable',
    label VARCHAR(200) NULL COMMENT '节点标签',
    description TEXT NULL COMMENT '节点描述',
    config JSON NOT NULL COMMENT '节点配置',
    position_x FLOAT NOT NULL DEFAULT 0,
    position_y FLOAT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_wn_workflow (workflow_id),
    UNIQUE KEY uk_wn_node (workflow_id, node_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流节点表';

-- 工作流边表
CREATE TABLE IF NOT EXISTS workflow_edges (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    source_node_id VARCHAR(100) NOT NULL COMMENT '源节点ID',
    target_node_id VARCHAR(100) NOT NULL COMMENT '目标节点ID',
    source_handle VARCHAR(50) NULL COMMENT '源端口',
    target_handle VARCHAR(50) NULL COMMENT '目标端口',
    condition_expression TEXT NULL COMMENT '条件表达式',
    label VARCHAR(200) NULL COMMENT '边标签',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_we_workflow (workflow_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流边表';

-- 工作流版本历史表
CREATE TABLE IF NOT EXISTS workflow_versions (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    version INT NOT NULL COMMENT '版本号',
    dag_config JSON NOT NULL COMMENT '完整DAG配置快照',
    change_log TEXT NULL COMMENT '变更说明',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_wv_workflow (workflow_id),
    INDEX idx_wv_version (workflow_id, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流版本历史表';

-- 工作流执行记录表
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    workflow_version INT NOT NULL COMMENT '工作流版本',
    tenant_id VARCHAR(36) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL DEFAULT 'manual' COMMENT 'manual/cron/api/event',
    trigger_id VARCHAR(36) NULL COMMENT '触发器ID',
    status VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT 'running/success/failed/cancelled/timeout',
    -- 执行状态
    node_states JSON NOT NULL COMMENT '各节点执行状态',
    current_node_id VARCHAR(100) NULL COMMENT '当前执行节点',
    variables JSON NOT NULL COMMENT '执行变量',
    -- 输入输出
    inputs JSON NULL COMMENT '输入参数',
    outputs JSON NULL COMMENT '输出结果',
    -- 执行日志
    execution_log JSON NULL COMMENT '执行日志',
    node_logs JSON NULL COMMENT '节点级执行日志',
    trace_tree JSON NULL COMMENT '追踪树',
    trace_id VARCHAR(36) NULL COMMENT '链路追踪ID',
    -- 错误信息
    error_message TEXT NULL,
    error_node_id VARCHAR(100) NULL COMMENT '出错节点',
    -- 性能指标
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    duration_ms INT NULL COMMENT '执行时长(毫秒)',
    -- 费用统计
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_wex_workflow (workflow_id),
    INDEX idx_wex_tenant (tenant_id),
    INDEX idx_wex_status (status),
    INDEX idx_wex_trace (trace_id),
    INDEX idx_wex_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流执行记录表';

-- ============================================================
-- 多Agent协作
-- ============================================================

-- 团队(Crew)表
CREATE TABLE IF NOT EXISTS crews (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL COMMENT '团队名称',
    description TEXT NULL,
    process VARCHAR(20) NOT NULL DEFAULT 'sequential' COMMENT 'sequential/hierarchical/parallel/consensus',
    config JSON NOT NULL COMMENT '团队配置：agents, tasks, inputs',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/archived',
    -- 统计
    total_executions INT NOT NULL DEFAULT 0,
    last_executed_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_crews_tenant (tenant_id),
    INDEX idx_crews_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多Agent团队表';

-- 团队执行记录表
CREATE TABLE IF NOT EXISTS crew_executions (
    id VARCHAR(36) PRIMARY KEY,
    crew_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL COMMENT '发起用户',
    status VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT 'running/success/failed/cancelled',
    inputs JSON NOT NULL COMMENT '输入参数',
    results JSON NULL COMMENT '执行结果',
    agent_results JSON NULL COMMENT '各Agent执行结果',
    error_message TEXT NULL,
    -- 性能指标
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    duration_ms INT NULL,
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ce_crew (crew_id),
    INDEX idx_ce_tenant (tenant_id),
    INDEX idx_ce_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='团队执行记录表';

-- Agent移交配置表
CREATE TABLE IF NOT EXISTS agent_handoffs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    source_agent_id VARCHAR(36) NOT NULL COMMENT '源Agent',
    target_agent_ids JSON NOT NULL COMMENT '目标Agent列表',
    handoff_config JSON NOT NULL COMMENT '移交配置：条件、上下文变量、最大跳转次数',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
    -- 统计
    total_handoffs INT NOT NULL DEFAULT 0,
    last_handoff_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_handoffs_source (source_agent_id),
    INDEX idx_handoffs_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent移交配置表';

-- 异步任务表
CREATE TABLE IF NOT EXISTS async_tasks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    task_type VARCHAR(50) NOT NULL COMMENT 'document_processing/evaluation/workflow_execution/export/import',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/running/success/failed/cancelled',
    priority INT NOT NULL DEFAULT 0 COMMENT '优先级，数值越大优先级越高',
    progress JSON NULL COMMENT '{current, total, message, percentage}',
    result JSON NULL COMMENT '任务结果',
    error_message TEXT NULL,
    -- 输入参数
    inputs JSON NULL COMMENT '任务输入参数',
    -- 重试配置
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    -- 关联资源
    resource_type VARCHAR(50) NULL COMMENT '关联资源类型',
    resource_id VARCHAR(36) NULL COMMENT '关联资源ID',
    -- 审计
    created_by VARCHAR(36) NULL,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tasks_tenant (tenant_id),
    INDEX idx_tasks_type (task_type),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步任务表';

-- ============================================================
-- 工具系统
-- ============================================================

-- 工具表
CREATE TABLE IF NOT EXISTS tools (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT '工具名称',
    description TEXT NULL,
    icon_url VARCHAR(500) NULL,
    tool_type VARCHAR(20) NOT NULL COMMENT 'builtin/custom/api/mcp',
    -- API配置（custom/api类型）
    api_schema JSON NULL COMMENT 'OpenAPI规范',
    api_endpoint VARCHAR(500) NULL COMMENT 'API端点',
    api_method VARCHAR(10) NULL COMMENT 'HTTP方法',
    api_headers JSON NULL COMMENT '请求头',
    -- MCP配置（mcp类型）
    mcp_server_url VARCHAR(500) NULL COMMENT 'MCP服务器URL',
    mcp_tool_name VARCHAR(100) NULL COMMENT 'MCP工具名称',
    -- 通用配置
    config JSON NULL COMMENT '工具配置',
    timeout INT NULL DEFAULT 30 COMMENT '超时时间(秒)',
    retry_count INT NULL DEFAULT 0 COMMENT '重试次数',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    -- 统计（冗余）
    total_executions INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failure_count INT NOT NULL DEFAULT 0,
    avg_duration_ms INT NULL,
    last_used_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    version INT NOT NULL DEFAULT 1,
    INDEX idx_tools_tenant (tenant_id),
    INDEX idx_tools_type (tool_type),
    INDEX idx_tools_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工具表';

-- 工具执行记录表
CREATE TABLE IF NOT EXISTS tool_executions (
    id VARCHAR(36) PRIMARY KEY,
    tool_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    conversation_id VARCHAR(36) NULL COMMENT '关联会话',
    message_id VARCHAR(36) NULL COMMENT '关联消息',
    agent_id VARCHAR(36) NULL COMMENT '调用的Agent',
    -- 输入输出
    input_data JSON NOT NULL,
    output_data JSON NULL,
    -- 执行状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/running/success/failed',
    error_message TEXT NULL,
    -- 性能指标
    duration_ms INT NULL,
    -- 审计
    trace_id VARCHAR(36) NULL COMMENT '链路追踪ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_te_tool (tool_id),
    INDEX idx_te_tenant (tenant_id),
    INDEX idx_te_conversation (conversation_id),
    INDEX idx_te_trace (trace_id),
    INDEX idx_te_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工具执行记录表';

-- ============================================================
-- 使用量与计费
-- ============================================================

-- 使用量日志表（原始记录，支持分区）
CREATE TABLE IF NOT EXISTS usage_logs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    agent_id VARCHAR(36) NULL COMMENT '使用的Agent',
    conversation_id VARCHAR(36) NULL COMMENT '关联会话',
    message_id VARCHAR(36) NULL COMMENT '关联消息',
    -- 模型信息
    model_provider VARCHAR(50) NULL,
    model_name VARCHAR(100) NULL,
    -- Token统计
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    cached_tokens INT NOT NULL DEFAULT 0 COMMENT '缓存命中Token',
    -- 费用
    cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    -- 请求信息
    request_type VARCHAR(20) NULL COMMENT 'chat/embedding/rerank/completion',
    status VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT 'success/failed',
    latency_ms INT NULL,
    -- 链路追踪
    trace_id VARCHAR(36) NULL,
    parent_trace_id VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usage_tenant (tenant_id),
    INDEX idx_usage_user (user_id),
    INDEX idx_usage_agent (agent_id),
    INDEX idx_usage_model (model_provider, model_name),
    INDEX idx_usage_created (created_at),
    INDEX idx_usage_trace (trace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用量日志表';

-- 模型使用量日聚合表
CREATE TABLE IF NOT EXISTS model_usage_daily (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL COMMENT '用户维度聚合',
    agent_id VARCHAR(36) NULL COMMENT 'Agent维度聚合',
    date DATE NOT NULL COMMENT '统计日期',
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    -- 聚合指标
    request_count INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failure_count INT NOT NULL DEFAULT 0,
    total_input_tokens INT NOT NULL DEFAULT 0,
    total_output_tokens INT NOT NULL DEFAULT 0,
    total_cached_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(12,6) NOT NULL DEFAULT 0.000000,
    avg_latency_ms INT NULL,
    p99_latency_ms INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_model_usage_daily (tenant_id, date, model_provider, model_name, user_id, agent_id),
    INDEX idx_mud_tenant (tenant_id),
    INDEX idx_mud_date (date),
    INDEX idx_mud_model (model_provider, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型使用量日聚合表';

-- 租户使用量月聚合表（账单用）
CREATE TABLE IF NOT EXISTS tenant_usage_monthly (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    year_month VARCHAR(7) NOT NULL COMMENT '格式：2026-05',
    -- 聚合指标
    total_requests INT NOT NULL DEFAULT 0,
    total_input_tokens BIGINT NOT NULL DEFAULT 0,
    total_output_tokens BIGINT NOT NULL DEFAULT 0,
    total_cost DECIMAL(12,4) NOT NULL DEFAULT 0.0000,
    -- 按模型分组
    cost_by_model JSON NULL COMMENT '{model_name: cost}',
    -- 按用户分组
    cost_by_user JSON NULL COMMENT '{user_id: cost}',
    -- 资源使用
    storage_used_gb DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    bandwidth_used_gb DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/confirmed/invoiced',
    confirmed_at DATETIME NULL,
    invoiced_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tenant_month (tenant_id, year_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户使用量月聚合表';

-- ============================================================
-- 审计日志
-- ============================================================

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL COMMENT '操作用户',
    username VARCHAR(50) NULL COMMENT '用户名（冗余）',
    -- 操作信息
    action VARCHAR(20) NOT NULL COMMENT 'create/update/delete/login/logout/export/import/execute',
    resource_type VARCHAR(50) NULL COMMENT 'agent/knowledge_base/workflow/tool/user/role/tenant',
    resource_id VARCHAR(36) NULL,
    resource_name VARCHAR(200) NULL COMMENT '资源名称（冗余）',
    -- 变更详情
    details JSON NULL COMMENT '变更详情：before, after, diff',
    -- 请求信息
    request_method VARCHAR(10) NULL COMMENT 'HTTP方法',
    request_path VARCHAR(500) NULL COMMENT '请求路径',
    request_body JSON NULL COMMENT '请求体（敏感信息已脱敏）',
    response_status INT NULL COMMENT '响应状态码',
    -- 环境信息
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    -- 风险标记
    risk_level VARCHAR(10) NULL COMMENT 'low/medium/high/critical',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_oplogs_tenant (tenant_id),
    INDEX idx_oplogs_user (user_id),
    INDEX idx_oplogs_resource (resource_type, resource_id),
    INDEX idx_oplogs_action (action),
    INDEX idx_oplogs_created (created_at),
    INDEX idx_oplogs_risk (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================================
-- Webhook系统
-- ============================================================

-- Webhook配置表
CREATE TABLE IF NOT EXISTS webhooks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT 'Webhook名称',
    url VARCHAR(500) NOT NULL COMMENT '回调URL',
    secret VARCHAR(200) NULL COMMENT '签名密钥',
    events JSON NOT NULL COMMENT '订阅的事件列表',
    headers JSON NULL COMMENT '自定义请求头',
    -- 重试配置
    max_retries INT NOT NULL DEFAULT 3,
    retry_interval_seconds INT NOT NULL DEFAULT 60,
    timeout_seconds INT NOT NULL DEFAULT 30,
    -- 过滤条件
    filter_conditions JSON NULL COMMENT '事件过滤条件',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    -- 统计
    total_deliveries INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failure_count INT NOT NULL DEFAULT 0,
    last_delivered_at DATETIME NULL,
    last_error_message TEXT NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_webhooks_tenant (tenant_id),
    INDEX idx_webhooks_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Webhook配置表';

-- Webhook事件投递记录表
CREATE TABLE IF NOT EXISTS webhook_events (
    id VARCHAR(36) PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型',
    payload JSON NOT NULL COMMENT '事件数据',
    -- 投递状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/delivered/failed/retrying',
    retry_count INT NOT NULL DEFAULT 0,
    next_retry_at DATETIME NULL COMMENT '下次重试时间',
    -- 响应信息
    response_status INT NULL COMMENT 'HTTP响应状态码',
    response_body TEXT NULL COMMENT '响应体',
    delivered_at DATETIME NULL,
    -- 错误信息
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_we_webhook (webhook_id),
    INDEX idx_we_status (status),
    INDEX idx_we_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Webhook事件投递记录表';

-- ============================================================
-- 触发器系统
-- ============================================================

-- 触发器配置表
CREATE TABLE IF NOT EXISTS triggers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    workflow_id VARCHAR(36) NOT NULL COMMENT '关联的工作流',
    name VARCHAR(100) NOT NULL COMMENT '触发器名称',
    trigger_type VARCHAR(20) NOT NULL COMMENT 'cron/event/webhook/manual',
    config JSON NOT NULL COMMENT '触发配置：cron表达式或事件规范',
    -- 过滤条件
    filter_conditions JSON NULL COMMENT '触发条件过滤',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    -- 执行统计
    total_triggered INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failure_count INT NOT NULL DEFAULT 0,
    last_triggered_at DATETIME NULL,
    last_error_message TEXT NULL,
    -- 下次执行时间（cron类型）
    next_run_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_triggers_workflow (workflow_id),
    INDEX idx_triggers_tenant (tenant_id),
    INDEX idx_triggers_next_run (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='触发器配置表';

-- ============================================================
-- 评估系统
-- ============================================================

-- 评估任务表
CREATE TABLE IF NOT EXISTS evaluations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL COMMENT '评估名称',
    description TEXT NULL,
    agent_id VARCHAR(36) NULL COMMENT '评估目标Agent',
    workflow_id VARCHAR(36) NULL COMMENT '评估目标工作流',
    -- 评估配置
    dataset JSON NOT NULL COMMENT '测试数据集',
    metrics JSON NOT NULL COMMENT '评估指标配置',
    eval_config JSON NULL COMMENT '评估配置：并发数、超时等',
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/running/completed/failed',
    -- 统计
    total_runs INT NOT NULL DEFAULT 0,
    last_run_at DATETIME NULL,
    last_run_status VARCHAR(20) NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_eval_tenant (tenant_id),
    INDEX idx_eval_agent (agent_id),
    INDEX idx_eval_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评估任务表';

-- 评估运行记录表
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id VARCHAR(36) PRIMARY KEY,
    evaluation_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/running/completed/failed/cancelled',
    -- 执行信息
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    duration_ms INT NULL,
    -- 结果摘要
    summary JSON NULL COMMENT '评估结果摘要：各指标得分',
    avg_scores JSON NULL COMMENT '平均分数',
    -- 费用
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_er_eval (evaluation_id),
    INDEX idx_er_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评估运行记录表';

-- 评估结果详情表
CREATE TABLE IF NOT EXISTS evaluation_results (
    id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    evaluation_id VARCHAR(36) NOT NULL COMMENT '评估ID（冗余）',
    test_case_index INT NOT NULL COMMENT '测试用例序号',
    -- 输入输出
    input_text TEXT NOT NULL COMMENT '输入文本',
    expected_output TEXT NULL COMMENT '期望输出',
    actual_output TEXT NULL COMMENT '实际输出',
    -- 评分
    scores JSON NOT NULL COMMENT '各指标得分',
    overall_score FLOAT NULL COMMENT '综合得分',
    -- 性能
    latency_ms INT NULL,
    token_count INT NULL,
    -- 错误信息
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_eres_run (run_id),
    INDEX idx_eres_eval (evaluation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评估结果详情表';

-- ============================================================
-- OAuth与第三方集成
-- ============================================================

-- OAuth提供商配置表
CREATE TABLE IF NOT EXISTS oauth_providers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    provider_name VARCHAR(50) NOT NULL COMMENT 'saml/oidc/github/google/wechat/dingtalk',
    display_name VARCHAR(100) NULL COMMENT '显示名称',
    config JSON NOT NULL COMMENT '提供商配置：client_id, issuer等',
    -- 属性映射
    attribute_mapping JSON NULL COMMENT '属性映射：email, name, department等',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    -- 统计
    total_logins INT NOT NULL DEFAULT 0,
    last_login_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_oauth_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OAuth提供商配置表';

-- 第三方账号关联表
CREATE TABLE IF NOT EXISTS account_integrates (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    external_id VARCHAR(200) NOT NULL COMMENT '第三方用户ID',
    external_username VARCHAR(200) NULL COMMENT '第三方用户名',
    external_email VARCHAR(200) NULL COMMENT '第三方邮箱',
    access_token VARCHAR(500) NULL COMMENT '加密存储的访问令牌',
    refresh_token VARCHAR(500) NULL COMMENT '加密存储的刷新令牌',
    token_expires_at DATETIME NULL COMMENT '令牌过期时间',
    raw_profile JSON NULL COMMENT '原始用户信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_account_integrate (provider_id, external_id),
    INDEX idx_ai_user (user_id),
    INDEX idx_ai_provider (provider_id),
    INDEX idx_ai_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='第三方账号关联表';

-- ============================================================
-- 应用模板与市场
-- ============================================================

-- 应用模板表
CREATE TABLE IF NOT EXISTS app_templates (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NULL COMMENT 'NULL表示系统模板',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT NULL,
    category VARCHAR(50) NULL COMMENT '分类',
    config JSON NOT NULL COMMENT '模板配置',
    icon VARCHAR(500) NULL COMMENT '图标URL或Emoji',
    cover_image VARCHAR(500) NULL COMMENT '封面图URL',
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
    is_system BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否系统模板',
    -- 统计
    install_count INT NOT NULL DEFAULT 0,
    -- 版本
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_tpl_category (category),
    INDEX idx_tpl_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='应用模板表';

-- 市场应用表（旧版，保留兼容）
CREATE TABLE IF NOT EXISTS marketplace_apps (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    category VARCHAR(50) NULL,
    config JSON NULL,
    version VARCHAR(20) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'published/pending/rejected',
    install_count INT NOT NULL DEFAULT 0,
    rating FLOAT NOT NULL DEFAULT 0.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_ma_tenant (tenant_id),
    INDEX idx_ma_status (status),
    INDEX idx_ma_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场应用表';

-- 市场应用安装记录表
CREATE TABLE IF NOT EXISTS app_installations (
    id VARCHAR(36) PRIMARY KEY,
    app_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    installed_by VARCHAR(36) NOT NULL COMMENT '安装者',
    config JSON NULL COMMENT '本地覆盖配置',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/uninstalled',
    installed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uninstalled_at DATETIME NULL,
    INDEX idx_ai_app (app_id),
    INDEX idx_ai_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场应用安装记录表';

-- 市场项目表（新版）
CREATE TABLE IF NOT EXISTS marketplace_items (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL COMMENT '发布者租户',
    creator_id VARCHAR(36) NOT NULL COMMENT '发布者用户',
    asset_type VARCHAR(20) NOT NULL COMMENT 'agent/workflow/tool/knowledge_base',
    asset_id VARCHAR(36) NOT NULL COMMENT '关联的资产ID',
    title VARCHAR(200) NOT NULL COMMENT '应用名称',
    summary VARCHAR(500) NULL COMMENT '简介',
    description TEXT NULL COMMENT '详细描述',
    cover_image VARCHAR(500) NULL COMMENT '封面图',
    category VARCHAR(50) NULL COMMENT '分类',
    tags JSON NULL COMMENT '标签列表',
    visibility VARCHAR(20) NOT NULL DEFAULT 'tenant' COMMENT 'tenant/platform/public',
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/pending/approved/rejected/frozen/archived',
    reject_reason TEXT NULL,
    version INT NOT NULL DEFAULT 1,
    config_snapshot JSON NULL COMMENT '配置快照',
    -- 统计
    avg_rating FLOAT NOT NULL DEFAULT 0.0,
    rating_count INT NOT NULL DEFAULT 0,
    usage_count INT NOT NULL DEFAULT 0,
    clone_count INT NOT NULL DEFAULT 0,
    -- 推荐
    featured BOOLEAN NOT NULL DEFAULT FALSE,
    promoted_level VARCHAR(20) NULL,
    -- 审核
    frozen_at DATETIME NULL,
    frozen_reason TEXT NULL,
    published_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_mi_tenant (tenant_id),
    INDEX idx_mi_creator (creator_id),
    INDEX idx_mi_asset (asset_type, asset_id),
    INDEX idx_mi_status (status),
    INDEX idx_mi_category (category),
    INDEX idx_mi_featured (featured),
    INDEX idx_mi_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场项目表';

-- 市场审核记录表
CREATE TABLE IF NOT EXISTS marketplace_reviews (
    id VARCHAR(36) PRIMARY KEY,
    item_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    submitter_id VARCHAR(36) NOT NULL COMMENT '提交者',
    reviewer_id VARCHAR(36) NULL COMMENT '审核者',
    review_type VARCHAR(20) NOT NULL DEFAULT 'publish' COMMENT 'publish/update/appeal',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected',
    comment TEXT NULL,
    reviewed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mr_item (item_id),
    INDEX idx_mr_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场审核记录表';

-- 市场评分表
CREATE TABLE IF NOT EXISTS marketplace_ratings (
    id VARCHAR(36) PRIMARY KEY,
    item_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    score INT NOT NULL COMMENT '评分1-5',
    comment TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_marketplace_rating (item_id, user_id),
    INDEX idx_mrat_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场评分表';

-- 市场克隆记录表
CREATE TABLE IF NOT EXISTS marketplace_clones (
    id VARCHAR(36) PRIMARY KEY,
    source_item_id VARCHAR(36) NOT NULL COMMENT '源项目',
    target_tenant_id VARCHAR(36) NOT NULL COMMENT '目标租户',
    target_asset_id VARCHAR(36) NOT NULL COMMENT '克隆后的资产ID',
    cloner_id VARCHAR(36) NOT NULL COMMENT '克隆者',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mc_source (source_item_id),
    INDEX idx_mc_target (target_tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场克隆记录表';

-- ============================================================
-- 分享与文件管理
-- ============================================================

-- 分享链接表
CREATE TABLE IF NOT EXISTS share_links (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    resource_type VARCHAR(30) NOT NULL COMMENT 'agent/conversation/workflow/knowledge_base',
    resource_id VARCHAR(36) NOT NULL,
    token VARCHAR(64) NOT NULL COMMENT '分享Token',
    permissions JSON NULL COMMENT '分享权限配置',
    -- 访问控制
    password VARCHAR(200) NULL COMMENT '访问密码哈希',
    max_access_count INT NULL COMMENT '最大访问次数',
    access_count INT NOT NULL DEFAULT 0 COMMENT '已访问次数',
    allowed_ips JSON NULL COMMENT 'IP白名单',
    -- 状态
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at DATETIME NULL,
    created_by VARCHAR(36) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sl_tenant (tenant_id),
    INDEX idx_sl_token (token),
    INDEX idx_sl_resource (resource_type, resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分享链接表';

-- 文件资产表
CREATE TABLE IF NOT EXISTS file_assets (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_type VARCHAR(50) NULL COMMENT 'MIME类型',
    file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
    file_hash VARCHAR(64) NULL COMMENT '文件内容哈希',
    storage_path VARCHAR(500) NOT NULL COMMENT '存储路径',
    storage_type VARCHAR(20) NOT NULL DEFAULT 'local' COMMENT 'local/s3/oss/minio',
    -- 关联信息
    resource_type VARCHAR(30) NULL COMMENT '关联资源类型',
    resource_id VARCHAR(36) NULL COMMENT '关联资源ID',
    -- 访问控制
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    access_url VARCHAR(500) NULL COMMENT '访问URL',
    -- 审计
    uploaded_by VARCHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    INDEX idx_fa_tenant (tenant_id),
    INDEX idx_fa_hash (file_hash),
    INDEX idx_fa_resource (resource_type, resource_id),
    INDEX idx_fa_deleted (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件资产表';

-- ============================================================
-- 租户邀请
-- ============================================================

-- 租户邀请表
CREATE TABLE IF NOT EXISTS tenant_invitations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(200) NOT NULL COMMENT '受邀邮箱',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '邀请角色',
    role_id VARCHAR(36) NULL COMMENT '自定义角色ID',
    invited_by VARCHAR(36) NOT NULL COMMENT '邀请人',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/accepted/expired/revoked',
    token VARCHAR(64) NOT NULL COMMENT '邀请Token',
    expires_at DATETIME NULL,
    accepted_at DATETIME NULL,
    revoked_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ti_token (token),
    INDEX idx_ti_tenant (tenant_id),
    INDEX idx_ti_email (email),
    INDEX idx_ti_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户邀请表';

-- ============================================================
-- 通用反馈表
-- ============================================================

-- 反馈表
CREATE TABLE IF NOT EXISTS feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(50) NOT NULL COMMENT 'agent/response/tool/workflow/evaluation',
    entity_id VARCHAR(36) NOT NULL,
    rating VARCHAR(10) NOT NULL COMMENT 'positive/negative',
    comment TEXT NULL,
    tags JSON NULL COMMENT '反馈标签',
    metadata JSON NULL COMMENT '扩展元数据',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fb_tenant (tenant_id),
    INDEX idx_fb_entity (entity_type, entity_id),
    INDEX idx_fb_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用反馈表';

-- ============================================================
-- 链路追踪表（可选，支持分布式追踪）
-- ============================================================

-- 追踪记录表
CREATE TABLE IF NOT EXISTS trace_spans (
    id VARCHAR(36) PRIMARY KEY,
    trace_id VARCHAR(36) NOT NULL COMMENT '链路ID',
    parent_span_id VARCHAR(36) NULL COMMENT '父SpanID',
    span_type VARCHAR(30) NOT NULL COMMENT 'agent_call/llm_call/tool_call/workflow_step/retrieval',
    name VARCHAR(200) NOT NULL COMMENT 'Span名称',
    tenant_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    agent_id VARCHAR(36) NULL,
    conversation_id VARCHAR(36) NULL,
    -- 时间信息
    started_at DATETIME(3) NOT NULL COMMENT '开始时间(毫秒精度)',
    finished_at DATETIME(3) NULL,
    duration_ms INT NULL,
    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'ok' COMMENT 'ok/error/cancelled',
    error_message TEXT NULL,
    -- 详情
    input JSON NULL COMMENT '输入数据',
    output JSON NULL COMMENT '输出数据',
    attributes JSON NULL COMMENT '自定义属性',
    -- 费用
    tokens INT NULL,
    cost DECIMAL(10,6) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ts_trace (trace_id),
    INDEX idx_ts_parent (parent_span_id),
    INDEX idx_ts_tenant (tenant_id),
    INDEX idx_ts_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='链路追踪表';

-- ============================================================
-- 种子数据
-- ============================================================

-- 默认租户
INSERT IGNORE INTO tenants (id, name, code, status, max_agents, max_users, max_storage_gb, features, subscription_plan)
VALUES ('default', '默认租户', 'default', 'active', 100, 1000, 100,
    '{"graph_rag": true, "multi_agent": true, "evaluation": true, "marketplace": true, "workflow": true, "webhook": true}',
    'enterprise');

-- 管理员用户
INSERT IGNORE INTO users (id, tenant_id, username, email, hashed_password, role, status, nickname)
VALUES ('admin-user', 'default', 'admin', 'admin@example.com',
    '$2b$12$LJ3m4ys3Lz0YBGQxKvGqeOBUOzHMHHMFGCoN7G7F8J3YlQ3Yq5K2e', 'admin', 'active', '系统管理员');

-- 系统角色
INSERT IGNORE INTO roles (id, tenant_id, name, code, description, is_system, is_default, priority, data_scope) VALUES
    ('role-owner', 'default', '所有者', 'owner', '租户所有者，拥有全部权限', TRUE, FALSE, 100, 'all'),
    ('role-admin', 'default', '管理员', 'admin', '系统管理员', TRUE, FALSE, 90, 'all'),
    ('role-editor', 'default', '编辑者', 'editor', '可创建和编辑资源', TRUE, TRUE, 50, 'dept_and_children'),
    ('role-viewer', 'default', '查看者', 'viewer', '只读访问', TRUE, FALSE, 10, 'self');

-- 权限定义
INSERT IGNORE INTO permissions (id, module, resource, action, name, description) VALUES
    -- Agent权限
    ('perm-agent-c', 'agent', 'agent', 'create', 'agent:create', '创建Agent'),
    ('perm-agent-r', 'agent', 'agent', 'read', 'agent:read', '查看Agent'),
    ('perm-agent-u', 'agent', 'agent', 'update', 'agent:update', '编辑Agent'),
    ('perm-agent-d', 'agent', 'agent', 'delete', 'agent:delete', '删除Agent'),
    ('perm-agent-p', 'agent', 'agent', 'publish', 'agent:publish', '发布Agent'),
    ('perm-agent-e', 'agent', 'agent', 'execute', 'agent:execute', '执行Agent'),
    -- 知识库权限
    ('perm-kb-c', 'knowledge', 'knowledge_base', 'create', 'knowledge_base:create', '创建知识库'),
    ('perm-kb-r', 'knowledge', 'knowledge_base', 'read', 'knowledge_base:read', '查看知识库'),
    ('perm-kb-u', 'knowledge', 'knowledge_base', 'update', 'knowledge_base:update', '编辑知识库'),
    ('perm-kb-d', 'knowledge', 'knowledge_base', 'delete', 'knowledge_base:delete', '删除知识库'),
    ('perm-kb-e', 'knowledge', 'knowledge_base', 'export', 'knowledge_base:export', '导出知识库'),
    -- 工作流权限
    ('perm-wf-c', 'workflow', 'workflow', 'create', 'workflow:create', '创建工作流'),
    ('perm-wf-r', 'workflow', 'workflow', 'read', 'workflow:read', '查看工作流'),
    ('perm-wf-u', 'workflow', 'workflow', 'update', 'workflow:update', '编辑工作流'),
    ('perm-wf-d', 'workflow', 'workflow', 'delete', 'workflow:delete', '删除工作流'),
    ('perm-wf-e', 'workflow', 'workflow', 'execute', 'workflow:execute', '执行工作流'),
    ('perm-wf-p', 'workflow', 'workflow', 'publish', 'workflow:publish', '发布工作流'),
    -- 工具权限
    ('perm-tool-c', 'tool', 'tool', 'create', 'tool:create', '创建工具'),
    ('perm-tool-r', 'tool', 'tool', 'read', 'tool:read', '查看工具'),
    ('perm-tool-u', 'tool', 'tool', 'update', 'tool:update', '编辑工具'),
    ('perm-tool-d', 'tool', 'tool', 'delete', 'tool:delete', '删除工具'),
    ('perm-tool-e', 'tool', 'tool', 'execute', 'tool:execute', '执行工具'),
    -- 模型权限
    ('perm-model-c', 'model', 'model', 'create', 'model:create', '配置模型'),
    ('perm-model-r', 'model', 'model', 'read', 'model:read', '查看模型配置'),
    ('perm-model-u', 'model', 'model', 'update', 'model:update', '编辑模型配置'),
    ('perm-model-d', 'model', 'model', 'delete', 'model:delete', '删除模型配置'),
    -- 用户权限
    ('perm-user-c', 'user', 'user', 'create', 'user:create', '创建用户'),
    ('perm-user-r', 'user', 'user', 'read', 'user:read', '查看用户'),
    ('perm-user-u', 'user', 'user', 'update', 'user:update', '编辑用户'),
    ('perm-user-d', 'user', 'user', 'delete', 'user:delete', '删除用户'),
    -- 会话权限
    ('perm-conv-c', 'conversation', 'conversation', 'create', 'conversation:create', '创建会话'),
    ('perm-conv-r', 'conversation', 'conversation', 'read', 'conversation:read', '查看会话'),
    ('perm-conv-d', 'conversation', 'conversation', 'delete', 'conversation:delete', '删除会话'),
    ('perm-conv-e', 'conversation', 'conversation', 'export', 'conversation:export', '导出会话'),
    -- 租户权限
    ('perm-tenant-r', 'tenant', 'tenant', 'read', 'tenant:read', '查看租户信息'),
    ('perm-tenant-u', 'tenant', 'tenant', 'update', 'tenant:update', '编辑租户设置'),
    -- 审计权限
    ('perm-audit-r', 'system', 'audit', 'read', 'audit:read', '查看审计日志'),
    ('perm-audit-e', 'system', 'audit', 'export', 'audit:export', '导出审计日志'),
    -- 市场权限
    ('perm-market-c', 'marketplace', 'marketplace', 'create', 'marketplace:create', '发布到市场'),
    ('perm-market-r', 'marketplace', 'marketplace', 'read', 'marketplace:read', '浏览市场'),
    ('perm-market-u', 'marketplace', 'marketplace', 'update', 'marketplace:update', '更新市场应用'),
    ('perm-market-d', 'marketplace', 'marketplace', 'delete', 'marketplace:delete', '下架市场应用');

-- 角色权限映射：Owner获得所有权限
INSERT IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT CONCAT('rp-owner-', p.id), 'role-owner', p.id FROM permissions p;

-- Admin：除租户管理外的所有权限
INSERT IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT CONCAT('rp-admin-', p.id), 'role-admin', p.id
FROM permissions p WHERE p.module != 'tenant';

-- Editor：创建/读取/更新/执行权限
INSERT IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT CONCAT('rp-editor-', p.id), 'role-editor', p.id
FROM permissions p WHERE p.action IN ('create', 'read', 'update', 'execute');

-- Viewer：只读权限
INSERT IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT CONCAT('rp-viewer-', p.id), 'role-viewer', p.id
FROM permissions p WHERE p.action = 'read';

-- 默认部门
INSERT IGNORE INTO departments (id, tenant_id, name, code, level, path, sort_order)
VALUES ('dept-default', 'default', '默认部门', 'DEFAULT', 1, '/default', 0);

-- 默认模型提供商
INSERT IGNORE INTO model_providers (id, tenant_id, name, provider_type, api_base, status)
VALUES
    ('provider-openai', 'default', 'OpenAI', 'openai', 'https://api.openai.com/v1', 'active'),
    ('provider-anthropic', 'default', 'Anthropic', 'anthropic', 'https://api.anthropic.com', 'active'),
    ('provider-deepseek', 'default', 'DeepSeek', 'custom_openai', 'https://api.deepseek.com/v1', 'active');

-- 默认模型配置
INSERT IGNORE INTO model_configs (id, tenant_id, provider_id, model_name, model_type, display_name, config, is_default, enabled, max_context_tokens, max_output_tokens, supports_streaming, supports_function_calling, input_price_per_1k, output_price_per_1k)
VALUES
    ('config-gpt4o', 'default', 'provider-openai', 'gpt-4o', 'llm', 'GPT-4o', '{"temperature": 0.7, "max_tokens": 4096}', TRUE, TRUE, 128000, 4096, TRUE, TRUE, 0.002500, 0.010000),
    ('config-gpt4o-mini', 'default', 'provider-openai', 'gpt-4o-mini', 'llm', 'GPT-4o Mini', '{"temperature": 0.7, "max_tokens": 4096}', FALSE, TRUE, 128000, 4096, TRUE, TRUE, 0.000150, 0.000600),
    ('config-embedding-3-large', 'default', 'provider-openai', 'text-embedding-3-large', 'embedding', 'Text Embedding 3 Large', '{"dimensions": 1536}', TRUE, TRUE, NULL, NULL, FALSE, FALSE, 0.000130, NULL),
    ('config-claude-sonnet', 'default', 'provider-anthropic', 'claude-sonnet-4-20250514', 'llm', 'Claude Sonnet 4', '{"temperature": 0.7, "max_tokens": 4096}', FALSE, TRUE, 200000, 4096, TRUE, TRUE, 0.003000, 0.015000),
    ('config-deepseek-chat', 'default', 'provider-deepseek', 'deepseek-chat', 'llm', 'DeepSeek Chat', '{"temperature": 0.7, "max_tokens": 4096}', FALSE, TRUE, 64000, 4096, TRUE, TRUE, 0.000140, 0.000280);

-- 内置工具
INSERT IGNORE INTO tools (id, tenant_id, name, description, tool_type, api_schema, config, enabled)
VALUES
    ('tool-web-search', 'default', 'Web Search', '使用DuckDuckGo或SearXNG搜索网络', 'builtin',
     '{"type":"object","properties":{"query":{"type":"string","description":"搜索查询"}},"required":["query"]}',
     '{"engine": "duckduckgo", "max_results": 5}', TRUE),
    ('tool-calculator', 'default', 'Calculator', '安全计算数学表达式', 'builtin',
     '{"type":"object","properties":{"expression":{"type":"string","description":"数学表达式"}},"required":["expression"]}',
     '{}', TRUE),
    ('tool-http-request', 'default', 'HTTP Request', '发送HTTP请求（SSRF安全）', 'builtin',
     '{"type":"object","properties":{"url":{"type":"string"},"method":{"type":"string","enum":["GET","POST","PUT","DELETE"]},"headers":{"type":"object"},"body":{"type":"string"}},"required":["url","method"]}',
     '{"timeout": 30, "max_redirects": 3}', TRUE),
    ('tool-code-executor', 'default', 'Code Executor', '在沙箱中执行Python代码', 'builtin',
     '{"type":"object","properties":{"code":{"type":"string","description":"Python代码"},"timeout":{"type":"integer","default":30}},"required":["code"]}',
     '{"sandbox": "docker", "memory_limit": "256m"}', TRUE),
    ('tool-db-query', 'default', 'Database Query', '执行只读数据库查询', 'builtin',
     '{"type":"object","properties":{"sql":{"type":"string","description":"SQL查询（仅SELECT）"}},"required":["sql"]}',
     '{"readonly": true, "max_rows": 100}', TRUE),
    ('tool-file-ops', 'default', 'File Operations', '在受限目录中读写文件', 'builtin',
     '{"type":"object","properties":{"path":{"type":"string"},"operation":{"type":"string","enum":["read","write","list"]},"content":{"type":"string"}},"required":["path","operation"]}',
     '{"base_dir": "/app/workspace", "max_file_size": 10485760}', TRUE);

-- 应用模板
INSERT IGNORE INTO app_templates (id, tenant_id, name, description, category, config, icon, is_system, status, version)
VALUES
    ('tpl-customer-service', NULL, '客服机器人', '基于知识库的AI客服', '客户服务',
     '{"system_prompt": "你是一名专业的客服代表。基于知识库回答问题。保持礼貌和专业。", "tools": ["tool-web-search"], "safety_config": {"pii_detection": true, "content_moderation": true}}',
     '🤖', TRUE, 'active', '1.0.0'),
    ('tpl-knowledge-assistant', NULL, '知识助手', '通用知识问答助手', '助手',
     '{"system_prompt": "你是一名知识渊博的助手。使用提供的知识库准确回答问题。如果不确定，请说明。", "safety_config": {"pii_detection": true}}',
     '📚', TRUE, 'active', '1.0.0'),
    ('tpl-education-tutor', NULL, '教育导师', '互动式教学助手', '教育',
     '{"system_prompt": "你是一名耐心的导师。通过引导性问题帮助学生理解概念。使用例子和类比。", "tools": ["tool-calculator", "tool-web-search"]}',
     '🎓', TRUE, 'active', '1.0.0'),
    ('tpl-code-assistant', NULL, '代码助手', '编程帮助和代码审查', '开发',
     '{"system_prompt": "你是一名编程专家。帮助解答代码问题，审查代码并建议改进。支持多种语言。", "tools": ["tool-code-executor", "tool-web-search"]}',
     '💻', TRUE, 'active', '1.0.0');

-- ================================================================
-- 表结构变更说明
-- ================================================================
-- v2.0.0 变更摘要：
-- 1. 新增表：user_roles, user_sessions, tenant_usage_monthly, trace_spans, marketplace_items, marketplace_reviews, marketplace_ratings, marketplace_clones
-- 2. 所有表添加 deleted_at 软删除字段
-- 3. 所有配置表添加 created_by 审计字段
-- 4. 所有配置表添加 version_lock 乐观锁字段
-- 5. tenants 表增加 parent_id, org_level, org_path, max_users, max_storage_gb, settings, subscription_plan, subscription_expires_at, billing_email, contact_name, contact_phone, timezone, locale
-- 6. users 表增加 phone, salt, nickname, avatar_url, position, last_login_at, last_login_ip, login_count, password_changed_at, email_verified_at, phone_verified_at, settings
-- 7. conversations 表增加 agent_name, summary, model_provider, model_name, is_pinned, message_count, total_input_tokens, total_output_tokens, total_cost, last_message_at, last_message_preview, archived_at
-- 8. messages 表增加 tenant_id, input_tokens, output_tokens, total_tokens, model_provider, model_name, tool_calls, tool_call_id, name, latency_ms, first_token_ms, citation_sources, feedback_score
-- 9. knowledge_bases 表增加 icon_url, retrieval_top_k, score_threshold, rerank_enabled, rerank_model, segment_count, total_tokens, last_synced_at
-- 10. documents 表增加 file_hash, title, author, language, page_count, token_count, processed_at, vector_indexed, es_indexed, graph_indexed
-- 11. agents 表增加 icon_url, category, user_prompt_template, total_conversations, total_messages, avg_rating, last_used_at, version_lock
-- 12. workflows 表增加 icon_url, category, max_iterations, retry_policy, visibility, total_executions, success_count, failure_count, avg_duration_ms, last_executed_at, version_lock
-- 13. usage_logs 表增加 agent_id, conversation_id, message_id, cached_tokens, trace_id, parent_trace_id
-- 14. model_providers 表增加 api_version, last_health_check_at, health_status, health_error_message, total_requests, total_tokens, total_cost
-- 15. model_configs 表增加 max_context_tokens, max_output_tokens, supports_streaming, supports_function_calling, supports_vision, input_price_per_1k, output_price_per_1k
-- 16. 所有金额字段从 DOUBLE 改为 DECIMAL 以保证精度
-- 17. 文件大小字段从 INT 改为 BIGINT 以支持大文件
-- 18. 所有表添加适当的索引以优化查询性能

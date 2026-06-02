#!/usr/bin/env python3
"""Create missing tables directly via pymysql."""
import pymysql

conn = pymysql.connect(
    host='172.16.91.134', port=13306,
    user='root', password='yunqu168',
    database='agent_engine', charset='utf8mb4'
)
cur = conn.cursor()

statements = [
    """
    CREATE TABLE IF NOT EXISTS publish_channels (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL,
        agent_id VARCHAR(36) NOT NULL,
        type VARCHAR(20) NOT NULL,
        name VARCHAR(100) NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        config JSON DEFAULT NULL,
        api_key_prefix VARCHAR(10) DEFAULT NULL,
        total_calls INT DEFAULT 0,
        calls_today INT DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL,
        created_by VARCHAR(36) DEFAULT NULL,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_publish_channels_tenant_id (tenant_id),
        INDEX idx_publish_channels_agent_id (agent_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS plugins (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT DEFAULT '',
        version VARCHAR(20) NOT NULL,
        author VARCHAR(100) DEFAULT '',
        category VARCHAR(50) DEFAULT 'general',
        tags JSON DEFAULT NULL,
        icon VARCHAR(500) DEFAULT NULL,
        homepage VARCHAR(500) DEFAULT NULL,
        repository VARCHAR(500) DEFAULT NULL,
        config_schema JSON DEFAULT NULL,
        entry_point VARCHAR(200) NOT NULL,
        dependencies JSON DEFAULT NULL,
        permissions JSON DEFAULT NULL,
        downloads INT DEFAULT 0,
        rating FLOAT DEFAULT 0.0,
        rating_count INT DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        tenant_id VARCHAR(36) NOT NULL,
        created_by VARCHAR(36) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_plugins_name (name),
        INDEX idx_plugins_category (category),
        INDEX idx_plugins_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS plugin_installs (
        id VARCHAR(36) PRIMARY KEY,
        plugin_id VARCHAR(36) NOT NULL,
        tenant_id VARCHAR(36) NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        config JSON DEFAULT NULL,
        installed_by VARCHAR(36) NOT NULL,
        installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_plugin_installs_plugin_id (plugin_id),
        INDEX idx_plugin_installs_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS plugin_ratings (
        id VARCHAR(36) PRIMARY KEY,
        plugin_id VARCHAR(36) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        score INT NOT NULL,
        comment TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_plugin_ratings_plugin_id (plugin_id),
        INDEX idx_plugin_ratings_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS compliance_reports (
        id VARCHAR(36) PRIMARY KEY,
        report_type VARCHAR(50) NOT NULL,
        period_start DATETIME NOT NULL,
        period_end DATETIME NOT NULL,
        summary JSON NOT NULL,
        details JSON DEFAULT NULL,
        format VARCHAR(20) DEFAULT 'json',
        tenant_id VARCHAR(36) NOT NULL,
        created_by VARCHAR(36) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_compliance_reports_report_type (report_type),
        INDEX idx_compliance_reports_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ab_tests (
        id VARCHAR(36) PRIMARY KEY,
        agent_id VARCHAR(36) NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT DEFAULT NULL,
        version_a_id VARCHAR(36) NOT NULL,
        version_b_id VARCHAR(36) NOT NULL,
        traffic_split FLOAT DEFAULT 0.5,
        metric VARCHAR(50) DEFAULT 'satisfaction',
        duration_hours INT DEFAULT 24,
        min_samples INT DEFAULT 100,
        status VARCHAR(20) DEFAULT 'created',
        started_at DATETIME DEFAULT NULL,
        ended_at DATETIME DEFAULT NULL,
        results JSON DEFAULT NULL,
        tenant_id VARCHAR(36) NOT NULL,
        created_by VARCHAR(36) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_ab_tests_agent_id (agent_id),
        INDEX idx_ab_tests_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS marketplace_change_logs (
        id VARCHAR(36) PRIMARY KEY,
        item_id VARCHAR(36) NOT NULL,
        version VARCHAR(50) NOT NULL,
        change_type VARCHAR(20) NOT NULL,
        changes JSON NOT NULL,
        created_by VARCHAR(36) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version INT DEFAULT 1,
        version_lock INT NOT NULL DEFAULT 1,
        INDEX idx_marketplace_change_logs_item_id (item_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]

for sql in statements:
    try:
        cur.execute(sql)
        conn.commit()
        table = sql.split('TABLE IF NOT EXISTS')[1].split('(')[0].strip()
        print(f"OK: {table}")
    except Exception as e:
        conn.rollback()
        table = sql.split('TABLE IF NOT EXISTS')[1].split('(')[0].strip()
        print(f"FAIL: {table} - {e}")

cur.close()
conn.close()
print("Done")

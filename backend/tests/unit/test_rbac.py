"""Unit tests for RBAC permission system."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.core.rbac import (
    PERMISSIONS,
    DEFAULT_ROLES,
    check_permission,
    get_user_permissions,
    invalidate_user_permissions,
    require_permission,
    init_default_roles,
)


# ---------------------------------------------------------------------------
# PERMISSIONS dict completeness
# ---------------------------------------------------------------------------

class TestPermissionsDict:
    def test_permissions_is_non_empty(self):
        assert len(PERMISSIONS) > 0

    def test_all_resources_have_actions(self):
        for resource, actions in PERMISSIONS.items():
            assert isinstance(actions, list)
            assert len(actions) > 0
            for action in actions:
                assert isinstance(action, str)
                assert len(action) > 0

    def test_expected_resources_exist(self):
        expected = {"agent", "knowledge", "workflow", "tool", "conversation",
                    "user", "tenant", "audit", "api_token", "webhook", "role"}
        assert expected == set(PERMISSIONS.keys())

    def test_agent_actions(self):
        assert set(PERMISSIONS["agent"]) == {"create", "read", "update", "delete", "publish"}

    def test_knowledge_actions(self):
        assert set(PERMISSIONS["knowledge"]) == {"create", "read", "update", "delete", "upload"}

    def test_workflow_actions(self):
        assert set(PERMISSIONS["workflow"]) == {"create", "read", "update", "delete", "execute"}

    def test_tool_actions(self):
        assert set(PERMISSIONS["tool"]) == {"create", "read", "update", "delete", "execute"}

    def test_conversation_actions(self):
        assert set(PERMISSIONS["conversation"]) == {"create", "read", "delete"}

    def test_tenant_actions(self):
        assert set(PERMISSIONS["tenant"]) == {"read", "update", "manage_features", "manage_quota"}

    def test_all_permissions_are_resource_action_format(self):
        """Every permission string in default roles should be 'resource:action'."""
        for role_name, role_def in DEFAULT_ROLES.items():
            for perm_str in role_def["permissions"]:
                assert ":" in perm_str, f"{role_name} has malformed permission: {perm_str}"
                resource, action = perm_str.split(":", 1)
                assert resource in PERMISSIONS, f"{role_name}: unknown resource '{resource}'"
                assert action in PERMISSIONS[resource], (
                    f"{role_name}: unknown action '{action}' for resource '{resource}'"
                )


# ---------------------------------------------------------------------------
# Default roles
# ---------------------------------------------------------------------------

class TestDefaultRoles:
    def test_four_default_roles(self):
        assert len(DEFAULT_ROLES) == 4

    def test_expected_role_names(self):
        names = set(DEFAULT_ROLES.keys())
        assert names == {"Owner", "Admin", "Contributor", "Viewer"}

    def test_owner_has_all_permissions(self):
        owner_perms = set(DEFAULT_ROLES["Owner"]["permissions"])
        all_perms = {
            f"{res}:{act}"
            for res, actions in PERMISSIONS.items()
            for act in actions
        }
        assert owner_perms == all_perms

    def test_admin_has_all_except_tenant(self):
        admin_perms = set(DEFAULT_ROLES["Admin"]["permissions"])
        tenant_perms = {f"tenant:{a}" for a in PERMISSIONS["tenant"]}
        assert tenant_perms.isdisjoint(admin_perms)
        # Admin should have everything else
        non_tenant = {
            f"{res}:{act}"
            for res, actions in PERMISSIONS.items()
            if res != "tenant"
            for act in actions
        }
        assert admin_perms == non_tenant

    def test_contributor_has_expected_permissions(self):
        contrib = set(DEFAULT_ROLES["Contributor"]["permissions"])
        # Should include create/read/update on main resources
        assert "agent:create" in contrib
        assert "agent:read" in contrib
        assert "agent:update" in contrib
        # Should NOT include delete or publish
        assert "agent:delete" not in contrib
        assert "agent:publish" not in contrib
        # Should NOT include user management
        assert "user:create" not in contrib
        assert "user:delete" not in contrib

    def test_viewer_is_read_only(self):
        viewer = set(DEFAULT_ROLES["Viewer"]["permissions"])
        for perm_str in viewer:
            _, action = perm_str.split(":", 1)
            assert action == "read", f"Viewer has non-read permission: {perm_str}"

    def test_all_roles_have_system_flag(self):
        for role_def in DEFAULT_ROLES.values():
            assert role_def["is_system"] is True

    def test_all_roles_have_description(self):
        for role_def in DEFAULT_ROLES.values():
            assert len(role_def["description"]) > 0


# ---------------------------------------------------------------------------
# check_permission
# ---------------------------------------------------------------------------

class TestCheckPermission:
    @pytest.mark.asyncio
    async def test_check_permission_owner_has_all(self):
        mock_db = AsyncMock()
        with patch("app.core.rbac.get_user_permissions", return_value={
            "agent:create", "agent:read", "agent:delete",
            "tenant:manage_features",
        }):
            result = await check_permission("u1", "t1", "agent", "create", mock_db)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_denied(self):
        mock_db = AsyncMock()
        with patch("app.core.rbac.get_user_permissions", return_value={"agent:read"}):
            result = await check_permission("u1", "t1", "agent", "delete", mock_db)
            assert result is False

    @pytest.mark.asyncio
    async def test_check_permission_empty_set(self):
        mock_db = AsyncMock()
        with patch("app.core.rbac.get_user_permissions", return_value=set()):
            result = await check_permission("u1", "t1", "agent", "read", mock_db)
            assert result is False


# ---------------------------------------------------------------------------
# get_user_permissions
# ---------------------------------------------------------------------------

class TestGetUserPermissions:
    @pytest.mark.asyncio
    async def test_admin_user_gets_all_permissions(self):
        """User with role='admin' and no RBAC role gets all permissions as fallback."""
        mock_db = AsyncMock()

        # Mock UserModel lookup
        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        # Mock RoleModel lookup (returns None — no RBAC role)
        mock_result_role = MagicMock()
        mock_result_role.scalar_one_or_none.return_value = None

        execute_results = [mock_result_user, mock_result_role]
        mock_db.execute = AsyncMock(side_effect=execute_results)

        perms = await get_user_permissions("u1", "t1", mock_db)
        # Admin fallback should return all permissions
        assert "agent:create" in perms
        assert "tenant:manage_features" in perms
        assert len(perms) > 0

    @pytest.mark.asyncio
    async def test_unknown_user_returns_empty(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        perms = await get_user_permissions("unknown", "t1", mock_db)
        assert perms == set()

    @pytest.mark.asyncio
    async def test_non_admin_no_rbac_role_returns_empty(self):
        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.role = "viewer"
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_result_role = MagicMock()
        mock_result_role.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(side_effect=[mock_result_user, mock_result_role])

        perms = await get_user_permissions("u1", "t1", mock_db)
        assert perms == set()


# ---------------------------------------------------------------------------
# require_permission dependency
# ---------------------------------------------------------------------------

class TestRequirePermission:
    def test_require_permission_returns_callable(self):
        dep = require_permission("agent", "create")
        assert callable(dep)

    def test_require_permission_different_resources(self):
        for resource, actions in PERMISSIONS.items():
            for action in actions:
                dep = require_permission(resource, action)
                assert callable(dep)


# ---------------------------------------------------------------------------
# Redis caching layer
# ---------------------------------------------------------------------------

class TestRedisCache:
    """Tests for the RBAC Redis caching behaviour."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_perms(self):
        """When Redis has a cached value, it is returned without DB access."""
        mock_db = AsyncMock()
        cached_perms = ["agent:read", "agent:create"]

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_perms))

        with patch("app.core.redis.get_redis", return_value=mock_redis):
            perms = await get_user_permissions("u1", "t1", mock_db)

        assert perms == {"agent:read", "agent:create"}
        # DB should NOT have been queried
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_queries_db_and_populates(self):
        """On cache miss, DB is queried and the result is written to Redis."""
        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_result_role = MagicMock()
        mock_result_role.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(
            side_effect=[mock_result_user, mock_result_role]
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # cache miss
        mock_redis.set = AsyncMock()

        with patch("app.core.redis.get_redis", return_value=mock_redis):
            perms = await get_user_permissions("u1", "t1", mock_db)

        # DB was queried
        assert mock_db.execute.call_count == 2
        # Permissions returned correctly
        assert "agent:create" in perms
        # Redis.set was called to populate the cache
        mock_redis.set.assert_awaited_once()
        args, kwargs = mock_redis.set.call_args
        assert args[0] == "rbac:perms:t1:u1"
        assert kwargs.get("ex") == 300 or (len(args) > 2 and args[2] == 300)

    @pytest.mark.asyncio
    async def test_redis_down_falls_back_to_db(self):
        """If Redis raises an exception, the function still returns DB results."""
        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_result_role = MagicMock()
        mock_result_role.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(
            side_effect=[mock_result_user, mock_result_role]
        )

        # Redis raises on both get and set
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis.set = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.redis.get_redis", return_value=mock_redis):
            perms = await get_user_permissions("u1", "t1", mock_db)

        # Still got the correct result from DB
        assert "agent:create" in perms
        assert "tenant:manage_features" in perms

    @pytest.mark.asyncio
    async def test_invalidate_deletes_cache_key(self):
        """invalidate_user_permissions deletes the correct Redis key."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.core.redis.get_redis", return_value=mock_redis):
            await invalidate_user_permissions("u1", "t1")

        mock_redis.delete.assert_awaited_once_with("rbac:perms:t1:u1")

    @pytest.mark.asyncio
    async def test_invalidate_handles_redis_failure(self):
        """invalidate_user_permissions does not raise when Redis is down."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.redis.get_redis", return_value=mock_redis):
            # Should not raise
            await invalidate_user_permissions("u1", "t1")

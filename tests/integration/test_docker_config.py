"""Docker Compose configuration validation tests.

These tests verify configuration correctness without requiring a Docker daemon.
Covers: D-001 (compose validity), D-002 (required env vars), D-005 (volumes).
"""

import re

import pytest
import yaml


# ---------------------------------------------------------------------------
# D-001: docker-compose.yml is valid YAML and has all expected services
# ---------------------------------------------------------------------------

class TestDockerComposeValidity:
    """D-001: Validate docker-compose.yml structure and services."""

    EXPECTED_SERVICES = {
        "mysql",
        "redis",
        "milvus-standalone",
        "neo4j",
        "elasticsearch",
        "minio",
        "rabbitmq",
        "backend",
        "celery-worker",
        "celery-beat",
        "frontend",
        "nginx",
    }

    def test_is_valid_yaml(self, docker_compose: dict):
        """docker-compose.yml must parse without errors."""
        assert isinstance(docker_compose, dict), "Top-level must be a mapping"

    def test_has_services_key(self, docker_compose: dict):
        """Top-level 'services' key must exist."""
        assert "services" in docker_compose, "Missing 'services' key"

    def test_all_expected_services_present(self, docker_compose: dict):
        """Every expected service must be declared."""
        actual = set(docker_compose["services"].keys())
        missing = self.EXPECTED_SERVICES - actual
        assert not missing, f"Missing services: {missing}"

    def test_no_unexpected_services(self, docker_compose: dict):
        """No undeclared services should exist."""
        actual = set(docker_compose["services"].keys())
        extra = actual - self.EXPECTED_SERVICES
        assert not extra, f"Unexpected services: {extra}"

    def test_version_declared(self, docker_compose: dict):
        """Compose file version should be declared."""
        assert "version" in docker_compose, "Missing 'version' key"


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

class TestHealthChecks:
    """Every data-store / infrastructure service must have a healthcheck."""

    # Services that MUST have healthchecks (infrastructure services)
    SERVICES_REQUIRING_HEALTHCHECK = {
        "mysql",
        "redis",
        "milvus-standalone",
        "neo4j",
        "elasticsearch",
        "rabbitmq",
    }

    def test_infrastructure_services_have_healthchecks(self, docker_compose: dict):
        """All infrastructure services must define a healthcheck."""
        services = docker_compose["services"]
        missing = []
        for svc_name in self.SERVICES_REQUIRING_HEALTHCHECK:
            svc = services.get(svc_name, {})
            if "healthcheck" not in svc:
                missing.append(svc_name)
        assert not missing, f"Services missing healthcheck: {missing}"

    def test_healthchecks_have_required_fields(self, docker_compose: dict):
        """Each healthcheck must have at least 'test'."""
        services = docker_compose["services"]
        for svc_name in self.SERVICES_REQUIRING_HEALTHCHECK:
            svc = services.get(svc_name, {})
            hc = svc.get("healthcheck", {})
            assert "test" in hc, f"{svc_name}: healthcheck missing 'test'"


# ---------------------------------------------------------------------------
# D-002: Environment variables use ${VAR:?ERROR} pattern
# ---------------------------------------------------------------------------

class TestRequiredEnvVars:
    """D-002: Sensitive / required env vars must use the ${VAR:?} pattern."""

    # These variables must be set by the operator (no safe default).
    REQUIRED_VARS = {
        "MYSQL_ROOT_PASSWORD",
        "NEO4J_PASSWORD",
        "MINIO_SECRET_KEY",
    }

    def _extract_env_values(self, docker_compose: dict) -> dict[str, list[str]]:
        """Return {service_name: [raw_env_value_strings]}."""
        result: dict[str, list[str]] = {}
        for svc_name, svc in docker_compose["services"].items():
            env = svc.get("environment")
            if env is None:
                continue
            values: list[str] = []
            if isinstance(env, dict):
                values.extend(str(v) for v in env.values())
            elif isinstance(env, list):
                values.extend(str(v) for v in env)
            if values:
                result[svc_name] = values
        return result

    def test_required_vars_use_error_pattern(self, docker_compose: dict):
        """Required vars must use ${VAR:?error message} so compose fails when unset."""
        env_map = self._extract_env_values(docker_compose)
        for var in self.REQUIRED_VARS:
            found = False
            for svc_name, values in env_map.items():
                for v in values:
                    # Match ${VAR:?...} anywhere in the value
                    pattern = rf"\$\{{\s*{re.escape(var)}\s*:\?.*?\}}"
                    if re.search(pattern, v):
                        found = True
                        break
                if found:
                    break
            assert found, (
                f"Required variable '{var}' does not use ${{VAR:?ERROR}} pattern "
                f"in any service"
            )


# ---------------------------------------------------------------------------
# D-005: Volume mounts for data persistence
# ---------------------------------------------------------------------------

class TestVolumePersistence:
    """D-005: Data-storing services must declare named volumes."""

    # Services that persist data and must mount a named volume.
    DATA_SERVICES = {
        "mysql",
        "redis",
        "milvus-standalone",
        "neo4j",
        "elasticsearch",
        "minio",
        "rabbitmq",
    }

    def test_data_services_declare_volumes(self, docker_compose: dict):
        """Each data service must have at least one volume mount."""
        services = docker_compose["services"]
        missing = []
        for svc_name in self.DATA_SERVICES:
            svc = services.get(svc_name, {})
            volumes = svc.get("volumes", [])
            if not volumes:
                missing.append(svc_name)
        assert not missing, f"Data services without volumes: {missing}"

    def test_named_volumes_declared_at_top_level(self, docker_compose: dict):
        """Top-level 'volumes' key must exist with expected named volumes."""
        assert "volumes" in docker_compose, "Missing top-level 'volumes' key"
        declared = set(docker_compose["volumes"].keys())
        expected = {
            "mysql_data",
            "redis_data",
            "milvus_data",
            "neo4j_data",
            "es_data",
            "minio_data",
            "rabbitmq_data",
            "upload_data",
        }
        missing = expected - declared
        assert not missing, f"Named volumes not declared: {missing}"

    def test_backend_has_upload_volume(self, docker_compose: dict):
        """Backend service must mount upload_data for file persistence."""
        backend = docker_compose["services"]["backend"]
        volumes = backend.get("volumes", [])
        upload_mounts = [v for v in volumes if "upload_data" in str(v)]
        assert upload_mounts, "Backend must mount upload_data volume"


# ---------------------------------------------------------------------------
# nginx.conf validation
# ---------------------------------------------------------------------------

class TestNginxConfig:
    """Validate nginx.conf has correct upstream and proxy_pass setup."""

    def test_backend_upstream_defined(self, nginx_conf: str):
        """upstream backend must point to backend:8000."""
        assert re.search(
            r"upstream\s+backend\s*\{[^}]*server\s+backend:8000",
            nginx_conf,
        ), "Missing or incorrect 'upstream backend'"

    def test_frontend_upstream_defined(self, nginx_conf: str):
        """upstream frontend must point to frontend:3000."""
        assert re.search(
            r"upstream\s+frontend\s*\{[^}]*server\s+frontend:3000",
            nginx_conf,
        ), "Missing or incorrect 'upstream frontend'"

    def test_api_proxy_pass_to_backend(self, nginx_conf: str):
        """/api/ location must proxy_pass to http://backend."""
        # Find the /api/ location block and verify proxy_pass
        api_block = re.search(
            r"location\s+/api/\s*\{(.*?)\}", nginx_conf, re.DOTALL
        )
        assert api_block, "Missing /api/ location block"
        assert "proxy_pass http://backend" in api_block.group(1), (
            "/api/ must proxy_pass to http://backend"
        )

    def test_root_proxy_pass_to_frontend(self, nginx_conf: str):
        """Catch-all / location must proxy_pass to http://frontend."""
        root_block = re.search(
            r"location\s+/\s*\{(.*?)\}", nginx_conf, re.DOTALL
        )
        assert root_block, "Missing / location block"
        assert "proxy_pass http://frontend" in root_block.group(1), (
            "/ must proxy_pass to http://frontend"
        )

    def test_security_headers_present(self, nginx_conf: str):
        """Nginx must set security headers."""
        for header in ("X-Frame-Options", "X-Content-Type-Options", "X-XSS-Protection"):
            assert header in nginx_conf, f"Missing security header: {header}"

    def test_rate_limiting_configured(self, nginx_conf: str):
        """Rate limiting zones must be defined."""
        assert "limit_req_zone" in nginx_conf, "No rate limiting configured"
        assert "zone=api" in nginx_conf, "Missing API rate-limit zone"

    def test_health_endpoint_proxied(self, nginx_conf: str):
        """/health must be proxied to backend."""
        health_block = re.search(
            r"location\s+/health\s*\{(.*?)\}", nginx_conf, re.DOTALL
        )
        assert health_block, "Missing /health location block"
        assert "proxy_pass http://backend" in health_block.group(1)


# ---------------------------------------------------------------------------
# init.sql schema validation
# ---------------------------------------------------------------------------

class TestInitSql:
    """Validate init.sql creates the expected schema."""

    EXPECTED_TABLES = {
        "tenants",
        "users",
        "agents",
        "model_providers",
        "model_configs",
        "knowledge_bases",
        "documents",
        "usage_logs",
        "conversations",
        "messages",
    }

    def test_creates_agent_engine_database(self, init_sql: str):
        """Script must create the agent_engine database."""
        assert re.search(
            r"CREATE\s+DATABASE\s+IF\s+NOT\s+EXISTS\s+agent_engine",
            init_sql,
            re.IGNORECASE,
        ), "Missing CREATE DATABASE agent_engine"

    def test_all_expected_tables_created(self, init_sql: str):
        """All expected tables must be created."""
        # Extract table names from CREATE TABLE statements
        created = set(
            m.group(1).lower()
            for m in re.finditer(
                r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)",
                init_sql,
                re.IGNORECASE,
            )
        )
        missing = self.EXPECTED_TABLES - created
        assert not missing, f"Missing tables: {missing}"

    def test_utf8mb4_charset(self, init_sql: str):
        """Tables should use utf8mb4 charset for full Unicode support."""
        assert "utf8mb4" in init_sql, "init.sql should specify utf8mb4 charset"

    def test_seed_data_present(self, init_sql: str):
        """Default tenant and admin user seed data must exist."""
        assert "INSERT" in init_sql.upper(), "No seed data INSERT statements"
        assert "default" in init_sql, "Missing default tenant seed"
        assert "admin" in init_sql, "Missing admin user seed"


# ---------------------------------------------------------------------------
# .env.example safety checks
# ---------------------------------------------------------------------------

class TestEnvExampleSafety:
    """Ensure .env.example contains no real secrets."""

    # Patterns that would indicate a real secret was accidentally committed.
    SECRET_PATTERNS = [
        # Real API keys (long alphanumeric strings, not placeholders)
        r"(?i)api_key\s*=\s*[A-Za-z0-9]{20,}",
        # Real passwords (not <MUST_BE_SET>, not 'guest', not referencing other vars)
        r"(?i)password\s*=\s*(?!<|guest|\$\{)[^\s#]{8,}",
        # AWS-style keys
        r"AKIA[0-9A-Z]{16}",
        # Base64 blobs that look like real keys
        r"(?i)secret\s*=\s*[A-Za-z0-9+/=]{20,}",
    ]

    def _get_env_value_lines(self, env_text: str) -> list[tuple[str, str]]:
        """Return [(key, value)] for non-comment, non-empty lines."""
        pairs = []
        for line in env_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs.append((key.strip(), value.strip()))
        return pairs

    def test_no_real_api_keys(self, env_example: str):
        """No real API keys should appear in .env.example."""
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, env_example)
            # Filter out lines that are clearly placeholders
            real_matches = [
                m for m in matches
                if "<" not in m and "${" not in m and "MUST_BE_SET" not in m
            ]
            assert not real_matches, (
                f"Possible real secret found matching {pattern}: {real_matches}"
            )

    def test_sensitive_vars_marked_must_be_set(self, env_example: str):
        """Critical secrets must be marked <MUST_BE_SET> in .env.example."""
        sensitive_keys = {
            "MYSQL_ROOT_PASSWORD",
            "NEO4J_PASSWORD",
            "MINIO_SECRET_KEY",
            "SECRET_KEY",
            "ENCRYPTION_KEY",
        }
        pairs = self._get_env_value_lines(env_example)
        env_dict = {k: v for k, v in pairs}
        missing = set()
        for key in sensitive_keys:
            val = env_dict.get(key)
            if val is None or "<MUST_BE_SET>" not in val:
                missing.add(key)
        assert not missing, (
            f"Sensitive vars not marked <MUST_BE_SET>: {missing}"
        )

    def test_no_hardcoded_urls_with_credentials(self, env_example: str):
        """Connection strings should not embed real credentials."""
        # Lines like DATABASE_URL=mysql+aiomysql://root:realpass@... would be bad
        url_pattern = r"(?i)(url|uri|dsn)\s*=\s*\S+://[^#\s]+"
        for match in re.finditer(url_pattern, env_example):
            url = match.group(0)
            # Allow references to other env vars like ${MYSQL_ROOT_PASSWORD} or <MYSQL_ROOT_PASSWORD>
            if "${" in url or "<" in url:
                continue
            # Allow 'guest' as it's a well-known default
            if "guest" in url:
                continue
            # Check for password-like content after ://user:
            after_scheme = re.search(r"://[^:]+:([^@]+)@", url)
            if after_scheme:
                pwd = after_scheme.group(1)
                assert pwd.startswith("${") or pwd.startswith("<") or pwd in ("guest",), (
                    f"Possible hardcoded credential in URL: {url}"
                )

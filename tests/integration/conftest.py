"""Shared fixtures for Docker config integration tests."""

import os
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def docker_compose(project_root: Path) -> dict:
    """Load and parse docker-compose.yml."""
    path = project_root / "docker-compose.yml"
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def env_example(project_root: Path) -> str:
    """Return raw content of .env.example."""
    path = project_root / ".env.example"
    return path.read_text()


@pytest.fixture
def init_sql(project_root: Path) -> str:
    """Return raw content of scripts/init.sql."""
    path = project_root / "scripts" / "init.sql"
    return path.read_text()


@pytest.fixture
def nginx_conf(project_root: Path) -> str:
    """Return raw content of nginx/nginx.conf."""
    path = project_root / "nginx" / "nginx.conf"
    return path.read_text()

import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.v1 import api_router
from app.core.audit import AuditLogMiddleware
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.metrics_middleware import MetricsMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app_instance):
    """Application lifespan: startup and shutdown logic."""
    # --- Startup ---
    from app.engines.tool_engine.registry import register_builtin_tools
    register_builtin_tools()

    from app.core.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start()

    yield

    # --- Shutdown ---
    await scheduler.stop()

    from app.core.redis import close_redis
    await close_redis()


app = FastAPI(title="Agent Engine Platform", version="1.0.0", docs_url="/docs", lifespan=lifespan)

# SEC-009: HTTPS redirect middleware
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "false").lower() == "true"


@app.middleware("http")
async def https_redirect(request: Request, call_next):
    if FORCE_HTTPS and request.headers.get("X-Forwarded-Proto") == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url, status_code=301)
    return await call_next(request)


# Parse CORS origins from environment variable
def _parse_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    if not raw.strip():
        return ["http://localhost:3000"]
    try:
        origins = json.loads(raw)
        if isinstance(origins, list):
            return origins
    except (json.JSONDecodeError, TypeError):
        pass  # Fall through to comma-separated parsing
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


CORS_ORIGINS = _parse_cors_origins()

app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(api_router)

# Prometheus metrics endpoint
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    @app.get("/metrics")
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
except ImportError:
    pass  # prometheus_client not installed, /metrics endpoint unavailable

# Global exception handlers
from app.core.exceptions import (
    AgentEngineError,
    AllProvidersUnavailableError,
    DocumentNotFoundError,
    ModelNotFoundError,
    RateLimitExceededError,
)


@app.exception_handler(AgentEngineError)
async def agent_engine_error_handler(request: Request, exc: AgentEngineError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ModelNotFoundError)
async def not_found_handler(request: Request, exc: ModelNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.get("/health")
async def health():
    """Health check endpoint - returns component statuses."""
    import asyncio
    components = {}

    async def check_database():
        try:
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return "database", "ok"
        except Exception as e:
            return "database", f"error: {str(e)[:100]}"

    async def check_redis():
        try:
            from app.core.redis import get_redis
            r = await get_redis()
            await r.ping()
            return "redis", "ok"
        except Exception as e:
            return "redis", f"error: {str(e)[:100]}"

    async def check_milvus():
        try:
            from pymilvus import MilvusClient
            from app.config import settings
            client = MilvusClient(
                uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}",
                timeout=5,
            )
            client.close()
            return "milvus", "ok"
        except Exception as e:
            return "milvus", f"error: {str(e)[:100]}"

    async def check_neo4j():
        try:
            from neo4j import AsyncGraphDatabase
            from app.config import settings
            driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            async with driver.session() as session:
                await session.run("RETURN 1")
            await driver.close()
            return "neo4j", "ok"
        except Exception as e:
            return "neo4j", f"error: {str(e)[:100]}"

    async def check_elasticsearch():
        try:
            from elasticsearch import AsyncElasticsearch
            from app.config import settings
            es = AsyncElasticsearch(
                hosts=settings.ES_HOSTS.split(","),
                basic_auth=(settings.ES_USERNAME, settings.ES_PASSWORD) if settings.ES_USERNAME else None,
            )
            if await es.ping():
                await es.close()
                return "elasticsearch", "ok"
            await es.close()
            return "elasticsearch", "error: ping failed"
        except Exception as e:
            return "elasticsearch", f"error: {str(e)[:100]}"

    # Run all health checks concurrently
    results = await asyncio.gather(
        check_database(),
        check_redis(),
        check_milvus(),
        check_neo4j(),
        check_elasticsearch(),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, Exception):
            continue
        name, status = result
        components[name] = status

    all_ok = all(v == "ok" for v in components.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "version": "1.0.0",
        "components": components,
    }

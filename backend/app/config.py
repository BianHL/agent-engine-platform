from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---- General ----
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # ---- Database (MySQL) ----
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/agent_engine"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""  # embedded in REDIS_URL or set separately

    # ---- Celery (broker = Redis, same Redis instance different db) ----
    CELERY_BROKER_URL: str = ""  # defaults to redis://{host}:6379/2
    CELERY_RESULT_BACKEND: str = ""  # defaults to redis://{host}:6379/3
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600

    # ---- Milvus (Vector DB) ----
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_PREFIX: str = "aep_"  # table/collection name prefix

    # ---- Neo4j (Graph DB) ----
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"  # target database name

    # ---- Elasticsearch ----
    ES_HOSTS: str = "http://localhost:9200"
    ES_INDEX_PREFIX: str = "aep_"  # index name prefix
    ES_USERNAME: str = ""
    ES_PASSWORD: str = ""

    # ---- JWT / Auth ----
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- Encryption ----
    ENCRYPTION_KEY: str = "change-me-in-production"

    # ---- Cryptography backend ----
    CRYPTO_BACKEND: str = "standard"  # "standard" (default) or "gm" (国密)

    # ---- MCP Server Auth ----
    MCP_API_KEY: str = ""  # Required; MCP clients must send this key to authenticate

    # ---- CORS ----
    CORS_ORIGINS: str = '["http://localhost:3000"]'
    CORS_ALLOW_METHODS: str = '["GET","POST","PUT","DELETE","PATCH","OPTIONS"]'
    CORS_ALLOW_HEADERS: str = '["Authorization","Content-Type","X-Request-ID"]'

    # ---- Rate Limiting ----
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_RATE_LIMIT: int = 5  # attempts per window
    LOGIN_RATE_WINDOW: int = 60  # seconds

    # ---- Upload ----
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ---- Workflow ----
    WORKFLOW_GLOBAL_TIMEOUT: int = 300  # seconds
    WORKFLOW_CODE_SANDBOX_TIMEOUT: int = 30
    WORKFLOW_CODE_MAX_OUTPUT: int = 5000  # chars

    # ---- Safety ----
    SAFETY_INPUT_CHECK_ENABLED: bool = True
    SAFETY_OUTPUT_CHECK_ENABLED: bool = True

    # ---- WeCom (企业微信) integration ----
    WECOM_CORP_ID: str = ""
    WECOM_AGENT_ID: str = ""
    WECOM_SECRET: str = ""
    WECOM_REDIRECT_URI: str = ""
    WECOM_WEBHOOK_URL: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def _apply_defaults_and_validate(self) -> "Settings":
        # Derive Celery URLs from REDIS_URL if not explicitly set
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self._redis_url_for_db(2)
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self._redis_url_for_db(3)

        if self.ENVIRONMENT == "production":
            insecure = "change-me-in-production"
            for name in ("SECRET_KEY", "ENCRYPTION_KEY"):
                val = getattr(self, name)
                if val == insecure:
                    raise ValueError(f"{name} must be changed from default in production")
                if len(val) < 16:
                    raise ValueError(f"{name} must be >= 16 chars in production")
        return self

    def _redis_url_for_db(self, db: int) -> str:
        """Derive a Redis URL with a different db number from REDIS_URL."""
        url = self.REDIS_URL
        if "/" in url:
            base = url.rsplit("/", 1)[0]
            return f"{base}/{db}"
        return f"{url}/{db}"


settings = Settings()

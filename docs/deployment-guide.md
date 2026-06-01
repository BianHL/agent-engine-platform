# Agent Engine Platform — 测试环境部署手册

> 适用版本：V3 | 更新日期：2026-05-27

## 1. 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Docker | 24.0+ | 容器运行时 |
| Docker Compose | v2.20+ | `docker-compose` (V1 standalone) 或 `docker compose` (V2 插件) |
| 系统内存 | 16 GB | Milvus + ES + Neo4j 共需约 8 GB |
| 磁盘 | 40 GB | Docker 镜像 + 数据卷 |
| CPU | 4 核 | 推荐 8 核 |
| 操作系统 | Linux (Ubuntu 22.04+) / macOS | 内核 5.x+ |

### 端口清单

| 端口 | 服务 | 用途 | 暴露策略 |
|------|------|------|---------|
| 80 | Nginx | 统一入口 (HTTP) | 公开 |
| 443 | Nginx | HTTPS (可选) | 公开 |
| 3000 | Frontend | Next.js | 仅内部 |
| 8000 | Backend | FastAPI | 仅内部 |
| 3306 | MySQL | 数据库 | 仅本地 |
| 6379 | Redis | 缓存/会话 | 仅本地 |
| 19530 | Milvus | 向量数据库 | 仅本地 |
| 9091 | Milvus | 健康检查 | 仅本地 |
| 7474 | Neo4j | Browser UI | 仅本地 |
| 7687 | Neo4j | Bolt 协议 | 仅本地 |
| 9200 | Elasticsearch | REST API | 仅本地 |
| 9000 | MinIO | S3 API | 仅内部 |
| 9001 | MinIO | Console | 仅本地 |
| 5672 | RabbitMQ | AMQP | 仅内部 |
| 15672 | RabbitMQ | 管理界面 | 仅本地 |

---

## 2. 部署步骤

### 2.1 克隆代码

```bash
git clone <repo-url> /opt/agent-engine-platform
cd /opt/agent-engine-platform
```

### 2.2 生成密钥

```bash
# JWT 签名密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 示例: k8fG2aBx9TnQ7wRzPmVyDcX4eF1hJqLoU3sI0oA6bN

# Fernet 对称加密密钥 (用于 API Key / OAuth Token 加密存储)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 示例: u7XBh9fK2mNpQsR4vW6xYzA8cD3gE5hJ0kL2nO4qT6=
```

### 2.3 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写所有必填项（下表中 `<MUST_BE_SET>` 替换为实际值）：

```env
# ---- MySQL ----
MYSQL_ROOT_PASSWORD=<强密码，至少16位，如 MyS3cur3P@ssw0rd!>

# ---- Neo4j ----
NEO4J_USER=neo4j
NEO4J_PASSWORD=<强密码，不能是 "password">

# ---- MinIO ----
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=<强密码>

# ---- RabbitMQ ----
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=<强密码>

# ---- JWT ----
SECRET_KEY=<步骤 2.2 生成的 token_urlsafe 值>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ---- Encryption (敏感字段加密) ----
ENCRYPTION_KEY=<步骤 2.2 生成的 Fernet Key>

# ---- Database URL (密码须与 MYSQL_ROOT_PASSWORD 一致) ----
DATABASE_URL=mysql+aiomysql://root:<MYSQL_ROOT_PASSWORD>@mysql:3306/agent_engine

# ---- Redis ----
REDIS_URL=redis://redis:6379/0

# ---- Celery (用户名密码须与 RabbitMQ 一致) ----
CELERY_BROKER_URL=amqp://guest:<RABBITMQ_PASSWORD>@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1

# ---- Milvus ----
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530

# ---- Elasticsearch ----
ES_HOSTS=elasticsearch:9200

# ---- MinIO ----
MINIO_ENDPOINT=minio:9000

# ---- CORS (测试环境允许的前端地址) ----
CORS_ORIGINS=["http://<服务器IP或域名>","http://localhost:3000"]
```

**一致性检查：**
- `DATABASE_URL` 中的密码 = `MYSQL_ROOT_PASSWORD`
- `CELERY_BROKER_URL` 中的用户名:密码 = `RABBITMQ_USER`:`RABBITMQ_PASSWORD`

### 2.4 构建并启动

```bash
docker-compose up -d --build
```

首次启动约需 3-5 分钟（拉取镜像 + MySQL 初始化 + Milvus 初始化）。

### 2.5 检查服务状态

```bash
# 查看容器状态（等待全部 healthy 或 running）
docker-compose ps

# 持续观察直到所有服务就绪
watch -n 5 'docker-compose ps --format "table {{.Name}}\t{{.Status}}"'
```

预期全部服务 Up：

```
NAME                     STATUS
agent-engine-backend     Up
agent-engine-celery      Up
agent-engine-celery-beat Up
agent-engine-es          Up (healthy)
agent-engine-frontend    Up
agent-engine-milvus      Up (healthy)
agent-engine-minio       Up
agent-engine-mysql       Up (healthy)
agent-engine-neo4j       Up (healthy)
agent-engine-nginx       Up
agent-engine-rabbitmq    Up (healthy)
agent-engine-redis       Up (healthy)
```

### 2.6 验证健康

```bash
curl -s http://localhost/health | python3 -m json.tool
```

预期：

```json
{
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### 2.7 验证数据库初始化

```bash
docker-compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" agent_engine \
  -e "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='agent_engine';"
```

预期约 30 张表。

### 2.8 验证登录

```bash
curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | python3 -m json.tool
```

预期返回含 `access_token` 的 JSON。

---

## 3. 初始化配置

### 3.1 修改管理员密码

```bash
# 获取 token
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 修改密码
curl -X PUT http://localhost/api/v1/users/admin-user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "<新的强密码>"}'
```

### 3.2 配置 LLM Provider API Key

通过前端界面：**模型管理 → 选择 Provider → 编辑 → 填入 API Key**。

或通过 API：

```bash
# 更新 OpenAI Provider
curl -X PATCH http://localhost/api/v1/models/providers/provider-openai \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-xxx-your-key"}'

# 更新 Anthropic Provider
curl -X PATCH http://localhost/api/v1/models/providers/provider-anthropic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-ant-xxx-your-key"}'
```

> API Key 在数据库中通过 Fernet 加密存储，不会明文落盘。

### 3.3 验证对话功能

```bash
curl -s -X POST http://localhost/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "<创建的 agent id>", "messages": [{"role": "user", "content": "你好"}]}' \
  | python3 -m json.tool
```

---

## 4. 服务管理

### 4.1 常用命令

```bash
# 停止所有服务
docker-compose down

# 停止并清除数据卷（⚠️ 不可恢复）
docker-compose down -v

# 重启单个服务
docker-compose restart backend

# 代码更新后重新构建
docker-compose up -d --build backend celery-worker celery-beat frontend
docker-compose restart nginx

# 查看资源使用
docker stats --no-stream
```

### 4.2 仅启动基础设施（开发模式）

```bash
docker-compose up -d mysql redis milvus-standalone neo4j elasticsearch minio rabbitmq
```

然后本地启动 backend：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4.3 查看 Celery 任务状态

```bash
# RabbitMQ 管理界面
open http://localhost:15672  # guest / <RABBITMQ_PASSWORD>

# Celery Worker 日志
docker-compose logs -f celery-worker --tail 50
```

### 4.4 扩容 Celery Worker

```bash
docker-compose up -d --scale celery-worker=3
```

---

## 5. 备份与恢复

### 5.1 MySQL

```bash
# 备份
docker-compose exec mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction agent_engine > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复
docker-compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  agent_engine < backup_20260527.sql
```

### 5.2 Redis

```bash
# 触发 RDB 快照
docker-compose exec redis redis-cli BGSAVE
# 复制快照
docker-compose cp agent-engine-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### 5.3 Milvus

```bash
# 备份 volume（停服后执行更安全）
docker-compose stop milvus-standalone
docker run --rm \
  -v agent-engine-platform_milvus_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/milvus_backup_$(date +%Y%m%d).tar.gz -C /data .
docker-compose start milvus-standalone
```

### 5.4 Neo4j

```bash
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/tmp/
docker-compose cp agent-engine-neo4j:/tmp/neo4j.dump ./neo4j_backup_$(date +%Y%m%d).dump
```

---

## 6. 常见问题排查

### 6.1 Backend 启动失败: "SECRET_KEY must be changed"

`.env` 中 `SECRET_KEY` 或 `ENCRYPTION_KEY` 仍为默认值 `change-me-in-production`。
按步骤 2.2 生成新值并更新 `.env`，然后 `docker-compose restart backend celery-worker celery-beat`。

### 6.2 Milvus 健康检查超时

Milvus 首次启动需 90 秒以上。如果持续失败：

```bash
docker-compose logs milvus-standalone --tail 50
curl http://localhost:9091/healthz

# 重置 Milvus 数据
docker-compose down
docker volume rm agent-engine-platform_milvus_data
docker-compose up -d milvus-standalone
```

### 6.3 MySQL 连接被拒

```bash
docker-compose exec mysql mysqladmin ping -h localhost -uroot -p"${MYSQL_ROOT_PASSWORD}"
```

如果密码不对，重置：

```bash
docker-compose down
docker volume rm agent-engine-platform_mysql_data
# 修改 .env 中的 MYSQL_ROOT_PASSWORD 和 DATABASE_URL
docker-compose up -d
```

### 6.4 Celery Worker 无法连接 RabbitMQ

检查 `CELERY_BROKER_URL` 中的用户名密码是否与 `RABBITMQ_USER`/`RABBITMQ_PASSWORD` 一致。

```bash
docker-compose exec rabbitmq rabbitmq-diagnostics check_running
docker-compose logs celery-worker --tail 20
```

### 6.5 Elasticsearch 内存不足 (OOM)

编辑 `docker-compose.yml`：

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 默认 512m，改为 1g
```

### 6.6 前端白屏 / API 502

```bash
# 检查 Nginx 配置
docker-compose exec nginx nginx -t

# 检查 Backend
docker-compose ps backend
curl http://localhost:8000/health
```

### 6.7 Neo4j 启动失败

`NEO4J_PASSWORD` 不能为空，不能是 `password`，不能是 `neo4j`。

---

## 7. 架构总览

```
                       ┌──────────────┐
                       │   Browser    │
                       └──────┬───────┘
                              │ :80 / :443
                       ┌──────▼───────┐
                       │    Nginx     │  反向代理 · 限流 · 安全头
                       └───┬──────┬───┘
                           │      │
                  /api/*   │      │  /*
                           │      │
                    ┌──────▼──┐ ┌─▼─────────┐
                    │ Backend │ │  Frontend  │
                    │ :8000   │ │  :3000     │
                    └────┬────┘ └────────────┘
                         │
         ┌───────┬───────┼───────┬────────────┐
         │       │       │       │            │
    ┌────▼──┐ ┌─▼────┐ ┌▼─────┐ ┌▼────────┐ ┌▼─────────┐
    │ MySQL │ │Redis │ │Milvus│ │RabbitMQ │ │ Neo4j    │
    │ :3306 │ │:6379 │ │:19530│ │ :5672   │ │ :7687    │
    └───────┘ └──────┘ └──────┘ └────┬─────┘ └──────────┘
                                      │
                               ┌──────▼──────┐
                               │Celery Worker│ × N
                               │Celery Beat  │
                               └─────────────┘

    ┌────────────┐  ┌──────────────┐  ┌────────────┐
    │    ES      │  │    MinIO     │  │  Milvus    │
    │  :9200     │  │ :9000/:9001  │  │  向量检索   │
    │  全文检索   │  │  文件存储    │  │            │
    └────────────┘  └──────────────┘  └────────────┘
```

---

## 8. 环境变量参考

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | **是** | — | MySQL root 密码 |
| `NEO4J_USER` | 否 | neo4j | Neo4j 用户名 |
| `NEO4J_PASSWORD` | **是** | — | Neo4j 密码 |
| `MINIO_ACCESS_KEY` | 否 | minioadmin | MinIO Access Key |
| `MINIO_SECRET_KEY` | **是** | — | MinIO Secret Key |
| `RABBITMQ_USER` | 否 | guest | RabbitMQ 用户名 |
| `RABBITMQ_PASSWORD` | 否 | guest | RabbitMQ 密码 |
| `SECRET_KEY` | **是** | — | JWT 签名密钥 (≥32 字符) |
| `ENCRYPTION_KEY` | **是** | — | Fernet 加密密钥 |
| `ALGORITHM` | 否 | HS256 | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | 30 | JWT 有效期 (分钟) |
| `DATABASE_URL` | 否* | — | MySQL 连接串 (需与 MYSQL_ROOT_PASSWORD 一致) |
| `REDIS_URL` | 否 | redis://redis:6379/0 | Redis 连接串 |
| `CELERY_BROKER_URL` | 否* | — | Celery Broker (需与 RabbitMQ 密码一致) |
| `CELERY_RESULT_BACKEND` | 否 | redis://redis:6379/1 | Celery 结果后端 |
| `MILVUS_HOST` | 否 | milvus-standalone | Milvus 主机 |
| `MILVUS_PORT` | 否 | 19530 | Milvus 端口 |
| `ES_HOSTS` | 否 | elasticsearch:9200 | Elasticsearch 地址 |
| `MINIO_ENDPOINT` | 否 | minio:9000 | MinIO 端点 |
| `CORS_ORIGINS` | 否 | ["http://localhost:3000"] | CORS 允许的来源 (JSON 数组或逗号分隔) |
| `ENVIRONMENT` | 否 | development | 环境标识 (development/staging/production) |

> \* `DATABASE_URL` 和 `CELERY_BROKER_URL` 有默认值但不保证正确，建议显式设置。

---

## 9. 安全加固清单

- [ ] `.env` 文件权限设置为 `600`: `chmod 600 .env`
- [ ] 修改 admin 默认密码 (`admin123`)
- [ ] 所有密码 ≥ 16 位，含大小写 + 数字 + 特殊字符
- [ ] `SECRET_KEY` 和 `ENCRYPTION_KEY` 使用随机生成值
- [ ] `CORS_ORIGINS` 仅包含实际前端地址，不含 `*`
- [ ] 非公开端口绑定 `127.0.0.1`（修改 `docker-compose.yml` 的 `ports` 为 `127.0.0.1:3306:3306`）
- [ ] 启用 HTTPS（证书放入 `nginx/ssl/`，修改 `nginx.conf`）
- [ ] 定期备份 MySQL（建议 cron 每日一次）
- [ ] 审计日志保留 ≥ 90 天
- [ ] MinIO Console / RabbitMQ Management / Neo4j Browser 仅内网可访问

---

## 10. 验收清单

部署完成后逐项验证：

- [ ] `curl http://<HOST>/health` → `{"status":"ok"}`
- [ ] 浏览器访问 `http://<HOST>/login` 显示登录页
- [ ] `admin / <修改后密码>` 登录成功，跳转 Dashboard
- [ ] Dashboard 页面数据正常加载
- [ ] Agent 管理：创建 → 编辑 → 发布成功
- [ ] 知识库：创建 → 上传文档 → 文档处理完成 (status=ready)
- [ ] 知识库：检索测试返回结果
- [ ] 对话：与 Agent 对话正常响应
- [ ] 工具管理：工具列表正常显示
- [ ] 模型管理：Provider 列表 + API Key 配置成功
- [ ] 工作流：创建 → 执行成功
- [ ] RabbitMQ 管理界面 `http://<HOST>:15672` 可访问
- [ ] MinIO Console `http://<HOST>:9001` 可访问
- [ ] 后端日志无 ERROR 级别异常
- [ ] Celery Worker 日志无连接错误

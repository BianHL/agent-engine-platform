# Agent Engine Platform 管理员指南

> **版本**: v3.0  
> **更新日期**: 2026-06-01  
> **适用角色**: 系统管理员、运维人员

---

## 目录

- [1. 系统管理](#1-系统管理)
- [2. 用户管理](#2-用户管理)
- [3. 租户管理](#3-租户管理)
- [4. 权限管理](#4-权限管理)
- [5. 模型配置](#5-模型配置)
- [6. 系统监控](#6-系统监控)
- [7. 安全管理](#7-安全管理)
- [8. 备份恢复](#8-备份恢复)
- [9. 性能优化](#9-性能优化)
- [10. 运维自动化](#10-运维自动化)

---

## 1. 系统管理

### 1.1 系统配置

#### 环境变量管理

所有系统配置通过环境变量管理，配置文件位于 `.env`。

**关键配置项**:

```env
# 通用配置
ENVIRONMENT=production          # development/staging/production
LOG_LEVEL=INFO                 # DEBUG/INFO/WARNING/ERROR
APP_PORT=8000                  # 后端端口
FRONTEND_PORT=3000             # 前端端口

# 数据库配置
DATABASE_URL=mysql+aiomysql://root:password@mysql:3306/agent_engine
DB_POOL_SIZE=20                # 连接池大小
DB_MAX_OVERFLOW=40             # 最大溢出连接

# Redis配置
REDIS_URL=redis://:password@redis:6379/0

# JWT配置
SECRET_KEY=<random-32-chars>   # JWT签名密钥
ACCESS_TOKEN_EXPIRE_MINUTES=30 # 令牌有效期

# 安全配置
ENCRYPTION_KEY=<fernet-key>    # 数据加密密钥
```

#### 配置更新流程

1. 修改 `.env` 文件
2. 重启相关服务：
   ```bash
   docker-compose restart backend celery-worker celery-beat frontend
   ```
3. 验证配置生效：
   ```bash
   curl http://localhost:8000/health
   ```

### 1.2 服务管理

#### 服务状态检查

```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务状态
docker-compose ps backend

# 查看服务日志
docker-compose logs -f backend --tail 100

# 查看资源使用
docker stats --no-stream
```

#### 服务启停操作

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启单个服务
docker-compose restart backend

# 重启所有服务
docker-compose restart
```

#### 服务扩展

```bash
# 扩展Celery Worker
docker-compose up -d --scale celery-worker=3

# 扩展后端实例（需要负载均衡器）
docker-compose up -d --scale backend=3
```

### 1.3 数据库管理

#### MySQL管理

**连接数据库**:
```bash
docker-compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" agent_engine
```

**查看数据库状态**:
```sql
-- 查看表
SHOW TABLES;

-- 查看表结构
DESCRIBE table_name;

-- 查看数据量
SELECT COUNT(*) FROM table_name;
```

**数据库迁移**:
```bash
# 查看当前版本
docker-compose exec backend alembic current

# 升级到最新版本
docker-compose exec backend alembic upgrade head

# 生成新迁移
docker-compose exec backend alembic revision --autogenerate -m "description"

# 回滚迁移
docker-compose exec backend alembic downgrade -1
```

#### Redis管理

**连接Redis**:
```bash
docker-compose exec redis redis-cli -a "${REDIS_PASSWORD}"
```

**常用命令**:
```bash
# 查看所有键
KEYS *

# 查看键类型
TYPE key_name

# 查看键过期时间
TTL key_name

# 清空数据库
FLUSHDB

# 查看内存使用
INFO memory
```

#### Milvus管理

**健康检查**:
```bash
curl http://localhost:9091/healthz
```

**查看集合**:
```bash
curl http://localhost:9091/collections
```

#### Neo4j管理

**访问Neo4j Browser**: http://localhost:7474

**常用Cypher查询**:
```cypher
// 查看所有节点
MATCH (n) RETURN n LIMIT 25

// 查看节点数量
MATCH (n) RETURN count(n)

// 查看关系
MATCH ()-[r]->() RETURN type(r), count(r)
```

### 1.4 日志管理

#### 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|---------|
| DEBUG | 详细调试信息 | 开发环境 |
| INFO | 一般信息 | 生产环境 |
| WARNING | 警告信息 | 需要关注 |
| ERROR | 错误信息 | 需要处理 |

#### 查看日志

```bash
# 实时查看后端日志
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail 100 backend

# 查看错误日志
docker-compose logs backend | grep ERROR

# 查看特定时间段日志
docker-compose logs --since "2026-06-01T10:00:00" backend
```

#### 日志轮转

配置日志轮转防止磁盘占满：

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 2. 用户管理

### 2.1 用户创建

#### 通过API创建用户

```bash
# 获取管理员令牌
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 创建用户
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "securepassword123",
    "email": "newuser@example.com",
    "full_name": "新用户",
    "role": "developer"
  }'
```

#### 通过前端创建用户

1. 登录管理后台
2. 进入"用户管理"页面
3. 点击"创建用户"
4. 填写用户信息
5. 选择角色
6. 点击"保存"

### 2.2 用户角色

#### 预设角色

| 角色 | 权限 | 说明 |
|------|------|------|
| `admin` | 全部权限 | 系统管理员 |
| `developer` | 开发相关权限 | 开发人员 |
| `operator` | 运维相关权限 | 运维人员 |
| `viewer` | 只读权限 | 普通用户 |

#### 自定义角色

可以通过API创建自定义角色：

```bash
curl -X POST http://localhost:8000/api/v1/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_role",
    "description": "自定义角色",
    "permissions": [
      "agents:read",
      "agents:create",
      "knowledge:read",
      "workflows:read"
    ]
  }'
```

### 2.3 用户操作

#### 修改用户信息

```bash
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "full_name": "更新后的姓名"
  }'
```

#### 重置密码

```bash
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newpassword123"
  }'
```

#### 禁用用户

```bash
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "disabled"
  }'
```

#### 删除用户

```bash
curl -X DELETE http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer $TOKEN"
```

### 2.4 用户审计

#### 查看用户活动

```bash
curl -X GET "http://localhost:8000/api/v1/audit?user_id={user_id}" \
  -H "Authorization: Bearer $TOKEN"
```

#### 查看登录历史

```bash
curl -X GET "http://localhost:8000/api/v1/audit?action=user.login" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 3. 租户管理

### 3.1 租户创建

#### 创建租户

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例租户",
    "description": "用于演示的租户",
    "quota": {
      "max_users": 50,
      "max_agents": 20,
      "max_storage_gb": 50
    }
  }'
```

### 3.2 租户配置

#### 资源配额

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `max_users` | 最大用户数 | 100 |
| `max_agents` | 最大智能体数 | 50 |
| `max_knowledge_bases` | 最大知识库数 | 20 |
| `max_workflows` | 最大工作流数 | 30 |
| `max_storage_gb` | 最大存储空间(GB) | 100 |

#### 租户设置

```json
{
  "settings": {
    "allow_public_agents": false,
    "allow_external_tools": true,
    "require_approval_for_publish": true,
    "default_model": "gpt-4o",
    "max_tokens_per_request": 4096
  }
}
```

### 3.3 租户隔离

#### 数据隔离

- 每个租户的数据完全隔离
- 用户只能访问自己租户的数据
- API请求自动过滤租户ID

#### 资源隔离

- 每个租户有独立的资源配额
- 超出配额时返回错误
- 可以单独调整每个租户的配额

---

## 4. 权限管理

### 4.1 RBAC模型

#### 权限结构

```
权限 = 资源:操作

示例:
- agents:read      # 查看智能体
- agents:create    # 创建智能体
- agents:update    # 更新智能体
- agents:delete    # 删除智能体
- agents:*         # 智能体所有权限
```

#### 资源类型

| 资源 | 说明 |
|------|------|
| `agents` | 智能体 |
| `knowledge` | 知识库 |
| `workflows` | 工作流 |
| `tools` | 工具 |
| `models` | 模型 |
| `users` | 用户 |
| `roles` | 角色 |
| `tenants` | 租户 |
| `audit` | 审计日志 |

#### 操作类型

| 操作 | 说明 |
|------|------|
| `read` | 查看 |
| `create` | 创建 |
| `update` | 更新 |
| `delete` | 删除 |
| `execute` | 执行 |
| `*` | 所有操作 |

### 4.2 角色管理

#### 创建角色

```bash
curl -X POST http://localhost:8000/api/v1/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_analyst",
    "description": "数据分析师",
    "permissions": [
      "agents:read",
      "knowledge:read",
      "knowledge:create",
      "workflows:read",
      "workflows:execute",
      "tools:read",
      "tools:execute"
    ]
  }'
```

#### 修改角色权限

```bash
curl -X PUT http://localhost:8000/api/v1/roles/{role_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": [
      "agents:read",
      "agents:create",
      "knowledge:*",
      "workflows:*"
    ]
  }'
```

### 4.3 权限检查

#### API权限验证

所有API请求都会进行权限验证：

1. 验证JWT令牌
2. 提取用户角色
3. 检查角色权限
4. 验证资源访问权限

#### 权限错误响应

```json
{
  "code": 403,
  "message": "权限不足",
  "detail": "需要 agents:create 权限"
}
```

---

## 5. 模型配置

### 5.1 模型提供商配置

#### OpenAI配置

```bash
curl -X PATCH http://localhost:8000/api/v1/models/providers/provider-openai \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-xxx-your-key",
    "enabled": true
  }'
```

#### Anthropic配置

```bash
curl -X PATCH http://localhost:8000/api/v1/models/providers/provider-anthropic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-ant-xxx-your-key",
    "enabled": true
  }'
```

#### Ollama配置（本地模型）

```bash
curl -X PATCH http://localhost:8000/api/v1/models/providers/provider-ollama \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_base": "http://ollama:11434",
    "enabled": true
  }'
```

### 5.2 模型管理

#### 查看可用模型

```bash
curl -X GET http://localhost:8000/api/v1/models \
  -H "Authorization: Bearer $TOKEN"
```

#### 模型使用统计

```bash
curl -X GET "http://localhost:8000/api/v1/usage?group_by=day&start_date=2026-06-01" \
  -H "Authorization: Bearer $TOKEN"
```

### 5.3 成本控制

#### 设置使用配额

```json
{
  "quota": {
    "max_tokens_per_day": 1000000,
    "max_requests_per_day": 10000,
    "max_cost_per_day": 100.00
  }
}
```

#### 成本监控

```bash
# 查看今日成本
curl -X GET "http://localhost:8000/api/v1/usage?start_date=$(date +%Y-%m-%d)" \
  -H "Authorization: Bearer $TOKEN"

# 查看本月成本
curl -X GET "http://localhost:8000/api/v1/usage?start_date=$(date +%Y-%m-01)" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 6. 系统监控

### 6.1 健康检查

#### 应用健康检查

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "ok",
  "components": {
    "database": {"status": "ok", "latency": 5},
    "redis": {"status": "ok", "latency": 2},
    "milvus": {"status": "ok", "latency": 10},
    "neo4j": {"status": "ok", "latency": 8},
    "elasticsearch": {"status": "ok", "latency": 15}
  }
}
```

#### 服务状态检查

```bash
# 检查所有服务
docker-compose ps

# 检查特定服务
docker-compose ps backend

# 检查资源使用
docker stats --no-stream
```

### 6.2 性能监控

#### 系统指标

```bash
# CPU和内存使用
docker stats --no-stream

# 磁盘使用
df -h

# 网络连接
netstat -tulpn
```

#### 应用指标

```bash
# 查看API响应时间
curl -o /dev/null -s -w "Time: %{time_total}s\n" http://localhost:8000/health

# 查看数据库连接数
docker-compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SHOW STATUS LIKE 'Threads_connected';"
```

### 6.3 日志监控

#### 实时日志监控

```bash
# 监控所有服务日志
docker-compose logs -f

# 监控特定服务日志
docker-compose logs -f backend

# 监控错误日志
docker-compose logs -f | grep ERROR
```

#### 日志分析

```bash
# 统计错误数量
docker-compose logs backend | grep ERROR | wc -l

# 查看最近错误
docker-compose logs --tail 100 backend | grep ERROR
```

### 6.4 告警配置

#### 基于日志的告警

```bash
# 监控错误日志并发送告警
docker-compose logs -f backend | grep ERROR | while read line; do
  # 发送告警通知
  curl -X POST "https://hooks.slack.com/..." \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"ERROR: $line\"}"
done
```

#### 基于指标的告警

```bash
# 监控CPU使用率
while true; do
  CPU=$(docker stats --no-stream --format "{{.CPUPerc}}" agent-engine-backend | sed 's/%//')
  if (( $(echo "$CPU > 80" | bc -l) )); then
    # 发送告警
    echo "CPU使用率过高: $CPU"
  fi
  sleep 60
done
```

---

## 7. 安全管理

### 7.1 访问控制

#### IP白名单

配置Nginx限制访问IP：

```nginx
# nginx/nginx.conf
server {
    listen 80;
    
    # 限制访问IP
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    location / {
        proxy_pass http://frontend;
    }
}
```

#### API限流

配置环境变量：

```env
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=60
```

### 7.2 数据加密

#### 敏感数据加密

所有敏感数据使用Fernet加密存储：

- API密钥
- 用户密码（bcrypt哈希）
- 配置中的敏感信息

#### 传输加密

配置HTTPS：

```bash
# 生成证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# 修改nginx配置启用HTTPS
```

### 7.3 安全审计

#### 审计日志

所有关键操作都会记录审计日志：

- 用户登录/登出
- 智能体创建/修改/删除
- 知识库操作
- 工作流执行
- 权限变更

#### 查看审计日志

```bash
curl -X GET "http://localhost:8000/api/v1/audit" \
  -H "Authorization: Bearer $TOKEN"
```

### 7.4 安全加固清单

- [ ] 修改所有默认密码
- [ ] 启用HTTPS
- [ ] 配置IP白名单
- [ ] 设置强密码策略
- [ ] 启用审计日志
- [ ] 定期轮换密钥
- [ ] 限制API访问频率
- [ ] 禁用不必要的服务
- [ ] 定期更新依赖
- [ ] 配置防火墙规则

---

## 8. 备份恢复

### 8.1 数据备份

#### MySQL备份

```bash
# 全量备份
docker-compose exec mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction agent_engine > backup_$(date +%Y%m%d_%H%M%S).sql

# 压缩备份
docker-compose exec mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction agent_engine | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 定时备份（每天凌晨2点）
echo "0 2 * * * cd /opt/agent-engine-platform && docker-compose exec mysql mysqldump -uroot -p\"\${MYSQL_ROOT_PASSWORD}\" --single-transaction agent_engine | gzip > /backup/mysql_$(date +\%Y\%m\%d).sql.gz" | crontab -
```

#### Redis备份

```bash
# 触发RDB快照
docker-compose exec redis redis-cli BGSAVE

# 复制快照
docker-compose cp agent-engine-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

#### Milvus备份

```bash
# 停止服务
docker-compose stop milvus-standalone

# 备份数据
docker run --rm \
  -v agent-engine-platform_milvus_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/milvus_backup_$(date +%Y%m%d).tar.gz -C /data .

# 启动服务
docker-compose start milvus-standalone
```

#### Neo4j备份

```bash
# 备份数据库
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/tmp/
docker-compose cp agent-engine-neo4j:/tmp/neo4j.dump ./neo4j_backup_$(date +%Y%m%d).dump
```

#### 完整备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "开始备份..."

# MySQL备份
echo "备份MySQL..."
docker-compose exec mysql mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction agent_engine | gzip > $BACKUP_DIR/mysql.sql.gz

# Redis备份
echo "备份Redis..."
docker-compose exec redis redis-cli BGSAVE
sleep 5
docker-compose cp agent-engine-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Milvus备份
echo "备份Milvus..."
docker-compose stop milvus-standalone
docker run --rm \
  -v agent-engine-platform_milvus_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/milvus.tar.gz -C /data .
docker-compose start milvus-standalone

# Neo4j备份
echo "备份Neo4j..."
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/tmp/
docker-compose cp agent-engine-neo4j:/tmp/neo4j.dump $BACKUP_DIR/neo4j.dump

echo "备份完成: $BACKUP_DIR"
```

### 8.2 数据恢复

#### MySQL恢复

```bash
# 恢复备份
docker-compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  agent_engine < backup_20260601.sql

# 恢复压缩备份
gunzip < backup_20260601.sql.gz | docker-compose exec -T mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  agent_engine
```

#### Redis恢复

```bash
# 停止Redis
docker-compose stop redis

# 替换数据文件
docker-compose cp redis_backup.rdb agent-engine-redis:/data/dump.rdb

# 启动Redis
docker-compose start redis
```

#### Milvus恢复

```bash
# 停止Milvus
docker-compose stop milvus-standalone

# 恢复数据
docker run --rm \
  -v agent-engine-platform_milvus_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/milvus_backup.tar.gz -C /data

# 启动Milvus
docker-compose start milvus-standalone
```

#### Neo4j恢复

```bash
# 停止Neo4j
docker-compose stop neo4j

# 恢复数据库
docker-compose cp neo4j_backup.dump agent-engine-neo4j:/tmp/
docker-compose exec neo4j neo4j-admin database load neo4j --from-path=/tmp/

# 启动Neo4j
docker-compose start neo4j
```

### 8.3 备份策略

#### 备份频率

| 数据类型 | 备份频率 | 保留时间 |
|---------|---------|---------|
| MySQL | 每天 | 30天 |
| Redis | 每天 | 7天 |
| Milvus | 每周 | 90天 |
| Neo4j | 每周 | 90天 |

#### 备份存储

- 本地备份: `/backup/` 目录
- 远程备份: 上传到对象存储（如S3）
- 异地备份: 复制到其他数据中心

---

## 9. 性能优化

### 9.1 数据库优化

#### MySQL优化

**索引优化**:
```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';

-- 查看执行计划
EXPLAIN SELECT * FROM agents WHERE id = 'xxx';

-- 添加索引
CREATE INDEX idx_agents_status ON agents(status);
```

**连接池优化**:
```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600
```

#### Redis优化

**内存优化**:
```bash
# 查看内存使用
docker-compose exec redis redis-cli INFO memory

# 配置内存策略
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 9.2 应用优化

#### 后端优化

**异步处理**:
- 使用异步IO处理并发请求
- 使用Celery处理耗时任务
- 使用连接池复用数据库连接

**缓存策略**:
- 使用Redis缓存热点数据
- 设置合理的缓存过期时间
- 使用缓存减少数据库查询

#### 前端优化

**代码分割**:
```javascript
// 使用动态导入
const HeavyComponent = dynamic(() => import('./HeavyComponent'))
```

**图片优化**:
```javascript
// 使用Next.js Image组件
import Image from 'next/image'
<Image src="/image.png" width={500} height={300} />
```

### 9.3 基础设施优化

#### Docker优化

**资源限制**:
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**日志优化**:
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 网络优化

**Nginx优化**:
```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 启用缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g;
```

---

## 10. 运维自动化

### 10.1 自动化脚本

#### 部署脚本

```bash
#!/bin/bash
# deploy.sh

set -e

echo "开始部署..."

# 拉取最新代码
git pull origin main

# 构建镜像
docker-compose build

# 停止旧服务
docker-compose down

# 启动新服务
docker-compose up -d

# 等待服务就绪
sleep 30

# 健康检查
curl -f http://localhost:8000/health || exit 1

echo "部署完成"
```

#### 监控脚本

```bash
#!/bin/bash
# monitor.sh

# 检查服务状态
check_service() {
  local service=$1
  local status=$(docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep $service | awk '{print $2}')
  
  if [[ $status != *"Up"* ]]; then
    echo "警告: $service 未运行"
    # 发送告警
    send_alert "$service 未运行"
  fi
}

# 检查所有服务
check_service "backend"
check_service "frontend"
check_service "mysql"
check_service "redis"
check_service "milvus-standalone"
check_service "neo4j"
check_service "elasticsearch"
```

### 10.2 CI/CD集成

#### GitHub Actions示例

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      
      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_KEY }}
          script: |
            cd /opt/agent-engine-platform
            git pull
            docker-compose up -d --build
```

### 10.3 容器编排

#### Docker Compose生产配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: agent-engine-backend:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Kubernetes部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: agent-engine-backend:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
```

---

## 附录

### A. 常用命令速查

```bash
# 服务管理
docker-compose up -d          # 启动所有服务
docker-compose down           # 停止所有服务
docker-compose restart        # 重启所有服务
docker-compose ps             # 查看服务状态
docker-compose logs -f        # 查看日志

# 数据库操作
docker-compose exec mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" agent_engine
docker-compose exec redis redis-cli -a "${REDIS_PASSWORD}"

# 备份恢复
./backup.sh                   # 执行备份
./restore.sh                  # 执行恢复

# 健康检查
curl http://localhost:8000/health
```

### B. 配置文件位置

| 文件 | 位置 | 说明 |
|------|------|------|
| 环境变量 | `.env` | 系统配置 |
| Docker配置 | `docker-compose.yml` | 服务编排 |
| Nginx配置 | `nginx/nginx.conf` | 反向代理 |
| 数据库迁移 | `backend/alembic/` | 数据库版本 |

### C. 故障排查流程

1. **检查服务状态**: `docker-compose ps`
2. **查看服务日志**: `docker-compose logs -f backend`
3. **检查健康状态**: `curl http://localhost:8000/health`
4. **检查资源使用**: `docker stats --no-stream`
5. **检查网络连接**: `ping localhost`
6. **检查端口占用**: `lsof -i :8000`

### D. 联系方式

- **文档**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **源码**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

---

**文档维护**: 本文档由Agent Engine Platform团队维护，如有问题或建议，请提交Issue。

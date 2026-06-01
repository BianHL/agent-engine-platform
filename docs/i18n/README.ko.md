<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">올인원 AI Agent 구축, 관리 및 오케스트레이션 플랫폼.</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.de.md">🇩🇪 Deutsch</a> •
  <a href="README.es.md">🇪🇸 Español</a> •
  <a href="README.pt.md">🇵🇹 Português</a> •
  <a href="README.ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <a href="../../LICENSE">
    <img src="https://img.shields.io/badge/License-Private-red.svg" alt="License">
  </a>
  <a href="../../backend/requirements.txt">
    <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" alt="Python">
  </a>
  <a href="../../frontend/package.json">
    <img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg" alt="Node">
  </a>
</p>

<p align="center">
  <a href="#빠른-시작">빠른 시작</a> •
  <a href="#핵심-기능">핵심 기능</a> •
  <a href="#시스템-아키텍처">시스템 아키텍처</a> •
  <a href="#엔진-모듈">엔진 모듈</a> •
  <a href="#api-개요">API</a> •
  <a href="#설정-안내">설정</a> •
  <a href="#배포-가이드">배포</a> •
  <a href="#기술-스택">기술 스택</a>
</p>

---

## 개요

Agent Engine Platform은 Agent 생성, 지식 베이스 관리, 워크플로우 오케스트레이션, 다중 Agent 협력, 보안 감사까지 완전한 기능을 제공하는 풀스택 지능형 에이전트 애플리케이션 엔진 플랫폼입니다.

**백엔드**: FastAPI + Python 3.11  
**프론트엔드**: Next.js 14 + React 18 + Ant Design  
**인프라**: Docker Compose 오케스트레이션

---

## 핵심 기능

- 🤖 **Agent 관리** - 지능형 에이전트의 생성, 구성, 배포를 지원하며, 모델 선택, 시스템 프롬프트, 도구 바인딩, 지식 베이스 연결을 지원합니다
- 🔀 **다중 모델 라우팅** - OpenAI / Anthropic / Ollama 등 다양한 LLM 제공업체를 통합 어댑터로 지원하며, 로드 밸런싱, 회로 차단 폴백, 비용 추적을 지원합니다
- 📚 **지식 엔진** - 완전한 RAG 파이프라인으로, 문서 파싱(PDF/Word/Excel/PPT), 지능형 청킹, 벡터 검색(Milvus), 전문 검색(ES), 그래프 검색(Neo4j) 및 LightRAG 이중 수준 검색을 지원합니다
- ⚡ **워크플로우 엔진** - 시각적 DAG 오케스트레이션으로, LLM 노드, 조건 분기, 병렬 실행, 루프, HTTP 호출, 코드 샌드박스, 인력 승인 및 하위 워크플로우를 지원합니다
- 🤝 **다중 Agent 협력** - Crew 모드(순차/계층/병렬/합의) 및 Handoff 라우팅 프로토콜
- 🔧 **도구 엔진** - 내장 계산기, 코드 실행기, 데이터베이스 쿼리, 파일 작업, HTTP 요청, 웹 검색을 포함하며, 사용자 정의 도구 등록을 지원합니다
- 🛡️ **보안 엔진** - 입출력 보안 감지로, Prompt 주입 방어, PII 비식별화, 민감 정보 필터링을 포함합니다
- 📊 **평가 엔진** - Ragas 스타일 RAG 품질 평가(faithfulness/relevancy/precision/recall/tool accuracy)
- 🧠 **메모리 시스템** - 단기 메모리(Redis 세션 히스토리) + 장기 메모리(벡터화 저장 + 주제 추출 + 요약 압축)
- 🔌 **MCP 서비스** - Model Context Protocol을 통해 플랫폼 기능을 외부에 노출
- 👥 **다중 테넌시** - 완전한 테넌트 격리, RBAC 권한 체계, 부서 관리 및 API Token 관리
- 📝 **감사 및 모니터링** - 운영 로그, API 호출 감사, 모델 사용량 추적, 속도 제한

---

## 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- 최소 8GB 사용 가능한 메모리 (Milvus + Elasticsearch는 많은 리소스가 필요합니다)

### 1. 클론 및 구성

```bash
git clone <repository-url>
cd agent-engine-platform

# 환경 변수 복사 및 필수 설정 수정
cp .env.example .env
# .env 편집, 최소한 다음 항목을 설정하세요:
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (프로덕션 환경에서는 반드시 수정 필요)
```

### 2. 모든 서비스 시작

```bash
# 전체 시작 (모든 인프라 + 애플리케이션 서비스)
docker compose --profile full up -d

# 또는 외부 데이터베이스 사용 (애플리케이션 + Neo4j만 시작)
docker compose --profile external-db up -d
```

### 3. 접속

| 서비스 | 주소 | 설명 |
|--------|------|------|
| 프론트엔드 | http://localhost:3000 | Next.js 관리 인터페이스 |
| 백엔드 API | http://localhost:8000 | FastAPI 서비스 |
| API 문서 | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | 통합 진입점 |
| Neo4j Browser | http://localhost:7474 | 그래프 데이터베이스 콘솔 |

### 4. 로컬 개발 (Docker 미사용)

**백엔드:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**프론트엔드:**

```bash
cd frontend
npm install
npm run dev
```

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (리버스 프록시)                      │
│                   HTTP :80 / HTTPS :443                      │
└──────────┬──────────────────────────────┬───────────────────┘
           │                              │
    ┌──────▼──────┐               ┌───────▼───────┐
    │  Frontend   │               │   Backend     │
    │  Next.js 14 │               │   FastAPI     │
    │  :3000      │               │   :8000       │
    └─────────────┘               └───────┬───────┘
                                          │
                    ┌─────────────────────┬┴──────────────────┐
                    │                     │                    │
             ┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────┐
             │    MySQL    │    │     Redis       │   │   Celery    │
             │  주 데이터베이스│    │  캐시/메시지 큐   │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│ 벡터 데이터베이스│  │  전문 검색 엔진 │ │ 그래프 데이터베이스│
└─────────┘  └─────────────┘ └─────────┘
```

### 데이터 흐름

1. **사용자 요청** → Nginx → Frontend(SSR/CSR) 또는 Backend API
2. **대화 요청** → Backend → 보안 엔진(입력 감지) → 모델 라우팅 → LLM → 보안 엔진(출력 감지) → SSE 스트리밍 반환
3. **RAG 요청** → 지식 엔진 → 문서 파싱 → 청킹 → Embedding → 저장(Milvus/ES/Neo4j) → 검색 → Rerank → 생성
4. **비동기 작업** → Backend → Celery Worker(문서 처리, 모델 학습, 정기 정리)
5. **워크플로우 실행** → 워크플로우 엔진 → DAG 스케줄링 → 노드 실행 → 인력 승인 → 결과 출력

---

## 엔진 모듈

### 모델 엔진

통합 LLM 어댑터 레이어로, 다양한 제공업체를 지원합니다:

| 어댑터 | 지원 모델 | 기능 |
|--------|---------|------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama(로컬 모델) | Chat / Streaming |

핵심 특징: **ModelRouter**(다중 Provider 로드 밸런싱), **CircuitBreaker**(회로 차단기 패턴), **CostTracker**(Token 사용량 추적 및 비용 계산), **멀티모달**(ASR/TTS/OCR/Vision 어댑터)

### 지식 엔진

문서에서 답변까지 완전한 RAG 파이프라인:

```
문서 업로드 → 파싱(PDF/Word/Excel/PPT/TXT) → 지능형 청킹 → Embedding
    → 저장(Milvus + ES + Neo4j) → 검색(벡터/전문/그래프/LightRAG) → Rerank → 생성
```

**LightRAG 검색 모드:**

| 모드 | 설명 | 적합한 시나리오 |
|------|------|---------------|
| `naive` | 순수 벡터 유사도 | 일반 Q&A |
| `local` | 엔티티 집중 - 구체적 이름 추출로 그래프 노드 검색 | 정확한 사실 조회 |
| `global` | 주제 집중 - 광범위한 개념 추출로 관계 엣지 검색 | 거시적 분석 |
| `hybrid` | local + global 가중 RRF 융합 | 복합 종합 쿼리 |

### 워크플로우 엔진

DAG 워크플로우 오케스트레이션으로, 다음 노드 유형을 지원합니다:

| 노드 유형 | 설명 |
|----------|------|
| `llm` | LLM 호출 노드 |
| `condition` | 조건 분기 |
| `parallel` | 병렬 실행 |
| `loop` | 루프 실행 |
| `http` | HTTP 요청 |
| `code` | Python 코드 샌드박스(리소스 격리) |
| `human` | 인력 승인 |
| `sub_workflow` | 하위 워크플로우 호출 |

특징: 전역 타임아웃 제어, 노드 수준 실행 추적, 변수 스냅샷, 상세 실행 로그.

### 다중 Agent 엔진

**Crew 모드**: 다중 Agent 팀 협력
- Sequential(순차 실행), Hierarchical(계층 관리), Parallel(병렬 실행), Consensus(합의 결정)

**Handoff 모드**: Agent 간 구조화된 인수인계
- Pydantic 기반 `HandoffMessage` 프로토콜
- `HandoffTracker`로 인수인계 상태 및 홉 수 추적

### 도구 엔진

내장 도구 세트:

| 도구 | 기능 |
|------|------|
| `calculator` | 수학 표현식 계산 |
| `code_executor` | Python 코드 샌드박스 실행 |
| `db_query` | 데이터베이스 쿼리(파라미터화) |
| `file_ops` | 파일 읽기/쓰기 작업 |
| `http_request` | HTTP 요청 |
| `web_search` | 웹 검색 |

`ToolRegistry`를 통한 사용자 정의 도구 동적 등록을 지원합니다.

### 보안 엔진

4중 보안 방어:
1. **Prompt 주입 감지** - 정규식 매칭 + 의미 분석
2. **PII 비식별화** - 주민등록번호, 휴대폰 번호, 이메일, 은행 카드 등 자동 인식 및 비식별화
3. **민감 정보 필터링** - 구성 가능한 민감도 수준(low/medium/high)
4. **컴플라이언스 검사** - 선택적 컴플라이언스 정책 스위치

### 메모리 엔진

- **ShortTermMemory** - Redis 기반 세션 히스토리로, TTL 및 최대 메시지 수 제한 지원
- **LongTermMemory** - 대화 요약 압축 + 주제 추출 + 벡터화 저장으로, 교차 세션 검색 지원

### 평가 엔진

Ragas 스타일 RAG 품질 평가, 5개 핵심 지표:
- `faithfulness` - 답변이 검색된 컨텍스트에 충실한지 여부
- `answer_relevancy` - 답변과 질문의 관련성
- `context_precision` - 검색 결과의 순위 품질
- `context_recall` - 검색이 모든 필수 정보를 커버하는지 여부
- `tool_call_accuracy` - 도구 호출의 정확성

---

## API 개요

모든 API 라우트 접두사: `/api/v1`

| 모듈 | 라우트 | 설명 |
|------|--------|------|
| Auth | `/auth/*` | 로그인, 회원가입, Token 갱신 |
| Agents | `/agents/*` | Agent CRUD, 배포 |
| Chat | `/chat/*` | 대화(SSE 스트리밍) |
| Conversations | `/conversations/*` | 세션 관리 |
| Knowledge | `/knowledge/*` | 지식 베이스, 문서 업로드, 검색 |
| Models | `/models/*` | 모델 제공업체 구성 |
| Workflows | `/workflows/*` | 워크플로우 CRUD, 실행 |
| Tools | `/tools/*` | 도구 관리 |
| Multi-Agent | `/multi-agent/*` | 다중 Agent 오케스트레이션 |
| Memory | `/memory/*` | 메모리 관리 |
| Evaluations | `/evaluations/*` | RAG 평가 |
| Triggers | `/triggers/*` | Cron / 이벤트 / Webhook 트리거 |
| Webhooks | `/webhooks/*` | Webhook 엔드포인트 관리 |
| Audit | `/audit/*` | 감사 로그 조회 |
| Usage | `/usage/*` | 모델 사용량 통계 |
| Users | `/users/*` | 사용자 관리 |
| Roles | `/roles/*` | 역할 권한 관리 |
| Tenants | `/tenants/*` | 테넌트 관리 |
| Tokens | `/tokens/*` | API Token 관리 |
| Feedbacks | `/feedbacks/*` | 사용자 피드백 |
| Tasks | `/tasks/*` | Celery 작업 상태 |

**헬스 체크**: `GET /health` — 데이터베이스 및 Redis 연결 상태를 반환합니다.

---

## 설정 안내

모든 설정은 환경 변수를 통해 관리되며, `.env.example`을 참조하세요.

### 프로덕션 환경에서 반드시 수정해야 하는 설정

| 설정 항목 | 설명 |
|-----------|------|
| `DB_PASSWORD` | MySQL root 비밀번호 |
| `REDIS_PASSWORD` | Redis 인증 비밀번호 |
| `NEO4J_PASSWORD` | Neo4j 인증 비밀번호 |
| `SECRET_KEY` | JWT 서명 키(≥16자) |
| `ENCRYPTION_KEY` | 데이터 암호화 키(≥16자) |

### 주요 조정 가능 파라미터

| 설정 항목 | 기본값 | 설명 |
|-----------|--------|------|
| `DB_POOL_SIZE` | 10 | 데이터베이스 연결 풀 크기 |
| `RATE_LIMIT_PER_MINUTE` | 60 | API 속도 제한 |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery Worker 동시 실행 수 |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | 워크플로우 전역 타임아웃(초) |
| `MAX_UPLOAD_SIZE_MB` | 50 | 파일 업로드 크기 제한(MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | 입력 보안 감지 스위치 |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | 출력 보안 감지 스위치 |

---

## 배포 가이드

### Docker 배포 (권장)

```bash
# 1. 환경 변수 구성
cp .env.example .env
vim .env  # 모든 <PRODUCTION> 표시 항목 수정

# 2. 보안 키 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 시작
docker compose --profile full up -d

# 4. 로그 확인
docker compose logs -f backend
```

### Nginx HTTPS 구성

`nginx/nginx.conf`를 편집하여 HTTPS server block 주석을 해제하고, 인증서를 `nginx/ssl/` 디렉토리에 배치합니다:

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### 외부 데이터베이스 모드

MySQL / Redis / Milvus / ES가 외부 서비스에 의해 제공되는 경우, `.env`에서 해당 연결 URL을 구성한 후:

```bash
docker compose --profile external-db up -d
```

---

## 기술 스택

### 백엔드

| 기술 | 용도 |
|------|------|
| Python 3.11 | 런타임 |
| FastAPI | 웹 프레임워크 |
| SQLAlchemy 2.0 + aiomysql | 비동기 ORM |
| Pydantic 2.0 | 데이터 검증 |
| Celery + Redis | 비동기 작업 큐 |
| Alembic | 데이터베이스 마이그레이션 |
| python-jose | JWT 인증 |
| httpx | 비동기 HTTP 클라이언트 |
| sse-starlette | SSE 스트리밍 응답 |
| pymilvus | Milvus 벡터 데이터베이스 클라이언트 |
| neo4j | Neo4j 그래프 데이터베이스 드라이버 |
| elasticsearch | ES 클라이언트 |
| minio | 객체 저장 클라이언트 |

### 프론트엔드

| 기술 | 용도 |
|------|------|
| Next.js 14 | React 프레임워크(App Router) |
| React 18 | UI 라이브러리 |
| TypeScript 5 | 타입 안전성 |
| Ant Design 5 | UI 컴포넌트 라이브러리 |
| Tailwind CSS 3 | 스타일링 |
| Zustand | 상태 관리 |
| Axios | HTTP 클라이언트 |
| ECharts | 데이터 시각화 |
| React Markdown | Markdown 렌더링 |
| Jest + Testing Library | 테스트 |

### 인프라

| 기술 | 용도 |
|------|------|
| Docker Compose | 서비스 오케스트레이션 |
| MySQL 8.0 | 주 데이터베이스 |
| Redis 7 | 캐시 + 메시지 큐 |
| Milvus 2.4 | 벡터 데이터베이스 |
| Neo4j 5 | 그래프 데이터베이스 |
| Elasticsearch 8.12 | 전문 검색 |
| Nginx | 리버스 프록시 + 속도 제한 |
| MinIO | 객체 저장(선택사항) |

---

## 프로젝트 구조

```
agent-engine-platform/
├── backend/                        # Python 백엔드 (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # RESTful API 라우트 (20+ 모듈)
│   │   ├── core/                   # 핵심 인프라
│   │   ├── engines/                # 핵심 엔진 모듈
│   │   ├── models/                 # SQLAlchemy ORM 모델
│   │   ├── schemas/                # Pydantic 요청/응답 Schema
│   │   ├── tasks/                  # Celery 비동기 작업
│   │   ├── mcp/                    # MCP 서버
│   │   └── main.py                 # FastAPI 애플리케이션 진입점
│   ├── tests/                      # 테스트 (unit / integration)
│   ├── alembic/                    # 데이터베이스 마이그레이션
│   └── Dockerfile
├── frontend/                       # TypeScript 프론트엔드 (Next.js 14)
│   ├── src/
│   │   ├── app/                    # App Router 페이지
│   │   ├── components/             # React 컴포넌트
│   │   ├── lib/                    # API 클라이언트
│   │   ├── store/                  # Zustand 상태 관리
│   │   └── types/                  # TypeScript 타입 정의
│   └── Dockerfile
├── nginx/                          # Nginx 리버스 프록시 구성
├── scripts/                        # 데이터베이스 초기화 SQL
├── docs/                           # 문서
├── docker-compose.yml              # 모든 서비스 오케스트레이션
├── .env.example                    # 환경 변수 템플릿
└── AGENTS.md                       # 자동화 에이전트 규칙
```

---

## 개발 및 테스트

### 백엔드 테스트

```bash
cd backend

# 모든 테스트 실행
pytest

# 단위 테스트만
pytest tests/unit -v

# 통합 테스트만
pytest tests/integration -v

# 데이터베이스 마이그레이션
alembic upgrade head

# 마이그레이션 생성
alembic revision --autogenerate -m "description"
```

### 프론트엔드 개발

```bash
cd frontend

npm install        # 의존성 설치
npm run dev        # 개발 서버 시작 (:3000)
npm run build      # 프로덕션 빌드
npm test           # 테스트 실행 (Jest)
npm run lint       # ESLint 검사
```

### 코드 규약

| 수준 | 규약 |
|------|------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-space indent |
| 네이밍 | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| 커밋 | Conventional Commits (`feat(scope): description`) |

---

## License

Private / Proprietary

---

## 지원

- **문서**: [docs/](../../docs/)
- **이슈 피드백**: [GitHub Issues](https://github.com/your-org/agent-engine-platform/issues)
- **저장소**: [github.com/your-org/agent-engine-platform](https://github.com/your-org/agent-engine-platform)

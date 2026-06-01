<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">Plataforma integral para la creación, gestión y orquestación de Agentes AI.</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.de.md">🇩🇪 Deutsch</a> •
  <a href="README.pt.md">🇵🇹 Português</a> •
  <a href="README.ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <a href="../../LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
  <a href="../../backend/requirements.txt">
    <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" alt="Python">
  </a>
  <a href="../../frontend/package.json">
    <img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg" alt="Node">
  </a>
</p>

<p align="center">
  <a href="#inicio-rápido">Inicio Rápido</a> •
  <a href="#capacidades-principales">Capacidades Principales</a> •
  <a href="#arquitectura-del-sistema">Arquitectura</a> •
  <a href="#módulos-de-motores">Motores</a> •
  <a href="#resumen-de-api">API</a> •
  <a href="#configuración">Configuración</a> •
  <a href="#guía-de-despliegue">Despliegue</a> •
  <a href="#stack-tecnológico">Stack Tecnológico</a>
</p>

---

## Resumen

Agent Engine Platform es una plataforma de motores de aplicaciones de agentes inteligentes de pila completa, que proporciona capacidades completas desde la creación de Agentes, gestión de bases de conocimiento, orquestación de flujos de trabajo, colaboración multi-Agente hasta auditoría de seguridad.

**Backend**: FastAPI + Python 3.11  
**Frontend**: Next.js 14 + React 18 + Ant Design  
**Infraestructura**: Orquestación con Docker Compose

---

## Capacidades Principales

- 🤖 **Gestión de Agentes** - Crear, configurar y publicar agentes inteligentes, con soporte para selección de modelos, prompts del sistema, vinculación de herramientas y asociación de bases de conocimiento
- 🔀 **Enrutamiento Multi-modelo** - Adaptación unificada para múltiples proveedores de LLM como OpenAI / Anthropic / Ollama, con soporte para balanceo de carga, circuit breaker y seguimiento de costos
- 📚 **Motor de Conocimiento** - Pipeline RAG completo, con soporte para análisis de documentos (PDF/Word/Excel/PPT), fragmentación inteligente, recuperación vectorial (Milvus), recuperación de texto completo (ES), recuperación de grafos (Neo4j) y recuperación de dos niveles LightRAG
- ⚡ **Motor de Flujo de Trabajo** - Orquestación DAG visual, con soporte para nodos LLM,分支 condicionales, ejecución paralela, bucles, llamadas HTTP, sandbox de código, aprobación humana y sub-flujos de trabajo
- 🤝 **Colaboración Multi-Agente** - Modo Crew (secuencial/jerárquico/paralelo/consenso) y protocolo de路由 Handoff
- 🔧 **Motor de Herramientas** - Herramientas integradas: calculadora, ejecutor de código, consulta de base de datos, operaciones de archivo, solicitud HTTP, búsqueda web, con soporte para registro de herramientas personalizadas
- 🛡️ **Motor de Seguridad** - Detección de seguridad de entrada y salida, que cubre防护 de inyección de Prompt, desensibilización de PII, filtrado de información sensible
- 📊 **Motor de Evaluación** - Evaluación de calidad RAG al estilo Ragas (faithfulness/relevancy/precision/recall/tool accuracy)
- 🧠 **Sistema de Memoria** - Memoria a corto plazo (historial de sesiones Redis) + Memoria a largo plazo (almacenamiento vectorial + extracción de temas + compresión de resúmenes)
- 🔌 **Servicio MCP** - Exponer capacidades de la plataforma a través de Model Context Protocol
- 👥 **Multi-tenancy** - Aislamiento completo de inquilinos, sistema de permisos RBAC, gestión departamental y gestión de Tokens API
- 📝 **Auditoría y Monitoreo** - Registros de operaciones, auditoría de llamadas API, seguimiento de uso de modelos, límite de velocidad

---

## Inicio Rápido

### Prerrequisitos

- Docker & Docker Compose
- Al menos 8GB de memoria disponible (Milvus + Elasticsearch requieren较多 recursos)

### 1. Clonar y Configurar

```bash
git clone <repository-url>
cd agent-engine-platform

# Copiar variables de entorno y modificar la configuración necesaria
cp .env.example .env
# Editar .env, establecer al menos los siguientes:
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (debe modificarse para producción)
```

### 2. Iniciar Todos los Servicios

```bash
# Inicio completo (toda la infraestructura + servicios de aplicación)
docker compose --profile full up -d

# O usar base de datos externa (solo iniciar aplicación + Neo4j)
docker compose --profile external-db up -d
```

### 3. Acceder

| Servicio | Dirección | Descripción |
|----------|-----------|-------------|
| Frontend | http://localhost:3000 | Interfaz de administración Next.js |
| Backend API | http://localhost:8000 | Servicio FastAPI |
| Documentación API | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | Entrada unificada |
| Neo4j Browser | http://localhost:7474 | Consola de base de datos de grafos |

### 4. Desarrollo Local (sin Docker)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Proxy Inverso)                │
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
             │  Base de    │    │  Caché/Cola de  │   │  Worker/Beat│
             │  datos      │    │  mensajes       │   │             │
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│ Base de │  │  Motor de    │ │ Base de │
│ datos   │  │  búsqueda    │ │ datos   │
│ vectorial│  │  texto completo│ │ de grafos│
└─────────┘  └─────────────┘ └─────────┘
```

### Flujo de Datos

1. **Solicitud del usuario** → Nginx → Frontend (SSR/CSR) o Backend API
2. **Solicitud de conversación** → Backend → Motor de seguridad (detección de entrada) → Enrutamiento de modelo → LLM → Motor de seguridad (detección de salida) → Respuesta en streaming SSE
3. **Solicitud RAG** → Motor de conocimiento → Análisis de documentos → Fragmentación → Embedding → Almacenamiento (Milvus/ES/Neo4j) → Recuperación → Rerank → Generación
4. **Tareas asíncronas** → Backend → Celery Worker (procesamiento de documentos, entrenamiento de modelos, limpieza programada)
5. **Ejecución de flujo de trabajo** → Motor de flujo de trabajo → Programación DAG → Ejecución de nodos → Aprobación humana → Salida de resultados

---

## Módulos de Motores

### Motor de Modelo

Capa de adaptación LLM unificada, con soporte para múltiples proveedores:

| Adaptador | Modelos Soportados | Capacidades |
|-----------|-------------------|-------------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama (modelos locales) | Chat / Streaming |

Características principales: **ModelRouter** (balanceo de carga multi-Proveedor), **CircuitBreaker** (patrón de circuit breaker), **CostTracker** (seguimiento de uso de tokens y cálculo de costos), **Multimodal** (adaptadores ASR/TTS/OCR/Vision)

### Motor de Conocimiento

Pipeline RAG completo, desde documentos hasta respuestas:

```
Carga de documentos → Análisis (PDF/Word/Excel/PPT/TXT) → Fragmentación inteligente → Embedding
    → Almacenamiento (Milvus + ES + Neo4j) → Recuperación (vectorial/texto completo/grafos/LightRAG) → Rerank → Generación
```

**Modos de recuperación LightRAG:**

| Modo | Descripción | Escenarios de Aplicación |
|------|-------------|-------------------------|
| `naive` | Similitud vectorial pura | Preguntas generales |
| `local` | Enfoque en entidades — extrae nombres específicos para buscar nodos de grafos | Consultas de hechos precisos |
| `global` | Enfoque en temas — extrae conceptos amplios para buscar bordes de relaciones | Análisis macro |
| `hybrid` | Fusión ponderada RRF de local + global | Consultas complejas e integrales |

### Motor de Flujo de Trabajo

Orquestación de flujo de trabajo DAG, con soporte para los siguientes tipos de nodos:

| Tipo de Nodo | Descripción |
|--------------|-------------|
| `llm` | Nodo de llamada LLM |
| `condition` | Bifurcación condicional |
| `parallel` | Ejecución paralela |
| `loop` | Ejecución en bucle |
| `http` | Solicitud HTTP |
| `code` | Sandbox de código Python (aislamiento de recursos) |
| `human` | Aprobación humana |
| `sub_workflow` | Llamada a sub-flujo de trabajo |

Características: Control de超时 global, seguimiento de ejecución a nivel de nodo, instantáneas de variables, registros de ejecución detallados.

### Motor Multi-Agente

**Modo Crew**: Colaboración en equipo de múltiples Agentes
- Sequential (ejecución secuencial), Hierarchical (gestión jerárquica), Parallel (ejecución paralela), Consensus (toma de decisiones por consenso)

**Modo Handoff**: Handoff estructurado entre Agentes
- Protocolo `HandoffMessage` basado en Pydantic
- `HandoffTracker` para seguimiento del estado de handoff y saltos

### Motor de Herramientas

Conjunto de herramientas integradas:

| Herramienta | Función |
|-------------|---------|
| `calculator` | Cálculo de expresiones matemáticas |
| `code_executor` | Ejecución sandbox de código Python |
| `db_query` | Consulta de base de datos (parametrizada) |
| `file_ops` | Operaciones de lectura/escritura de archivos |
| `http_request` | Solicitud HTTP |
| `web_search` | Búsqueda web |

Soporte para registro dinámico de herramientas personalizadas a través de `ToolRegistry`.

### Motor de Seguridad

Protección de seguridad en cuatro capas:
1. **Detección de inyección de Prompt** - Coincidencia de expresiones regulares + análisis semántico
2. **Desensibilización de PII** - Identificación automática y desensibilización de números de identificación, números de teléfono, correos electrónicos, números de tarjetas bancarias, etc.
3. **Filtrado de información sensible** - Niveles de sensibilidad configurables (low/medium/high)
4. **Verificación de cumplimiento** - Interruptores de políticas de cumplimiento opcionales

### Motor de Memoria

- **ShortTermMemory** - Historial de sesiones basado en Redis, con soporte para TTL y límite máximo de mensajes
- **LongTermMemory** - Compresión de resúmenes de conversación + extracción de temas + almacenamiento vectorial, con soporte para recuperación entre sesiones

### Motor de Evaluación

Evaluación de calidad RAG al estilo Ragas, 5 indicadores principales:
- `faithfulness` - Si la respuesta es fiel al contexto recuperado
- `answer_relevancy` - Relevancia de la respuesta con la pregunta
- `context_precision` - Calidad de clasificación de los resultados de recuperación
- `context_recall` - Si la recuperación cubre toda la información necesaria
- `tool_call_accuracy` - Correctitud de las llamadas a herramientas

---

## Resumen de API

Todas las rutas API prefijo: `/api/v1`

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Auth | `/auth/*` | Inicio de sesión, registro, actualización de Token |
| Agents | `/agents/*` | CRUD de Agentes, publicación |
| Chat | `/chat/*` | Conversación (streaming SSE) |
| Conversations | `/conversations/*` | Gestión de conversaciones |
| Knowledge | `/knowledge/*` | Base de conocimiento, carga de documentos, recuperación |
| Models | `/models/*` | Configuración de proveedores de modelos |
| Workflows | `/workflows/*` | CRUD de flujos de trabajo, ejecución |
| Tools | `/tools/*` | Gestión de herramientas |
| Multi-Agent | `/multi-agent/*` | Orquestación multi-Agente |
| Memory | `/memory/*` | Gestión de memoria |
| Evaluations | `/evaluations/*` | Evaluación RAG |
| Triggers | `/triggers/*` | Disparadores Cron / Evento / Webhook |
| Webhooks | `/webhooks/*` | Gestión de endpoints Webhook |
| Audit | `/audit/*` | Consulta de registros de auditoría |
| Usage | `/usage/*` | Estadísticas de uso de modelos |
| Users | `/users/*` | Gestión de usuarios |
| Roles | `/roles/*` | Gestión de permisos de roles |
| Tenants | `/tenants/*` | Gestión de inquilinos |
| Tokens | `/tokens/*` | Gestión de Tokens API |
| Feedbacks | `/feedbacks/*` | Comentarios de usuarios |
| Tasks | `/tasks/*` | Estado de tareas Celery |

**Verificación de salud**: `GET /health` — Devuelve el estado de conexión de la base de datos y Redis.

---

## Configuración

Toda la configuración se gestiona a través de variables de entorno, consulte `.env.example`.

### Configuración que debe modificarse en producción

| Elemento de Configuración | Descripción |
|---------------------------|-------------|
| `DB_PASSWORD` | Contraseña root de MySQL |
| `REDIS_PASSWORD` | Contraseña de autenticación de Redis |
| `NEO4J_PASSWORD` | Contraseña de autenticación de Neo4j |
| `SECRET_KEY` | Clave de firma JWT (≥16 caracteres) |
| `ENCRYPTION_KEY` | Clave de cifrado de datos (≥16 caracteres) |

### Parámetros clave ajustables

| Elemento de Configuración | Valor Predeterminado | Descripción |
|---------------------------|----------------------|-------------|
| `DB_POOL_SIZE` | 10 | Tamaño del pool de conexiones de base de datos |
| `RATE_LIMIT_PER_MINUTE` | 60 | Límite de velocidad de API |
| `CELERY_WORKER_CONCURRENCY` | 4 | Concurrency de Celery Worker |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 |超时 global del flujo de trabajo (segundos) |
| `MAX_UPLOAD_SIZE_MB` | 50 | Límite de tamaño de carga de archivos (MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | Interruptor de detección de seguridad de entrada |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | Interruptor de detección de seguridad de salida |

---

## Guía de Despliegue

### Despliegue con Docker (Recomendado)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
vim .env  # Modificar todos los elementos marcados con <PRODUCTION>

# 2. Generar claves de seguridad
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Iniciar
docker compose --profile full up -d

# 4. Ver registros
docker compose logs -f backend
```

### Configuración HTTPS de Nginx

Edite `nginx/nginx.conf`, descomente el bloque de servidor HTTPS y coloque los certificados en el directorio `nginx/ssl/`:

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### Modo de base de datos externa

Si MySQL / Redis / Milvus / ES son proporcionados por servicios externos, configure las URL de conexión correspondientes en `.env`, luego:

```bash
docker compose --profile external-db up -d
```

---

## Stack Tecnológico

### Backend

| Tecnología | Uso |
|------------|-----|
| Python 3.11 | Runtime |
| FastAPI | Framework web |
| SQLAlchemy 2.0 + aiomysql | ORM asíncrono |
| Pydantic 2.0 | Validación de datos |
| Celery + Redis | Cola de tareas asíncronas |
| Alembic | Migraciones de base de datos |
| python-jose | Autenticación JWT |
| httpx | Cliente HTTP asíncrono |
| sse-starlette | Respuesta en streaming SSE |
| pymilvus | Cliente de base de datos vectorial Milvus |
| neo4j | Controlador de base de datos de grafos Neo4j |
| elasticsearch | Cliente ES |
| minio | Cliente de almacenamiento de objetos |

### Frontend

| Tecnología | Uso |
|------------|-----|
| Next.js 14 | Framework React (App Router) |
| React 18 | Librería UI |
| TypeScript 5 | Seguridad de tipos |
| Ant Design 5 | Librería de componentes UI |
| Tailwind CSS 3 | Estilos |
| Zustand | Gestión de estado |
| Axios | Cliente HTTP |
| ECharts | Visualización de datos |
| React Markdown | Renderizado Markdown |
| Jest + Testing Library | Pruebas |

### Infraestructura

| Tecnología | Uso |
|------------|-----|
| Docker Compose | Orquestación de servicios |
| MySQL 8.0 | Base de datos principal |
| Redis 7 | Caché + cola de mensajes |
| Milvus 2.4 | Base de datos vectorial |
| Neo4j 5 | Base de datos de grafos |
| Elasticsearch 8.12 | Búsqueda de texto completo |
| Nginx | Proxy inverso + limitación de velocidad |
| MinIO | Almacenamiento de objetos (opcional) |

---

## Estructura del Proyecto

```
agent-engine-platform/
├── backend/                        # Backend Python (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # Rutas API RESTful (20+ módulos)
│   │   ├── core/                   # Infraestructura central
│   │   ├── engines/                # Módulos de motores principales
│   │   ├── models/                 # Modelos ORM SQLAlchemy
│   │   ├── schemas/                # Schema Pydantic请求/响应
│   │   ├── tasks/                  # Tareas asíncronas Celery
│   │   ├── mcp/                    # Servidor MCP
│   │   └── main.py                 # Punto de entrada de la aplicación FastAPI
│   ├── tests/                      # Pruebas (unitarias / integración)
│   ├── alembic/                    # Migraciones de base de datos
│   └── Dockerfile
├── frontend/                       # Frontend TypeScript (Next.js 14)
│   ├── src/
│   │   ├── app/                    # Páginas del App Router
│   │   ├── components/             # Componentes React
│   │   ├── lib/                    # Cliente API
│   │   ├── store/                  # Gestión de estado Zustand
│   │   └── types/                  # Definiciones de tipos TypeScript
│   └── Dockerfile
├── nginx/                          # Configuración del proxy inverso Nginx
├── scripts/                        # SQL de inicialización de base de datos
├── docs/                           # Documentación
├── docker-compose.yml              # Orquestación de todos los servicios
├── .env.example                    # Plantilla de variables de entorno
└── AGENTS.md                       # Reglas de agentes automatizados
```

---

## Desarrollo y Pruebas

### Pruebas de Backend

```bash
cd backend

# Ejecutar todas las pruebas
pytest

# Solo pruebas unitarias
pytest tests/unit -v

# Solo pruebas de integración
pytest tests/integration -v

# Migraciones de base de datos
alembic upgrade head

# Generar migración
alembic revision --autogenerate -m "description"
```

### Desarrollo de Frontend

```bash
cd frontend

npm install        # Instalar dependencias
npm run dev        # Iniciar servidor de desarrollo (:3000)
npm run build      # Construcción para producción
npm test           # Ejecutar pruebas (Jest)
npm run lint       # Verificación ESLint
```

### Estándares de Código

| Nivel | Estándar |
|-------|----------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + sangría de 2 espacios |
| Nomenclatura | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| Commits | Conventional Commits (`feat(scope): description`) |

---

## License

Este proyecto está licenciado bajo la Licencia Apache 2.0 - consulte el archivo [LICENSE](../../LICENSE) para obtener detalles.

---

## Contribuciones

¡Las contribuciones son bienvenidas! No dude en enviar un Pull Request.

1. Haga un fork del repositorio
2. Cree su rama de función (`git checkout -b feature/amazing-feature`)
3. Confirme sus cambios (`git commit -m 'feat: add amazing feature'`)
4. Envíe a la rama (`git push origin feature/amazing-feature`)
5. Abra un Pull Request

---

## Soporte

- **Documentación**: [docs/](../../docs/)
- **Reporte de problemas**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **Repositorio**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)
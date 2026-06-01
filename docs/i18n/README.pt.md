<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">Plataforma completa para criação, gerenciamento e orquestração de AI Agents.</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.de.md">🇩🇪 Deutsch</a> •
  <a href="README.es.md">🇪🇸 Español</a> •
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
  <a href="#início-rápido">Início Rápido</a> •
  <a href="#recursos-principais">Recursos Principais</a> •
  <a href="#arquitetura-do-sistema">Arquitetura</a> •
  <a href="#módulos-de-motores">Motores</a> •
  <a href="#visão-geral-da-api">API</a> •
  <a href="#configuração">Configuração</a> •
  <a href="#guia-de-deploy">Deploy</a> •
  <a href="#stack-tecnológico">Stack</a>
</p>

---

## Visão Geral

Agent Engine Platform é uma plataforma completa de engine para aplicações de agentes inteligentes, fornecendo capacidades completas desde criação de Agentes, gerenciamento de base de conhecimento, orquestração de workflows, colaboração multi-Agent até auditoria de segurança.

**Backend**: FastAPI + Python 3.11  
**Frontend**: Next.js 14 + React 18 + Ant Design  
**Infraestrutura**: Docker Compose

---

## Recursos Principais

- 🤖 **Gerenciamento de Agentes** - Crie, configure e publique agentes inteligentes com suporte a seleção de modelos, prompts do sistema, vinculação de ferramentas e associação de base de conhecimento
- 🔀 **Roteamento Multi-Modelo** - Adaptador unificado para OpenAI / Anthropic / Ollama e outros provedores LLM, com suporte a balanceamento de carga, circuit breaker e rastreamento de custos
- 📚 **Motor de Conhecimento** - Pipeline RAG completo com suporte a parsing de documentos (PDF/Word/Excel/PPT), chunking inteligente, busca vetorial (Milvus), busca full-text (ES), busca em grafos (Neo4j) e LightRAG de dois níveis
- ⚡ **Motor de Workflow** - Orquestração visual DAG com suporte a nós LLM, condições de分支, execução paralela, loops, chamadas HTTP, sandbox de código, aprovação humana e sub-workflows
- 🤝 **Colaboração Multi-Agent** - Modo Crew (sequencial/hierárquico/paralelo/consenso) e protocolo de handoff
- 🔧 **Motor de Ferramentas** - Calculadora, executor de código, consulta a banco de dados, operações de arquivo, requisições HTTP e pesquisa web integradas, com suporte a registro de ferramentas customizadas
- 🛡️ **Motor de Segurança** - Detecção de segurança na entrada e saída, cobrindo proteção contra injeção de prompt, mascaramento de PII e filtragem de informações sensíveis
- 📊 **Motor de Avaliação** - Avaliação de qualidade RAG no estilo Ragas (faithfulness/relevancy/precision/recall/tool accuracy)
- 🧠 **Sistema de Memória** - Memória de curto prazo (histórico de sessão Redis) + memória de longo prazo (armazenamento vetorial + extração de tópicos + compressão de resumos)
- 🔌 **Serviço MCP** - Exponha capacidades da plataforma via Model Context Protocol
- 👥 **Multi-Tenancy** - Isolamento completo de tenants, sistema de permissões RBAC, gerenciamento de departamentos e tokens API
- 📝 **Auditoria e Monitoramento** - Logs de operação, auditoria de chamadas API, rastreamento de uso de modelos e rate limiting

---

## Início Rápido

### Pré-requisitos

- Docker & Docker Compose
- Pelo menos 8GB de RAM disponível (Milvus + Elasticsearch requerem mais recursos)

### 1. Clone e Configure

```bash
git clone <repository-url>
cd agent-engine-platform

# Copie as variáveis de ambiente e modifique as configurações necessárias
cp .env.example .env
# Edite o .env, configure pelo menos:
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (obrigatório alterar em produção)
```

### 2. Inicie Todos os Serviços

```bash
# Início completo (toda infraestrutura + serviços de aplicação)
docker compose --profile full up -d

# Ou use banco de dados externo (inicie apenas aplicação + Neo4j)
docker compose --profile external-db up -d
```

### 3. Acesse

| Serviço | URL | Descrição |
|---------|-----|-----------|
| Frontend | http://localhost:3000 | Interface de gerenciamento Next.js |
| Backend API | http://localhost:8000 | Serviço FastAPI |
| Documentação API | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | Ponto de entrada unificado |
| Neo4j Browser | http://localhost:7474 | Console do banco de dados de grafos |

### 4. Desenvolvimento Local (sem Docker)

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

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Proxy Reverso)                │
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
             │  BD Primário│    │  Cache/Fila Msg │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│   DB    │  │  Busca Full  │ │ DB Grafos│
│ Vetorial│  │    -Text     │ │         │
└─────────┘  └─────────────┘ └─────────┘
```

### Fluxo de Dados

1. **Requisição do Usuário** → Nginx → Frontend (SSR/CSR) ou Backend API
2. **Requisição de Chat** → Backend → Motor de Segurança (detecção de entrada) → Roteamento de Modelo → LLM → Motor de Segurança (detecção de saída) → Streaming SSE
3. **Requisição RAG** → Motor de Conhecimento → Parsing de Documento → Chunking → Embedding → Armazenamento (Milvus/ES/Neo4j) → Recuperação → Rerank → Geração
4. **Tarefas Assíncronas** → Backend → Celery Worker (processamento de documentos, treinamento de modelos, limpeza agendada)
5. **Execução de Workflow** → Motor de Workflow → Escalonamento DAG → Execução de nós → Aprovação humana → Saída de resultados

---

## Módulos de Motores

### Motor de Modelo

Camada de adaptação unificada para LLMs com suporte a múltiplos provedores:

| Adaptador | Modelos Suportados | Capacidades |
|-----------|-------------------|-------------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama (modelos locais) | Chat / Streaming |

Recursos principais: **ModelRouter** (balanceamento de carga multi-provedor), **CircuitBreaker** (padrão circuit breaker), **CostTracker** (rastreamento de uso de tokens e cálculo de custos), **Multimodal** (adaptadores ASR/TTS/OCR/Vision)

### Motor de Conhecimento

Pipeline RAG completo, do documento à resposta:

```
Upload de Documento → Parsing (PDF/Word/Excel/PPT/TXT) → Chunking Inteligente → Embedding
    → Armazenamento (Milvus + ES + Neo4j) → Recuperação (Vetorial/Full-text/Grafo/LightRAG) → Rerank → Geração
```

**Modos de Recuperação LightRAG:**

| Modo | Descrição | Cenário de Uso |
|------|-----------|----------------|
| `naive` | Similaridade vetorial pura | Q&A geral |
| `local` | Foco em entidades — extrai nomes específicos para buscar nós no grafo | Consultas factuais precisas |
| `global` | Foco em tópicos — extrai conceitos amplos para buscar arestas de关系 | Análise macro |
| `hybrid` | Fusão ponderada RRF de local + global | Consultas complexas e abrangentes |

### Motor de Workflow

Orquestração de workflows DAG com suporte aos seguintes tipos de nós:

| Tipo de Nó | Descrição |
|------------|-----------|
| `llm` | Nó de chamada LLM |
| `condition` | Ramificação condicional |
| `parallel` | Execução paralela |
| `loop` | Execução em loop |
| `http` | Requisição HTTP |
| `code` | Sandbox de código Python (isolamento de recursos) |
| `human` | Aprovação humana |
| `sub_workflow` | Chamada de sub-workflow |

Recursos: controle de timeout global, rastreamento de execução por nó, snapshots de variáveis e logs de execução detalhados.

### Motor Multi-Agent

**Modo Crew**: Colaboração em equipe de múltiplos Agentes
- Sequential (execução sequencial), Hierarchical (gerenciamento hierárquico), Parallel (execução paralela), Consensus (decisão por consenso)

**Modo Handoff**: Handoff estruturado entre Agentes
- Protocolo `HandoffMessage` baseado em Pydantic
- `HandoffTracker` para rastrear estado do handoff e número de hops

### Motor de Ferramentas

Ferramentas integradas:

| Ferramenta | Função |
|------------|--------|
| `calculator` | Cálculo de expressões matemáticas |
| `code_executor` | Execução de código Python em sandbox |
| `db_query` | Consulta a banco de dados (parametrizada) |
| `file_ops` | Operações de leitura/escrita de arquivos |
| `http_request` | Requisição HTTP |
| `web_search` | Pesquisa na web |

Suporte a registro dinâmico de ferramentas customizadas via `ToolRegistry`.

### Motor de Segurança

Proteção de segurança em quatro camadas:
1. **Detecção de Injeção de Prompt** - Correspondência regex + análise semântica
2. **Mascaramento de PII** - Identificação e mascaramento automático de RG, telefone, email, cartão bancário, etc.
3. **Filtragem de Informações Sensíveis** - Níveis de sensibilidade configuráveis (low/medium/high)
4. **Verificação de Conformidade** - Políticas de conformidade opcionais

### Motor de Memória

- **ShortTermMemory** - Histórico de sessão baseado em Redis com suporte a TTL e limite máximo de mensagens
- **LongTermMemory** - Compressão de resumo de conversas + extração de tópicos + armazenamento vetorial com suporte a recuperação跨sessão

### Motor de Avaliação

Avaliação de qualidade RAG no estilo Ragas com 5 métricas principais:
- `faithfulness` - A resposta é fiel ao contexto recuperado?
- `answer_relevancy` - A resposta é relevante para a pergunta?
- `context_precision` - Qualidade de排序 dos resultados de recuperação
- `context_recall` - A recuperação cobre todas as informações necessárias?
- `tool_call_accuracy` - A chamada de ferramenta está correta?

---

## Visão Geral da API

Prefixo de todas as rotas API: `/api/v1`

| Módulo | Rota | Descrição |
|--------|------|-----------|
| Auth | `/auth/*` | Login, registro, refresh de token |
| Agents | `/agents/*` | CRUD de Agentes, publicação |
| Chat | `/chat/*` | Chat (streaming SSE) |
| Conversations | `/conversations/*` | Gerenciamento de conversas |
| Knowledge | `/knowledge/*` | Base de conhecimento, upload de documentos, recuperação |
| Models | `/models/*` | Configuração de provedores de modelos |
| Workflows | `/workflows/*` | CRUD de workflows, execução |
| Tools | `/tools/*` | Gerenciamento de ferramentas |
| Multi-Agent | `/multi-agent/*` | Orquestração multi-Agent |
| Memory | `/memory/*` | Gerenciamento de memória |
| Evaluations | `/evaluations/*` | Avaliação RAG |
| Triggers | `/triggers/*` | Triggers Cron / Evento / Webhook |
| Webhooks | `/webhooks/*` | Gerenciamento de endpoints Webhook |
| Audit | `/audit/*` | Consulta de logs de auditoria |
| Usage | `/usage/*` | Estatísticas de uso de modelos |
| Users | `/users/*` | Gerenciamento de usuários |
| Roles | `/roles/*` | Gerenciamento de permissões de papéis |
| Tenants | `/tenants/*` | Gerenciamento de tenants |
| Tokens | `/tokens/*` | Gerenciamento de tokens API |
| Feedbacks | `/feedbacks/*` | Feedback dos usuários |
| Tasks | `/tasks/*` | Status de tarefas Celery |

**Health Check**: `GET /health` — Retorna status de conexão do banco de dados e Redis.

---

## Configuração

Todas as configurações são gerenciadas via variáveis de ambiente, consulte `.env.example`.

### Configurações Obrigatórias em Produção

| Configuração | Descrição |
|--------------|-----------|
| `DB_PASSWORD` | Senha root do MySQL |
| `REDIS_PASSWORD` | Senha de autenticação do Redis |
| `NEO4J_PASSWORD` | Senha de autenticação do Neo4j |
| `SECRET_KEY` | Chave de assinatura JWT (≥16 caracteres) |
| `ENCRYPTION_KEY` | Chave de criptografia de dados (≥16 caracteres) |

### Parâmetros Ajustáveis Importantes

| Configuração | Padrão | Descrição |
|--------------|--------|-----------|
| `DB_POOL_SIZE` | 10 | Tamanho do pool de conexões do banco de dados |
| `RATE_LIMIT_PER_MINUTE` | 60 | Rate limit da API |
| `CELERY_WORKER_CONCURRENCY` | 4 | Concorrência do Celery Worker |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | Timeout global do workflow (segundos) |
| `MAX_UPLOAD_SIZE_MB` | 50 | Limite de tamanho de upload de arquivo (MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | Toggle de detecção de segurança na entrada |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | Toggle de detecção de segurança na saída |

---

## Guia de Deploy

### Deploy com Docker (Recomendado)

```bash
# 1. Configure as variáveis de ambiente
cp .env.example .env
vim .env  # Modifique todos os itens marcados com <PRODUCTION>

# 2. Gere chaves de segurança
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Inicie
docker compose --profile full up -d

# 4. Visualize os logs
docker compose logs -f backend
```

### Configuração HTTPS do Nginx

Edite `nginx/nginx.conf`, descomente o bloco de servidor HTTPS e coloque os certificados no diretório `nginx/ssl/`:

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### Modo de Banco de Dados Externo

Se MySQL / Redis / Milvus / ES são fornecidos por serviços externos, configure as URLs de conexão correspondentes no `.env` e então:

```bash
docker compose --profile external-db up -d
```

---

## Stack Tecnológico

### Backend

| Tecnologia | Uso |
|------------|-----|
| Python 3.11 | Runtime |
| FastAPI | Framework Web |
| SQLAlchemy 2.0 + aiomysql | ORM assíncrono |
| Pydantic 2.0 | Validação de dados |
| Celery + Redis | Fila de tarefas assíncronas |
| Alembic | Migrações de banco de dados |
| python-jose | Autenticação JWT |
| httpx | Cliente HTTP assíncrono |
| sse-starlette | Resposta de streaming SSE |
| pymilvus | Cliente do banco de dados vetorial Milvus |
| neo4j | Driver do banco de dados de grafos Neo4j |
| elasticsearch | Cliente ES |
| minio | Cliente de armazenamento de objetos |

### Frontend

| Tecnologia | Uso |
|------------|-----|
| Next.js 14 | Framework React (App Router) |
| React 18 | Biblioteca UI |
| TypeScript 5 | Type safety |
| Ant Design 5 | Biblioteca de componentes UI |
| Tailwind CSS 3 | Estilos |
| Zustand | Gerenciamento de estado |
| Axios | Cliente HTTP |
| ECharts | Visualização de dados |
| React Markdown | Renderização Markdown |
| Jest + Testing Library | Testes |

### Infraestrutura

| Tecnologia | Uso |
|------------|-----|
| Docker Compose | Orquestração de serviços |
| MySQL 8.0 | Banco de dados primário |
| Redis 7 | Cache + fila de mensagens |
| Milvus 2.4 | Banco de dados vetorial |
| Neo4j 5 | Banco de dados de grafos |
| Elasticsearch 8.12 | Busca full-text |
| Nginx | Proxy reverso + rate limiting |
| MinIO | Armazenamento de objetos (opcional) |

---

## Estrutura do Projeto

```
agent-engine-platform/
├── backend/                        # Backend Python (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # Rotas RESTful API (20+ módulos)
│   │   ├── core/                   # Infraestrutura核心
│   │   ├── engines/                # Módulos de motores核心
│   │   ├── models/                 # Modelos ORM SQLAlchemy
│   │   ├── schemas/                # Schemas Pydantic请求/resposta
│   │   ├── tasks/                  # Tarefas assíncronas Celery
│   │   ├── mcp/                    # Servidor MCP
│   │   └── main.py                 # Ponto de entrada da aplicação FastAPI
│   ├── tests/                      # Testes (unit / integration)
│   ├── alembic/                    # Migrações de banco de dados
│   └── Dockerfile
├── frontend/                       # Frontend TypeScript (Next.js 14)
│   ├── src/
│   │   ├── app/                    # Páginas do App Router
│   │   ├── components/             # Componentes React
│   │   ├── lib/                    # Cliente API
│   │   ├── store/                  # Gerenciamento de estado Zustand
│   │   └── types/                  # Definições de tipos TypeScript
│   └── Dockerfile
├── nginx/                          # Configuração do proxy reverso Nginx
├── scripts/                        # Scripts de inicialização do banco de dados SQL
├── docs/                           # Documentação
├── docker-compose.yml              # Orquestração de todos os serviços
├── .env.example                    # Template de variáveis de ambiente
└── AGENTS.md                       # Regras de agentes automatizados
```

---

## Desenvolvimento e Testes

### Testes do Backend

```bash
cd backend

# Execute todos os testes
pytest

# Apenas testes unitários
pytest tests/unit -v

# Apenas testes de integração
pytest tests/integration -v

# Migrações de banco de dados
alembic upgrade head

# Gere migração
alembic revision --autogenerate -m "description"
```

### Desenvolvimento do Frontend

```bash
cd frontend

npm install        # Instale dependências
npm run dev        # Inicie servidor de desenvolvimento (:3000)
npm run build      # Build de produção
npm test           # Execute testes (Jest)
npm run lint       # Verificação ESLint
```

### Padrões de Código

| Camada | Padrão |
|--------|--------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + indentação de 2 espaços |
| Nomenclatura | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| Commits | Conventional Commits (`feat(scope): description`) |

---

## License

Private / Proprietary

---

## Suporte

- **Documentação**: [docs/](../../docs/)
- **Reportar Problemas**: [GitHub Issues](https://github.com/your-org/agent-engine-platform/issues)
- **Repositório**: [github.com/your-org/agent-engine-platform](https://github.com/your-org/agent-engine-platform)

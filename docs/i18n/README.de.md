<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">Die All-in-One-Plattform für den Aufbau, die Verwaltung und Orchestrierung von KI-Agenten.</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.es.md">🇪🇸 Español</a> •
  <a href="README.pt.md">🇵🇹 Português</a> •
  <a href="README.ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <a href="../../LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Lizenz">
  </a>
  <a href="../../backend/requirements.txt">
    <img src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" alt="Python">
  </a>
  <a href="../../frontend/package.json">
    <img src="https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg" alt="Node">
  </a>
</p>

<p align="center">
  <a href="#schnellstart">Schnellstart</a> •
  <a href="#kernfunktionen">Kernfunktionen</a> •
  <a href="#systemarchitektur">Systemarchitektur</a> •
  <a href="#engine-module">Engine-Module</a> •
  <a href="#api-übersicht">API</a> •
  <a href="#konfiguration">Konfiguration</a> •
  <a href="#bereitstellung">Bereitstellung</a> •
  <a href="#technologie-Stack">Technologie-Stack</a>
</p>

---

## Überblick

Agent Engine Platform ist eine Full-Stack-Plattform für intelligente Agenten-Anwendungen, die umfassende Fähigkeiten von der Agent-Erstellung über Wissensmanagement und Workflow-Orchestrierung bis hin zu Multi-Agent-Kollaboration und Sicherheitsaudits bietet.

**Backend**: FastAPI + Python 3.11  
**Frontend**: Next.js 14 + React 18 + Ant Design  
**Infrastruktur**: Docker Compose Orchestrierung

---

## Kernfunktionen

- 🤖 **Agent-Verwaltung** - Erstellen, konfigurieren und veröffentlichen von intelligenten Agenten mit Modellauswahl, System-Prompts, Tool-Binding und Wissensdatenbank-Verknüpfung
- 🔀 **Multi-Model-Routing** - Einheitliche Anbindung an OpenAI / Anthropic / Ollama und weitere LLM-Anbieter mit Load-Balancing, Circuit-Breaker und Kostenverfolgung
- 📚 **Wissens-Engine** - Vollständige RAG-Pipeline mit Dokumentenparsung (PDF/Word/Excel/PPT), intelligentem Chunking, Vektorsuche (Milvus), Volltextsuche (ES), Graphsuche (Neo4j) und LightRAG-Zweistufen-Suche
- ⚡ **Workflow-Engine** - Visuelle DAG-Orchestrierung mit LLM-Nodes, bedingten Verzweigungen, paralleler Ausführung, Schleifen, HTTP-Aufrufen, Code-Sandbox, manueller Genehmigung und Unter-Workflows
- 🤝 **Multi-Agent-Kollaboration** - Crew-Modus (sequenziell/hierarchisch/parallel/Konsens) und Handoff-Routing-Protokoll
- 🔧 **Tool-Engine** - Integrierte Tools: Taschenrechner, Code-Ausführung, Datenbankabfragen, Dateioperationen, HTTP-Anfragen, Websuche; unterstützt benutzerdefinierte Tool-Registrierung
- 🛡️ **Sicherheits-Engine** - Ein-/Ausgabe-Sicherheitsprüfung mit Prompt-Injection-Schutz, PII-Anonymisierung und sensibler Informationsfilterung
- 📊 **Evaluierungs-Engine** - Ragas-Style RAG-Qualitätsbewertung (Faithfulness/Relevancy/Precision/Recall/Tool-Accuracy)
- 🧠 **Gedächtnissystem** - Kurzzeitgedächtnis (Redis-Sitzungshistorie) + Langzeitgedächtnis (Vektorspeicher + Themenextraktion + Zusammenfassungskomprimierung)
- 🔌 **MCP-Dienst** - Plattformfähigkeiten über Model Context Protocol bereitstellen
- 👥 **Mandantenfähigkeit** - Vollständige Mandantenisolation, RBAC-Berechtigungssystem, Abteilungsverwaltung und API-Token-Verwaltung
- 📝 **Audit & Monitoring** - Operations-Logs, API-Aufruf-Audits, Modellnutzungsverfolgung, Rate-Limiting

---

## Schnellstart

### Voraussetzungen

- Docker & Docker Compose
- Mindestens 8 GB verfügbarer Speicher (Milvus + Elasticsearch benötigen erhebliche Ressourcen)

### 1. Klonen und konfigurieren

```bash
git clone <repository-url>
cd agent-engine-platform

# Umgebungsvariablen kopieren und notwendige Konfiguration anpassen
cp .env.example .env
# .env bearbeiten, mindestens folgende Werte setzen:
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (müssen in Produktion geändert werden)
```

### 2. Alle Dienste starten

```bash
# Vollständiger Start (alle Infrastruktur- + Anwendungsdienste)
docker-compose --profile full up -d

# Oder mit externer Datenbank (nur Anwendung + Neo4j starten)
docker-compose --profile external-db up -d
```

### 3. Zugriff

| Dienst | Adresse | Beschreibung |
|--------|---------|--------------|
| Frontend | http://localhost:3000 | Next.js-Verwaltungsoberfläche |
| Backend API | http://localhost:8000 | FastAPI-Dienst |
| API-Dokumentation | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | Einheitlicher Einstiegspunkt |
| Neo4j Browser | http://localhost:7474 | Graphdatenbank-Konsole |

### 4. Lokale Entwicklung (ohne Docker)

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

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse-Proxy)                    │
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
             │  Primär-DB  │    │  Cache/Queue    │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│  Vektor-│  │  Volltext-   │ │  Graph- │
│   DB    │  │   suchmaschine│ │   DB    │
└─────────┘  └─────────────┘ └─────────┘
```

### Datenfluss

1. **Benutzeranfrage** → Nginx → Frontend (SSR/CSR) oder Backend API
2. **Chat-Anfrage** → Backend → Sicherheits-Engine (Eingabeprüfung) → Model-Routing → LLM → Sicherheits-Engine (Ausgabeprüfung) → SSE-Streaming-Antwort
3. **RAG-Anfrage** → Wissens-Engine → Dokumentenparsung → Chunking → Embedding → Speicherung (Milvus/ES/Neo4j) → Suche → Rerank → Generierung
4. **Asynchrone Aufgaben** → Backend → Celery Worker (Dokumentenverarbeitung, Modelltraining, geplante Bereinigung)
5. **Workflow-Ausführung** → Workflow-Engine → DAG-Scheduling → Node-Ausführung → Manuelle Genehmigung → Ergebnisausgabe

---

## Engine-Module

### Model-Engine

Einheitliche LLM-Anbindungsschicht mit Unterstützung für mehrere Anbieter:

| Adapter | Unterstützte Modelle | Fähigkeiten |
|---------|---------------------|-------------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama (lokale Modelle) | Chat / Streaming |

Kernfunktionen: **ModelRouter** (Multi-Provider Load-Balancing), **CircuitBreaker** (Circuit-Breaker-Pattern), **CostTracker** (Token-Nutzungsverfolgung & Kostenberechnung), **Multimodal** (ASR/TTS/OCR/Vision-Adapter)

### Wissens-Engine

Vollständige RAG-Pipeline, vom Dokument zur Antwort:

```
Dokument-Upload → Parsung (PDF/Word/Excel/PPT/TXT) → Intelligentes Chunking → Embedding
    → Speicherung (Milvus + ES + Neo4j) → Suche (Vektor/Volltext/Graph/LightRAG) → Rerank → Generierung
```

**LightRAG-Suchmodi:**

| Modus | Beschreibung | Anwendungsfall |
|-------|--------------|----------------|
| `naive` | Reine Vektorähnlichkeit | Allgemeine Frage-Antwort |
| `local` | Entitätsfokussiert — Extrahiert spezifische Namen zur Suche in Graphnodes | Präzise Faktenabfragen |
| `global` | Themenfokussiert — Extrahiert breite Konzepte zur Suche in Beziehungskanten | Makroanalysen |
| `hybrid` | local + global gewichtete RRF-Fusion | Komplexe umfassende Abfragen |

### Workflow-Engine

DAG-Workflow-Orchestrierung mit folgenden Node-Typen:

| Node-Typ | Beschreibung |
|----------|--------------|
| `llm` | LLM-Aufruf-Node |
| `condition` | Bedingte Verzweigung |
| `parallel` | Parallele Ausführung |
| `loop` | Schleifenausführung |
| `http` | HTTP-Anfrage |
| `code` | Python-Code-Sandbox (Ressourcenisolierung) |
| `human` | Manuelle Genehmigung |
| `sub_workflow` | Unter-Workflow-Aufruf |

Funktionen: Globale Timeout-Steuerung, node-spezifische Ausführungsverfolgung, Variablen-Snapshots, detaillierte Ausführungsprotokolle.

### Multi-Agent-Engine

**Crew-Modus**: Multi-Agent-Teamkollaboration
- Sequenziell, Hierarchisch, Parallel, Konsens

**Handoff-Modus**: Strukturierte Übergabe zwischen Agenten
- Pydantic-basiertes `HandoffMessage`-Protokoll
- `HandoffTracker` zur Verfolgung von Übergabezustand und Hop-Anzahl

### Tool-Engine

Integrierte Toolsammlung:

| Tool | Funktion |
|------|----------|
| `calculator` | Mathematische Ausdrucksberechnung |
| `code_executor` | Python-Code-Sandbox-Ausführung |
| `db_query` | Datenbankabfrage (parametrisiert) |
| `file_ops` | Datei-Lese-/Schreiboperationen |
| `http_request` | HTTP-Anfrage |
| `web_search` | Websuche |

Unterstützt dynamische Registrierung benutzerdefinierter Tools über `ToolRegistry`.

### Sicherheits-Engine

Vierstufiger Sicherheitsschutz:
1. **Prompt-Injection-Erkennung** - Regex-Matching + semantische Analyse
2. **PII-Anonymisierung** - Automatische Erkennung und Anonymisierung von Personalausweisen, Telefonnummern, E-Mails, Bankkonten usw.
3. **Sensible Informationsfilterung** - Konfigurierbare Sensibilitätsstufen (low/medium/high)
4. **Compliance-Prüfung** - Optionale Compliance-Richtlinien-Schalter

### Gedächtnis-Engine

- **ShortTermMemory** - Redis-basierte Sitzungshistorie mit TTL und maximaler Nachrichtenanzahl
- **LongTermMemory** - Dialogzusammenfassungskomprimierung + Themenextraktion + Vektorspeicherung mit abfrageübergreifender Suche

### Evaluierungs-Engine

Ragas-Style RAG-Qualitätsbewertung mit 5 Kernindikatoren:
- `faithfulness` - Ob die Antwort dem abgerufenen Kontext treu ist
- `answer_relevancy` - Relevanz der Antwort für die Frage
- `context_precision` - Sortierqualität der Suchergebnisse
- `context_recall` - Ob die Suche alle erforderlichen Informationen abdeckt
- `tool_call_accuracy` - Korrektheit der Tool-Aufrufe

---

## API-Übersicht

Alle API-Routen-Präfix: `/api/v1`

| Modul | Route | Beschreibung |
|-------|-------|--------------|
| Auth | `/auth/*` | Login, Registrierung, Token-Aktualisierung |
| Agents | `/agents/*` | Agent CRUD, Veröffentlichung |
| Chat | `/chat/*` | Dialog (SSE-Streaming) |
| Conversations | `/conversations/*` | Sitzungsverwaltung |
| Knowledge | `/knowledge/*` | Wissensdatenbank, Dokumentenupload, Suche |
| Models | `/models/*` | Modellanbieter-Konfiguration |
| Workflows | `/workflows/*` | Workflow CRUD, Ausführung |
| Tools | `/tools/*` | Tool-Verwaltung |
| Multi-Agent | `/multi-agent/*` | Multi-Agent-Orchestrierung |
| Memory | `/memory/*` | Gedächtnisverwaltung |
| Evaluations | `/evaluations/*` | RAG-Evaluierung |
| Triggers | `/triggers/*` | Cron / Event / Webhook-Trigger |
| Webhooks | `/webhooks/*` | Webhook-Endpunktverwaltung |
| Audit | `/audit/*` | Audit-Log-Abfrage |
| Usage | `/usage/*` | Modellnutzungsstatistiken |
| Users | `/users/*` | Benutzerverwaltung |
| Roles | `/roles/*` | Rollenberechtigungsverwaltung |
| Tenants | `/tenants/*` | Mandantenverwaltung |
| Tokens | `/tokens/*` | API-Token-Verwaltung |
| Feedbacks | `/feedbacks/*` | Benutzerfeedback |
| Tasks | `/tasks/*` | Celery-Aufgabenstatus |

**Health-Check**: `GET /health` — Gibt den Datenbank- und Redis-Verbindungsstatus zurück.

---

## Konfiguration

Alle Konfigurationen werden über Umgebungsvariablen verwaltet, siehe `.env.example`.

### In Produktion zwingend zu ändernde Konfigurationen

| Konfiguration | Beschreibung |
|---------------|--------------|
| `DB_PASSWORD` | MySQL Root-Passwort |
| `REDIS_PASSWORD` | Redis-Authentifizierungspasswort |
| `NEO4J_PASSWORD` | Neo4j-Authentifizierungspasswort |
| `SECRET_KEY` | JWT-Signaturschlüssel (≥16 Zeichen) |
| `ENCRYPTION_KEY` | Datenverschlüsselungsschlüssel (≥16 Zeichen) |

### Wichtige anpassbare Parameter

| Konfiguration | Standardwert | Beschreibung |
|---------------|--------------|--------------|
| `DB_POOL_SIZE` | 10 | Datenbank-Verbindungspool-Größe |
| `RATE_LIMIT_PER_MINUTE` | 60 | API-Rate-Limit |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery Worker-Nebenläufigkeit |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | Workflow-Global-Timeout (Sekunden) |
| `MAX_UPLOAD_SIZE_MB` | 50 | Dateiupload-Größenlimit (MB) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | Eingabe-Sicherheitsprüfung Schalter |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | Ausgabe-Sicherheitsprüfung Schalter |

---

## Bereitstellung

### Docker-Bereitstellung (empfohlen)

```bash
# 1. Umgebungsvariablen konfigurieren
cp .env.example .env
vim .env  # Alle mit <PRODUCTION> markierten Werte ändern

# 2. Sichere Schlüssel generieren
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Starten
docker-compose --profile full up -d

# 4. Logs anzeigen
docker-compose logs -f backend
```

### Nginx HTTPS-Konfiguration

Bearbeiten Sie `nginx/nginx.conf`, kommentieren Sie den HTTPS-Server-Block aus und legen Sie die Zertifikate im Verzeichnis `nginx/ssl/` ab:

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### Externer Datenbankmodus

Wenn MySQL / Redis / Milvus / ES von externen Diensten bereitgestellt werden, konfigurieren Sie die entsprechenden Verbindungs-URLs in `.env` und führen Sie dann aus:

```bash
docker-compose --profile external-db up -d
```

---

## Technologie-Stack

### Backend

| Technologie | Verwendung |
|-------------|------------|
| Python 3.11 | Laufzeitumgebung |
| FastAPI | Web-Framework |
| SQLAlchemy 2.0 + aiomysql | Async ORM |
| Pydantic 2.0 | Datenvalidierung |
| Celery + Redis | Asynchroner Aufgaben-Queue |
| Alembic | Datenbankmigration |
| python-jose | JWT-Authentifizierung |
| httpx | Async HTTP-Client |
| sse-starlette | SSE-Streaming-Antwort |
| pymilvus | Milvus-Vektordatenbank-Client |
| neo4j | Neo4j-Graphdatenbank-Treiber |
| elasticsearch | ES-Client |
| minio | Objektspeicher-Client |

### Frontend

| Technologie | Verwendung |
|-------------|------------|
| Next.js 14 | React-Framework (App Router) |
| React 18 | UI-Bibliothek |
| TypeScript 5 | Typsicherheit |
| Ant Design 5 | UI-Komponentenbibliothek |
| Tailwind CSS 3 | Styling |
| Zustand | State Management |
| Axios | HTTP-Client |
| ECharts | Datenvisualisierung |
| React Markdown | Markdown-Rendering |
| Jest + Testing Library | Tests |

### Infrastruktur

| Technologie | Verwendung |
|-------------|------------|
| Docker Compose | Dienstorchestrierung |
| MySQL 8.0 | Primärdatenbank |
| Redis 7 | Cache + Nachrichtenwarteschlange |
| Milvus 2.4 | Vektordatenbank |
| Neo4j 5 | Graphdatenbank |
| Elasticsearch 8.12 | Volltextsuche |
| Nginx | Reverse-Proxy + Rate-Limiting |
| MinIO | Objektspeicher (optional) |

---

## Projektstruktur

```
agent-engine-platform/
├── backend/                        # Python-Backend (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # RESTful API-Routen (20+ Module)
│   │   ├── core/                   # Kerninfrastruktur
│   │   ├── engines/                # Kern-Engine-Module
│   │   ├── models/                 # SQLAlchemy ORM-Modelle
│   │   ├── schemas/                # Pydantic Request/Response Schemas
│   │   ├── tasks/                  # Celery asynchrone Aufgaben
│   │   ├── mcp/                    # MCP-Server
│   │   └── main.py                 # FastAPI-Anwendungseinstieg
│   ├── tests/                      # Tests (unit / integration)
│   ├── alembic/                    # Datenbankmigrationen
│   └── Dockerfile
├── frontend/                       # TypeScript-Frontend (Next.js 14)
│   ├── src/
│   │   ├── app/                    # App Router-Seiten
│   │   ├── components/             # React-Komponenten
│   │   ├── lib/                    # API-Client
│   │   ├── store/                  # Zustand State Management
│   │   └── types/                  # TypeScript-Typdefinitionen
│   └── Dockerfile
├── nginx/                          # Nginx Reverse-Proxy-Konfiguration
├── scripts/                        # Datenbankinitialisierungs-SQL
├── docs/                           # Dokumentation
├── docker-compose.yml              # Alle Dienste orchestriert
├── .env.example                    # Umgebungsvariablen-Vorlage
└── AGENTS.md                       # Automatisierungsagenten-Regeln
```

---

## Entwicklung & Tests

### Backend-Tests

```bash
cd backend

# Alle Tests ausführen
pytest

# Nur Unit-Tests
pytest tests/unit -v

# Nur Integrationstests
pytest tests/integration -v

# Datenbankmigrationen
alembic upgrade head

# Migration generieren
alembic revision --autogenerate -m "Beschreibung"
```

### Frontend-Entwicklung

```bash
cd frontend

npm install        # Abhängigkeiten installieren
npm run dev        # Entwicklungsserver starten (:3000)
npm run build      # Produktionsbuild
npm test           # Tests ausführen (Jest)
npm run lint       # ESLint-Prüfung
```

### Codierkonventionen

| Ebene | Konvention |
|-------|------------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-Space-Einzug |
| Benennung | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| Commits | Conventional Commits (`feat(scope): Beschreibung`) |

---

## License

Dieses Projekt ist unter der Apache License 2.0 lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

---

## Beiträge

Beiträge sind willkommen! Bitte zögern Sie nicht, eine Pull Request einzureichen.

1. Forken Sie das Repository
2. Erstellen Sie Ihren Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Commiten Sie Ihre Änderungen (`git commit -m 'feat: add amazing feature'`)
4. Pushen Sie zum Branch (`git push origin feature/amazing-feature`)
5. Erstellen Sie eine Pull Request

---

## Support

- **Dokumentation**: [docs/](../../docs/)
- **Problemfeedback**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **Repository**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

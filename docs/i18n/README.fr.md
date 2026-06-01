<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">Plateforme complète de création, gestion et orchestration d'agents IA.</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ja.md">🇯🇵 日本語</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
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
  <a href="#démarrage-rapide">Démarrage rapide</a> •
  <a href="#capacités-clés">Capacités clés</a> •
  <a href="#architecture-système">Architecture</a> •
  <a href="#modules-moteurs">Moteurs</a> •
  <a href="#vue-densemble-api">API</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#guide-de-déploiement">Déploiement</a> •
  <a href="#stack-technologique">Stack</a>
</p>

---

## Vue d'ensemble

Agent Engine Platform est une plateforme complète d'applications d'agents intelligents, offrant des capacités allant de la création d'agents à la gestion des bases de connaissances, l'orchestration de workflows, la collaboration multi-agents et l'audit de sécurité.

**Backend** : FastAPI + Python 3.11  
**Frontend** : Next.js 14 + React 18 + Ant Design  
**Infrastructure** : Orchestration Docker Compose

---

## Capacités clés

- 🤖 **Gestion des agents** - Création, configuration et publication d'agents intelligents avec sélection de modèles, prompts système, liaison d'outils et association de bases de connaissances
- 🔀 **Routage multi-modèles** - Adaptation unifiée à plusieurs fournisseurs LLM (OpenAI / Anthropic / Ollama), avec équilibrage de charge, disjoncteur et suivi des coûts
- 📚 **Moteur de connaissances** - Pipeline RAG complet avec analyse de documents (PDF/Word/Excel/PPT), découpage intelligent, recherche vectorielle (Milvus), recherche plein texte (ES), recherche par graphe (Neo4j) et recherche bi-niveau LightRAG
- ⚡ **Moteur de workflow** - Orchestration DAG visuelle avec nœuds LLM, branches conditionnelles, exécution parallèle, boucles, appels HTTP, bac de code, approbation humaine et sous-workflows
- 🤝 **Collaboration multi-agents** - Mode Crew (séquentiel/hiéralarchique/parallèle/consensus) et protocole de routage Handoff
- 🔧 **Moteur d'outils** - Calculatrice intégrée, exécuteur de code, requêtes base de données, opérations fichiers, requêtes HTTP, recherche web, support de l'enregistrement d'outils personnalisés
- 🛡️ **Moteur de sécurité** - Détection de sécurité entrée/sortie, couvrant la protection contre l'injection de prompts, le dé-identification PII, le filtrage d'informations sensibles
- 📊 **Moteur d'évaluation** - Évaluation de qualité RAG de style Ragas (fidélité/pertinence/précision/rappel/précision des appels d'outils)
- 🧠 **Système de mémoire** - Mémoire à court terme (historique des sessions Redis) + mémoire à long terme (stockage vectoriel + extraction de thèmes + résumé compressé)
- 🔌 **Service MCP** - Exposition des capacités de la plateforme via Model Context Protocol
- 👥 **Multi-tenants** - Isolation complète des tenants, système d'autorisations RBAC, gestion des départements et gestion des tokens API
- 📝 **Audit et surveillance** - Journaux d'opérations, audit des appels API, suivi de l'utilisation des modèles, limitation de débit

---

## Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Au moins 8 Go de mémoire disponible (Milvus + Elasticsearch nécessitent des ressources importantes)

### 1. Cloner et configurer

```bash
git clone <repository-url>
cd agent-engine-platform

# Copier les variables d'environnement et modifier les configurations nécessaires
cp .env.example .env
# Éditer .env, définir au minimum :
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY (doit être modifié pour la production)
```

### 2. Démarrer tous les services

```bash
# Démarrage complet (toute l'infrastructure + services applicatifs)
docker compose --profile full up -d

# Ou utiliser une base de données externe (uniquement application + Neo4j)
docker compose --profile external-db up -d
```

### 3. Accès

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Interface d'administration Next.js |
| Backend API | http://localhost:8000 | Service FastAPI |
| Documentation API | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | Point d'entrée unifié |
| Neo4j Browser | http://localhost:7474 | Console de base de données graphe |

### 4. Développement local (sans Docker)

**Backend :**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend :**

```bash
cd frontend
npm install
npm run dev
```

---

## Architecture système

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (proxy inverse)                   │
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
             │   Base de   │    │  Cache/Queue    │   │  Worker/Beat│
             │   données   │    │  de messages    │   │             │
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│  Base   │    │  Moteur de  │ │  Base   │
│vectorielle│  │recherche    │ │ graphe  │
└─────────┘  │  plein texte │ └─────────┘
             └─────────────┘
```

### Flux de données

1. **Requête utilisateur** → Nginx → Frontend (SSR/CSR) ou Backend API
2. **Requête de conversation** → Backend → Moteur de sécurité (détection entrée) → Routage modèle → LLM → Moteur de sécurité (détection sortie) → Retour en streaming SSE
3. **Requête RAG** → Moteur de connaissances → Analyse de documents → Découpage → Embedding → Stockage (Milvus/ES/Neo4j) → Recherche → Rerank → Génération
4. **Tâches asynchrones** → Backend → Celery Worker (traitement de documents, entraînement de modèles, nettoyage planifié)
5. **Exécution de workflow** → Moteur de workflow → Orchestration DAG → Exécution des nœuds → Approbation humaine → Sortie des résultats

---

## Modules moteurs

### Moteur de modèles

Couche d'adaptation LLM unifiée supportant plusieurs fournisseurs :

| Adaptateur | Modèles supportés | Capacités |
|------------|-------------------|-----------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama (modèles locaux) | Chat / Streaming |

Caractéristiques principales : **ModelRouter** (équilibrage de charge multi-Provider), **CircuitBreaker** (mode disjoncteur), **CostTracker** (suivi de l'utilisation des tokens et calcul des coûts), **Multimodal** (adaptateurs ASR/TTS/OCR/Vision)

### Moteur de connaissances

Pipeline RAG complet, du document à la réponse :

```
Upload de document → Analyse (PDF/Word/Excel/PPT/TXT) → Découpage intelligent → Embedding
    → Stockage (Milvus + ES + Neo4j) → Recherche (vectorielle/plein texte/graphe/LightRAG) → Rerank → Génération
```

**Modes de recherche LightRAG :**

| Mode | Description | Cas d'utilisation |
|------|-------------|-------------------|
| `naive` | Similarité vectorielle pure | Questions-réponses générales |
| `local` | Focus sur l'entité — extrait des noms spécifiques pour rechercher les nœuds du graphe | Requêtes de faits précis |
| `global` | Focus sur le thème — extrait des concepts larges pour rechercher les arêtes de relation | Analyse macro |
| `hybrid` | Fusion pondérée RRF de local + global | Requêtes complexes et complètes |

### Moteur de workflow

Orchestration de workflows DAG supportant les types de nœuds suivants :

| Type de nœud | Description |
|--------------|-------------|
| `llm` | Nœud d'appel LLM |
| `condition` | Branche conditionnelle |
| `parallel` | Exécution parallèle |
| `loop` | Exécution en boucle |
| `http` | Requête HTTP |
| `code` | Bac de code Python (isolation des ressources) |
| `human` | Approbation humaine |
| `sub_workflow` | Appel de sous-workflow |

Caractéristiques : contrôle de timeout global, suivi d'exécution au niveau des nœuds, snapshots de variables, journaux d'exécution détaillés.

### Moteur multi-agents

**Mode Crew** : Collaboration d'équipe multi-agents
- Sequential (exécution séquentielle), Hierarchical (gestion hiérarchique), Parallel (exécution parallèle), Consensus (décision par consensus)

**Mode Handoff** : Transfert structuré entre agents
- Protocole `HandoffMessage` basé sur Pydantic
- `HandoffTracker` pour suivre l'état du transfert et le nombre de sauts

### Moteur d'outils

Ensemble d'outils intégrés :

| Outil | Fonction |
|-------|----------|
| `calculator` | Calcul d'expressions mathématiques |
| `code_executor` | Exécution de code Python en bac de sable |
| `db_query` | Requêtes base de données (paramétrées) |
| `file_ops` | Opérations de lecture/écriture de fichiers |
| `http_request` | Requête HTTP |
| `web_search` | Recherche web |

Supporte l'enregistrement dynamique d'outils personnalisés via `ToolRegistry`.

### Moteur de sécurité

Protection de sécurité à quatre niveaux :
1. **Détection d'injection de prompts** - Correspondance regex + analyse sémantique
2. **Dé-identification PII** - Identification et dé-identification automatiques des cartes d'identité, numéros de téléphone, e-mails, cartes bancaires, etc.
3. **Filtrage d'informations sensibles** - Niveaux de sensibilité configurables (low/medium/high)
4. **Vérification de conformité** - Interrupteurs de politiques de conformité optionnels

### Moteur de mémoire

- **ShortTermMemory** - Historique des sessions basé sur Redis, supportant TTL et un nombre maximal de messages
- **LongTermMemory** - Résumé compressé de conversation + extraction de thèmes + stockage vectoriel, supportant la recherche inter-sessions

### Moteur d'évaluation

Évaluation de qualité RAG de style Ragas, 5 indicateurs principaux :
- `faithfulness` - La réponse est-elle fidèle au contexte récupéré
- `answer_relevancy` - Pertinence de la réponse par rapport à la question
- `context_precision` - Qualité du classement des résultats de recherche
- `context_recall` - La recherche couvre-t-elle toutes les informations nécessaires
- `tool_call_accuracy` - Exactitude des appels d'outils

---

## Vue d'ensemble API

Tous les préfixes de routes API : `/api/v1`

| Module | Route | Description |
|--------|-------|-------------|
| Auth | `/auth/*` | Connexion, inscription, rafraîchissement de token |
| Agents | `/agents/*` | CRUD agents, publication |
| Chat | `/chat/*` | Conversation (streaming SSE) |
| Conversations | `/conversations/*` | Gestion des sessions |
| Knowledge | `/knowledge/*` | Base de connaissances, upload de documents, recherche |
| Models | `/models/*` | Configuration des fournisseurs de modèles |
| Workflows | `/workflows/*` | CRUD workflows, exécution |
| Tools | `/tools/*` | Gestion des outils |
| Multi-Agent | `/multi-agent/*` | Orchestration multi-agents |
| Memory | `/memory/*` | Gestion de la mémoire |
| Evaluations | `/evaluations/*` | Évaluation RAG |
| Triggers | `/triggers/*` | Déclencheurs Cron / événement / Webhook |
| Webhooks | `/webhooks/*` | Gestion des points d'accès Webhook |
| Audit | `/audit/*` | Recherche de journaux d'audit |
| Usage | `/usage/*` | Statistiques d'utilisation des modèles |
| Users | `/users/*` | Gestion des utilisateurs |
| Roles | `/roles/*` | Gestion des rôles et autorisations |
| Tenants | `/tenants/*` | Gestion des tenants |
| Tokens | `/tokens/*` | Gestion des tokens API |
| Feedbacks | `/feedbacks/*` | Retours utilisateurs |
| Tasks | `/tasks/*` | État des tâches Celery |

**Vérification de santé** : `GET /health` — Retourne l'état de connexion de la base de données et de Redis.

---

## Configuration

Toute la configuration est gérée via les variables d'environnement, voir `.env.example`.

### Configurations à modifier obligatoirement pour la production

| Élément de configuration | Description |
|--------------------------|-------------|
| `DB_PASSWORD` | Mot de passe root MySQL |
| `REDIS_PASSWORD` | Mot de passe d'authentification Redis |
| `NEO4J_PASSWORD` | Mot de passe d'authentification Neo4j |
| `SECRET_KEY` | Clé de signature JWT (≥16 caractères) |
| `ENCRYPTION_KEY` | Clé de chiffrement des données (≥16 caractères) |

### Paramètres clés ajustables

| Élément de configuration | Valeur par défaut | Description |
|--------------------------|-------------------|-------------|
| `DB_POOL_SIZE` | 10 | Taille du pool de connexions à la base de données |
| `RATE_LIMIT_PER_MINUTE` | 60 | Limitation de débit API |
| `CELERY_WORKER_CONCURRENCY` | 4 | Concurrence des workers Celery |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | Timeout global du workflow (secondes) |
| `MAX_UPLOAD_SIZE_MB` | 50 | Limite de taille d'upload de fichier (Mo) |
| `SAFETY_INPUT_CHECK_ENABLED` | true | Interrupteur de détection de sécurité entrée |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | Interrupteur de détection de sécurité sortie |

---

## Guide de déploiement

### Déploiement Docker (recommandé)

```bash
# 1. Configurer les variables d'environnement
cp .env.example .env
vim .env  # Modifier tous les éléments marqués <PRODUCTION>

# 2. Générer des clés sécurisées
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Démarrer
docker compose --profile full up -d

# 4. Voir les journaux
docker compose logs -f backend
```

### Configuration HTTPS Nginx

Éditez `nginx/nginx.conf`, décommentez le bloc serveur HTTPS, placez les certificats dans le répertoire `nginx/ssl/` :

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### Mode base de données externe

Si MySQL / Redis / Milvus / ES sont fournis par des services externes, configurez les URL de connexion correspondantes dans `.env`, puis :

```bash
docker compose --profile external-db up -d
```

---

## Stack technologique

### Backend

| Technologie | Utilisation |
|-------------|-------------|
| Python 3.11 | Runtime |
| FastAPI | Framework web |
| SQLAlchemy 2.0 + aiomysql | ORM asynchrone |
| Pydantic 2.0 | Validation de données |
| Celery + Redis | File de tâches asynchrones |
| Alembic | Migrations de base de données |
| python-jose | Authentification JWT |
| httpx | Client HTTP asynchrone |
| sse-starlette | Réponses en streaming SSE |
| pymilvus | Client de base de données vectorielle Milvus |
| neo4j | Pilote de base de données graphe Neo4j |
| elasticsearch | Client ES |
| minio | Client de stockage d'objets |

### Frontend

| Technologie | Utilisation |
|-------------|-------------|
| Next.js 14 | Framework React (App Router) |
| React 18 | Bibliothèque UI |
| TypeScript 5 | Sécurité de type |
| Ant Design 5 | Bibliothèque de composants UI |
| Tailwind CSS 3 | Styles |
| Zustand | Gestion d'état |
| Axios | Client HTTP |
| ECharts | Visualisation de données |
| React Markdown | Rendu Markdown |
| Jest + Testing Library | Tests |

### Infrastructure

| Technologie | Utilisation |
|-------------|-------------|
| Docker Compose | Orchestration de services |
| MySQL 8.0 | Base de données principale |
| Redis 7 | Cache + file de messages |
| Milvus 2.4 | Base de données vectorielle |
| Neo4j 5 | Base de données graphe |
| Elasticsearch 8.12 | Recherche plein texte |
| Nginx | Proxy inverse + limitation de débit |
| MinIO | Stockage d'objets (optionnel) |

---

## Structure du projet

```
agent-engine-platform/
├── backend/                        # Backend Python (FastAPI)
│   ├── app/
│   │   ├── api/v1/                 # Routes API RESTful (20+ modules)
│   │   ├── core/                   # Infrastructure de base
│   │   ├── engines/                # Modules moteurs principaux
│   │   ├── models/                 # Modèles ORM SQLAlchemy
│   │   ├── schemas/                # Schémas Pydantic requête/réponse
│   │   ├── tasks/                  # Tâches asynchrones Celery
│   │   ├── mcp/                    # Serveur MCP
│   │   └── main.py                 # Point d'entrée de l'application FastAPI
│   ├── tests/                      # Tests (unitaire / intégration)
│   ├── alembic/                    # Migrations de base de données
│   └── Dockerfile
├── frontend/                       # Frontend TypeScript (Next.js 14)
│   ├── src/
│   │   ├── app/                    # Pages App Router
│   │   ├── components/             # Composants React
│   │   ├── lib/                    # Client API
│   │   ├── store/                  # Gestion d'état Zustand
│   │   └── types/                  # Définitions de types TypeScript
│   └── Dockerfile
├── nginx/                          # Configuration du proxy inverse Nginx
├── scripts/                        # SQL d'initialisation de la base de données
├── docs/                           # Documentation
├── docker-compose.yml              # Orchestration de tous les services
├── .env.example                    # Modèle de variables d'environnement
└── AGENTS.md                       # Règles d'agents automatisés
```

---

## Développement et tests

### Tests backend

```bash
cd backend

# Exécuter tous les tests
pytest

# Uniquement les tests unitaires
pytest tests/unit -v

# Uniquement les tests d'intégration
pytest tests/integration -v

# Migrations de base de données
alembic upgrade head

# Générer une migration
alembic revision --autogenerate -m "description"
```

### Développement frontend

```bash
cd frontend

npm install        # Installer les dépendances
npm run dev        # Démarrer le serveur de développement (:3000)
npm run build      # Build de production
npm test           # Exécuter les tests (Jest)
npm run lint       # Vérification ESLint
```

### Normes de code

| Couche | Norme |
|--------|-------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + indentation 2 espaces |
| Nommage | Python : `snake_case` / TypeScript : `PascalCase` + `camelCase` |
| Commits | Conventional Commits (`feat(scope): description`) |

---

## License

Private / Proprietary

---

## Support

- **Documentation** : [docs/](../../docs/)
- **Retours** : [GitHub Issues](https://github.com/your-org/agent-engine-platform/issues)
- **Dépôt** : [github.com/your-org/agent-engine-platform](https://github.com/your-org/agent-engine-platform)

<h1 align="center">
  <br>
  Agent Engine Platform
  <br>
</h1>

<h4 align="center">オールインワン AI Agent 構築・管理・オーケストレーションプラットフォーム。</h4>

<p align="center">
  <a href="../../README.md">🇺🇸 English</a> •
  <a href="README.zh.md">🇨🇳 中文</a> •
  <a href="README.ko.md">🇰🇷 한국어</a> •
  <a href="README.fr.md">🇫🇷 Français</a> •
  <a href="README.de.md">🇩🇪 Deutsch</a> •
  <a href="README.es.md">🇪🇸 Español</a> •
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
  <a href="#クイックスタート">クイックスタート</a> •
  <a href="#コア機能">コア機能</a> •
  <a href="#システムアーキテクチャ">アーキテクチャ</a> •
  <a href="#エンジンモジュール">エンジン</a> •
  <a href="#api-概要">API</a> •
  <a href="#設定">設定</a> •
  <a href="#デプロイガイド">デプロイ</a> •
  <a href="#技術スタック">技術スタック</a>
</p>

---

## 概要

Agent Engine Platform は、Agent 作成、ナレッジベース管理、ワークフロー編排、マルチ Agent コラボレーション、セキュリティ監査までの完全な機能を提供するフルスタックインテリジェントエージェントアプリケーションエンジンプラットフォームです。

**バックエンド**：FastAPI + Python 3.11  
**フロントエンド**：Next.js 14 + React 18 + Ant Design  
**インフラ**：Docker Compose オーケストレーション

---

## コア機能

- 🤖 **Agent 管理** - インテリジェントエージェントの作成、設定、公開。モデル選択、システムプロンプト、ツールバインド、ナレッジベース関連付けをサポート
- 🔀 **マルチモデルルーティング** - OpenAI / Anthropic / Ollama など複数 LLM プロバイダーへの統一アダプター。負荷分散、サーキットブレーカー、コスト追跡をサポート
- 📚 **ナレッジエンジン** - 完全な RAG パイプライン。ドキュメント解析（PDF/Word/Excel/PPT）、インテリジェントチャンキング、ベクトル検索（Milvus）、全文検索（ES）、グラフ検索（Neo4j）、LightRAG 二段階検索をサポート
- ⚡ **ワークフローエンジン** - 可視化 DAG 編排。LLM ノード、条件分岐、並列実行、ループ、HTTP 呼び出し、コードサンドボックス、手動承認、サブワークフローをサポート
- 🤝 **マルチ Agent コラボレーション** - Crew モード（順次/階層/並列/コンセンサス）と Handoff ルーティングプロトコル
- 🔧 **ツールエンジン** - 組み込み計算機、コードエグゼキューター、DB クエリ、ファイル操作、HTTP リクエスト、Web 検索。カスタムツール登録をサポート
- 🛡️ **セキュリティエンジン** - 入出力セキュリティ検出。Prompt インジェクション防御、PII マスキング、機密情報フィルタリングをカバー
- 📊 **評価エンジン** - Ragas スタイル RAG 品質評価（faithfulness/relevancy/precision/recall/tool accuracy）
- 🧠 **メモリシステム** - ショートタームメモリ（Redis セッション履歴）+ ロングタームメモリ（ベクトル化ストレージ + トピック抽出 + 要約圧縮）
- 🔌 **MCP サービス** - Model Context Protocol を通じてプラットフォーム機能を公開
- 👥 **マルチテナント** - 完全なテナント分離、RBAC 権限体系、部門管理、API Token 管理
- 📝 **監査とモニタリング** - 操作ログ、API 呼び出し監査、モデル使用量追跡、レート制限

---

## クイックスタート

### 前提条件

- Docker & Docker Compose
- 最低 8GB の空きメモリ（Milvus + Elasticsearch はリソースを多く消費）

### 1. クローンと設定

```bash
git clone <repository-url>
cd agent-engine-platform

# 環境変数をコピーして設定を変更
cp .env.example .env
# .env を編集。最低限以下を設定：
#   DB_PASSWORD, REDIS_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY, ENCRYPTION_KEY（本番環境では必須）
```

### 2. 全サービス起動

```bash
# フル起動（全インフラ + アプリケーションサービス）
docker-compose --profile full up -d

# または外部データベース使用（アプリケーション + Neo4j のみ起動）
docker-compose --profile external-db up -d
```

### 3. アクセス

| サービス | URL | 説明 |
|----------|-----|------|
| フロントエンド | http://localhost:3000 | Next.js 管理画面 |
| バックエンド API | http://localhost:8000 | FastAPI サービス |
| API ドキュメント | http://localhost:8000/docs | Swagger UI |
| Nginx | http://localhost:80 | 統一エントリーポイント |
| Neo4j Browser | http://localhost:7474 | グラフデータベースコンソール |

### 4. ローカル開発（Docker 不使用）

**バックエンド：**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**フロントエンド：**

```bash
cd frontend
npm install
npm run dev
```

---

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                     Nginx（リバースプロキシ）                   │
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
             │  メインDB    │    │  キャッシュ/キュー │   │  Worker/Beat│
             └─────────────┘    └─────────────────┘   └─────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼────┐  ┌──────▼──────┐ ┌────▼────┐
│  Milvus │  │ Elasticsearch│ │  Neo4j  │
│ ベクトルDB│  │  全文検索エンジン│ │ グラフDB │
└─────────┘  └─────────────┘ └─────────┘
```

### データフロー

1. **ユーザーリクエスト** → Nginx → Frontend（SSR/CSR）または Backend API
2. **会話リクエスト** → Backend → セキュリティエンジン（入力検出）→ モデルルーティング → LLM → セキュリティエンジン（出力検出）→ SSE ストリーミング応答
3. **RAG リクエスト** → ナレッジエンジン → ドキュメント解析 → チャンキング → Embedding → ストレージ（Milvus/ES/Neo4j）→ 検索 → Rerank → 生成
4. **非同期タスク** → Backend → Celery Worker（ドキュメント処理、モデルトレーニング、定期クリーンアップ）
5. **ワークフロー実行** → ワークフローエンジン → DAG スケジューリング → ノード実行 → 手動承認 → 結果出力

---

## エンジンモジュール

### モデルエンジン

統一 LLM アダプテーション層。複数プロバイダーをサポート：

| アダプター | サポートモデル | 機能 |
|-----------|---------------|------|
| `OpenAIAdapter` | GPT-4o, GPT-4, GPT-3.5 | Chat / Streaming / Function Calling |
| `AnthropicAdapter` | Claude Sonnet / Opus / Haiku | Chat / Streaming |
| `OllamaAdapter` | Qwen2.5, Llama（ローカルモデル） | Chat / Streaming |

コア機能：**ModelRouter**（マルチプロバイダー負荷分散）、**CircuitBreaker**（サーキットブレーカーパターン）、**CostTracker**（トークン使用量追跡とコスト計算）、**マルチモーダル**（ASR/TTS/OCR/Vision アダプター）

### ナレッジエンジン

ドキュメントから回答までの完全な RAG パイプライン：

```
ドキュメントアップロード → 解析（PDF/Word/Excel/PPT/TXT）→ インテリジェントチャンキング → Embedding
    → ストレージ（Milvus + ES + Neo4j）→ 検索（ベクトル/全文/グラフ/LightRAG）→ Rerank → 生成
```

**LightRAG 検索モード：**

| モード | 説明 | 適用シーン |
|--------|------|-----------|
| `naive` | 純粋ベクトル類似度 | 汎用 Q&A |
| `local` | エンティティフォーカス — 具体的な名称を抽出してグラフノードを検索 | 正確な事実查詢 |
| `global` | トピックフォーカス — 幅広い概念を抽出してリレーションシップエッジを検索 | マクロ分析 |
| `hybrid` | local + global 加重 RRF フュージョン | 複雑な総合查詢 |

### ワークフローエンジン

DAG ワークフロー編排。以下のノードタイプをサポート：

| ノードタイプ | 説明 |
|-------------|------|
| `llm` | LLM 呼び出しノード |
| `condition` | 条件分岐 |
| `parallel` | 並列実行 |
| `loop` | ループ実行 |
| `http` | HTTP リクエスト |
| `code` | Python コードサンドボックス（リソース分離） |
| `human` | 手動承認 |
| `sub_workflow` | サブワークフロー呼び出し |

機能：グローバルタイムアウト制御、ノードレベル実行トレース、変数スナップショット、詳細実行ログ。

### マルチ Agent エンジン

**Crew モード**：マルチ Agent チームコラボレーション
- Sequential（順次実行）、Hierarchical（階層管理）、Parallel（並列実行）、Consensus（コンセンサス決定）

**Handoff モード**：Agent 間構造化ハンドオフ
- Pydantic ベースの `HandoffMessage` プロトコル
- `HandoffTracker` がハンドオフ状態とホップ数を追跡

### ツールエンジン

組み込みツールセット：

| ツール | 機能 |
|--------|------|
| `calculator` | 数式計算 |
| `code_executor` | Python コードサンドボックス実行 |
| `db_query` | データベースクエリ（パラメータ化） |
| `file_ops` | ファイル読み書き操作 |
| `http_request` | HTTP リクエスト |
| `web_search` | Web 検索 |

`ToolRegistry` を通じたカスタムツールの動的登録をサポート。

### セキュリティエンジン

4層セキュリティ防御：
1. **Prompt インジェクション検出** - 正規表現マッチング + セマンティック分析
2. **PII マスキング** - 身分証、電話番号、メール、銀行口座などの自動認識とマスキング
3. **機密情報フィルタリング** - 設定可能な機密度レベル（low/medium/high）
4. **コンプライアンスチェック** - オプションのコンプライアンスポリシースイッチ

### メモリエンジン

- **ShortTermMemory** - Redis ベースのセッション履歴。TTL と最大メッセージ数制限をサポート
- **LongTermMemory** - 会話要約圧縮 + トピック抽出 + ベクトル化ストレージ。クロスセッション検索をサポート

### 評価エンジン

Ragas スタイル RAG 品質評価。5 つのコア指標：
- `faithfulness` - 回答が検索されたコンテキストに忠実かどうか
- `answer_relevancy` - 回答と質問の関連性
- `context_precision` - 検索結果のランキング品質
- `context_recall` - 検索が必要なすべての情報をカバーしているか
- `tool_call_accuracy` - ツール呼び出しの正確性

---

## API 概要

全 API ルートプレフィックス：`/api/v1`

| モジュール | ルート | 説明 |
|-----------|--------|------|
| Auth | `/auth/*` | ログイン、登録、Token リフレッシュ |
| Agents | `/agents/*` | Agent CRUD、公開 |
| Chat | `/chat/*` | 会話（SSE ストリーミング） |
| Conversations | `/conversations/*` | セッション管理 |
| Knowledge | `/knowledge/*` | ナレッジベース、ドキュメントアップロード、検索 |
| Models | `/models/*` | モデルプロバイダー設定 |
| Workflows | `/workflows/*` | ワークフロー CRUD、実行 |
| Tools | `/tools/*` | ツール管理 |
| Multi-Agent | `/multi-agent/*` | マルチ Agent 編排 |
| Memory | `/memory/*` | メモリ管理 |
| Evaluations | `/evaluations/*` | RAG 評価 |
| Triggers | `/triggers/*` | Cron / イベント / Webhook トリガー |
| Webhooks | `/webhooks/*` | Webhook エンドポイント管理 |
| Audit | `/audit/*` | 監査ログ查詢 |
| Usage | `/usage/*` | モデル使用量統計 |
| Users | `/users/*` | ユーザー管理 |
| Roles | `/roles/*` | ロール権限管理 |
| Tenants | `/tenants/*` | テナント管理 |
| Tokens | `/tokens/*` | API Token 管理 |
| Feedbacks | `/feedbacks/*` | ユーザーフィードバック |
| Tasks | `/tasks/*` | Celery タスク状態 |

**ヘルスチェック**：`GET /health` — データベースと Redis の接続状態を返却。

---

## 設定

すべての設定は環境変数で管理。`.env.example` を参照。

### 本番環境で必須の設定

| 設定項目 | 説明 |
|----------|------|
| `DB_PASSWORD` | MySQL root パスワード |
| `REDIS_PASSWORD` | Redis 認証パスワード |
| `NEO4J_PASSWORD` | Neo4j 認証パスワード |
| `SECRET_KEY` | JWT 署名キー（≥16 文字） |
| `ENCRYPTION_KEY` | データ暗号化キー（≥16 文字） |

### 主要調整可能パラメータ

| 設定項目 | デフォルト値 | 説明 |
|----------|-------------|------|
| `DB_POOL_SIZE` | 10 | データベース接続プールサイズ |
| `RATE_LIMIT_PER_MINUTE` | 60 | API レート制限 |
| `CELERY_WORKER_CONCURRENCY` | 4 | Celery Worker 並行数 |
| `WORKFLOW_GLOBAL_TIMEOUT` | 300 | ワークフローグローバルタイムアウト（秒） |
| `MAX_UPLOAD_SIZE_MB` | 50 | ファイルアップロードサイズ制限（MB） |
| `SAFETY_INPUT_CHECK_ENABLED` | true | 入力セキュリティ検出スイッチ |
| `SAFETY_OUTPUT_CHECK_ENABLED` | true | 出力セキュリティ検出スイッチ |

---

## デプロイガイド

### Docker デプロイ（推奨）

```bash
# 1. 環境変数を設定
cp .env.example .env
vim .env  # すべての <PRODUCTION> マーク項目を変更

# 2. セキュアキーを生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 起動
docker-compose --profile full up -d

# 4. ログ確認
docker-compose logs -f backend
```

### Nginx HTTPS 設定

`nginx/nginx.conf` を編集し、HTTPS server ブロックのコメントを解除。証明書を `nginx/ssl/` ディレクトリに配置：

```
nginx/ssl/cert.pem
nginx/ssl/key.pem
```

### 外部データベースモード

MySQL / Redis / Milvus / ES が外部サービスで提供される場合、`.env` で対応する接続 URL を設定し、以下を実行：

```bash
docker-compose --profile external-db up -d
```

---

## 技術スタック

### バックエンド

| 技術 | 用途 |
|------|------|
| Python 3.11 | ランタイム |
| FastAPI | Web フレームワーク |
| SQLAlchemy 2.0 + aiomysql | 非同期 ORM |
| Pydantic 2.0 | データバリデーション |
| Celery + Redis | 非同期タスクキュー |
| Alembic | データベースマイグレーション |
| python-jose | JWT 認証 |
| httpx | 非同期 HTTP クライアント |
| sse-starlette | SSE ストリーミングレスポンス |
| pymilvus | Milvus ベクトルDBクライアント |
| neo4j | Neo4j グラフDBドライバー |
| elasticsearch | ES クライアント |
| minio | オブジェクトストレージクライアント |

### フロントエンド

| 技術 | 用途 |
|------|------|
| Next.js 14 | React フレームワーク（App Router） |
| React 18 | UI ライブラリ |
| TypeScript 5 | 型安全性 |
| Ant Design 5 | UI コンポーネントライブラリ |
| Tailwind CSS 3 | スタイリング |
| Zustand | 状態管理 |
| Axios | HTTP クライアント |
| ECharts | データ可視化 |
| React Markdown | Markdown レンダリング |
| Jest + Testing Library | テスト |

### インフラ

| 技術 | 用途 |
|------|------|
| Docker Compose | サービスオーケストレーション |
| MySQL 8.0 | メインデータベース |
| Redis 7 | キャッシュ + メッセージキュー |
| Milvus 2.4 | ベクトルデータベース |
| Neo4j 5 | グラフデータベース |
| Elasticsearch 8.12 | 全文検索 |
| Nginx | リバースプロキシ + レート制限 |
| MinIO | オブジェクトストレージ（オプション） |

---

## プロジェクト構造

```
agent-engine-platform/
├── backend/                        # Python バックエンド（FastAPI）
│   ├── app/
│   │   ├── api/v1/                 # RESTful API ルート（20+ モジュール）
│   │   ├── core/                   # コアインフラ
│   │   ├── engines/                # コアエンジンモジュール
│   │   ├── models/                 # SQLAlchemy ORM モデル
│   │   ├── schemas/                # Pydantic リクエスト/レスポンス Schema
│   │   ├── tasks/                  # Celery 非同期タスク
│   │   ├── mcp/                    # MCP サーバー
│   │   └── main.py                 # FastAPI アプリケーションエントリー
│   ├── tests/                      # テスト（unit / integration）
│   ├── alembic/                    # データベースマイグレーション
│   └── Dockerfile
├── frontend/                       # TypeScript フロントエンド（Next.js 14）
│   ├── src/
│   │   ├── app/                    # App Router ページ
│   │   ├── components/             # React コンポーネント
│   │   ├── lib/                    # API クライアント
│   │   ├── store/                  # Zustand 状態管理
│   │   └── types/                  # TypeScript 型定義
│   └── Dockerfile
├── nginx/                          # Nginx リバースプロキシ設定
├── scripts/                        # データベース初期化 SQL
├── docs/                           # ドキュメント
├── docker-compose.yml              # 全サービスオーケストレーション
├── .env.example                    # 環境変数テンプレート
└── AGENTS.md                       # 自動化エージェントルール
```

---

## 開発とテスト

### バックエンドテスト

```bash
cd backend

# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit -v

# 統合テストのみ
pytest tests/integration -v

# データベースマイグレーション
alembic upgrade head

# マイグレーション生成
alembic revision --autogenerate -m "description"
```

### フロントエンド開発

```bash
cd frontend

npm install        # 依存関係インストール
npm run dev        # 開発サーバー起動（:3000）
npm run build      # プロダクションビルド
npm test           # テスト実行（Jest）
npm run lint       # ESLint チェック
```

### コーディング規約

| レベル | 規約 |
|--------|------|
| Python | PEP 8 + Type Hints + async/await |
| TypeScript | ESLint + Strict Mode + 2-space indent |
| 命名規則 | Python: `snake_case` / TypeScript: `PascalCase` + `camelCase` |
| コミット | Conventional Commits（`feat(scope): description`） |

---

## License

このプロジェクトはApache License 2.0の下でライセンスされています。詳細は[LICENSE](../../LICENSE)ファイルをご覧ください。

---

## 貢献

貢献を歓迎します！Pull Requestをお気軽に送信してください。

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを開く

---

## サポート

- **ドキュメント**: [docs/](../../docs/)
- **問題報告**: [GitHub Issues](https://github.com/BianHL/agent-engine-platform/issues)
- **リポジトリ**: [github.com/BianHL/agent-engine-platform](https://github.com/BianHL/agent-engine-platform)

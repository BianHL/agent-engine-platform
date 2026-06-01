# Repository Guidelines

> **Frontend developers: All UI work MUST comply with `DESIGN.md` (design tokens, component specs, color rules) and `PRODUCT.md` (brand personality, anti-references). Read both before writing any frontend code.**

## Project Structure & Module Organization

This is a full-stack **Agent Engine Platform** with a Python backend and Next.js frontend, orchestrated via Docker Compose.

```
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # API route handlers (versioned: v1/)
│   │   ├── core/           # Auth, database, logging, middleware, security
│   │   ├── engines/        # Core engine modules (model, memory, knowledge, etc.)
│   │   ├── framework/      # Framework abstractions
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── tasks/          # Celery async tasks
│   │   ├── utils/          # Shared utilities
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/              # unit/, integration/, e2e/
│   └── alembic/            # Database migrations
├── frontend/               # Next.js 14 + React 18 + Ant Design + Tailwind
│   └── src/
│       ├── app/            # Next.js App Router pages & layouts
│       ├── components/     # React components
│       │   └── ui/         # Custom design system components (14 components)
│       ├── hooks/          # Custom React hooks
│       ├── lib/            # API client, theme tokens, helpers
│       ├── store/          # Zustand state stores
│       ├── locales/        # i18n translation files
│       └── types/          # TypeScript type definitions
├── nginx/                  # Nginx reverse proxy config
├── scripts/                # Init SQL and utility scripts
├── docs/                   # Specs and design documents
├── PRODUCT.md              # Product definition, users, brand personality
├── DESIGN.md               # Design system specification (authoritative)
├── docker-compose.yml      # Base Docker config
    ├── docker-compose.dev.yml  # Dev overrides
    ├── docker-compose.prod.yml # Prod overrides
    └── .env.docker             # Docker env template
```

## Design System

**All frontend work must comply with `DESIGN.md` and `PRODUCT.md`.** Read both before making any UI changes.

### Design North Star: "The Well-Typeset Workshop"

Soft editorial warmth. Warm parchment neutrals, olive-green and warm-gold accents, generous spacing. Designed for 6-hour work sessions, not 30-second demos.

### Key Design Tokens (CSS Variables)

All colors, radii, spacing, and shadows are defined as CSS variables in `frontend/src/app/globals.css` and `frontend/src/lib/theme.ts`. **Never hardcode colors** — always use tokens.

| Token | Value | Usage |
|-------|-------|-------|
| `--ae-bg` | `#f5efe6` | Page background (warm parchment) |
| `--ae-panel` | `rgba(255,255,255,0.74)` | Glassmorphism panel |
| `--ae-text` | `#26221e` | Primary text (warm black) |
| `--ae-muted` | `rgba(38,34,30,0.58)` | Secondary text |
| `--ae-accent-olive` | `#7a8a6a` | Primary accent |
| `--ae-accent-gold` | `#c29a63` | Secondary accent |
| `--ae-line` | `rgba(86,68,54,0.10)` | Borders |
| `--ae-radius-sm/md/lg/xl` | `12/16/22/30px` | Border radius scale |
| `--ae-shadow` | `0 18px 50px rgba(74,60,48,0.10)` | Card shadow (warm-tinted) |

### Absolute Rules (from DESIGN.md)

- **No pure black/white**: `#000` and `#fff` are prohibited. Use `rgba(255,255,255,0.95)` or tinted equivalents.
- **No blue or purple**: The palette is strictly warm (beige, olive, gold, warm red).
- **No gradient text**: No `background-clip: text`.
- **No cold gray shadows**: All shadows use warm brown tints.
- **Serif for display headings**: `h1`/`h2`/`h3` use Georgia serif. All UI text uses Inter sans-serif.
- **Glassmorphism by default**: Cards and panels use `backdrop-filter: blur(16px)` + semi-transparent backgrounds.
- **Large border radii**: Cards use 22px–30px. Controls use 12px–16px.

### Custom UI Components

Located in `frontend/src/components/ui/`. Import from `@/components/ui`:

```tsx
import { Card, Button, StatusBadge, ProgressBar, Modal, showToast } from '@/components/ui';
```

| Component | Description |
|-----------|-------------|
| `Card` | Glassmorphism card with hover lift, decorative gradient option |
| `Button` | Primary (gradient), ghost, danger variants. 3 sizes |
| `Input` | Glass panel input with olive focus ring |
| `TextArea` | Multi-line input |
| `Select` | Dropdown select |
| `Modal` | Glassmorphism modal with scale animation |
| `Toast` | Top-right notification (success/error/warning). Use `showToast()` |
| `Tooltip` | Warm-black tooltip with translateY animation |
| `StatusBadge` | Status dot with glow shadow (success/warning/danger/info/processing) |
| `ProgressBar` | Gradient fill bar (olive → sage → gold) |
| `ToggleSwitch` | 44×24px toggle with warm-tinted thumb |
| `EmptyState` | Centered empty state with dashed border |
| `Table` | Glass panel table with olive hover tint |
| `SearchInput` | Search input with icon |

### Ant Design Usage

Ant Design is retained for complex components (DatePicker, Select dropdowns, Form validation, Drawer, Menu). Visual styling is overridden via `globals.css` to match the design system. When using Ant Design components:

- Use the theme tokens from `theme.ts` — they auto-map to Ant Design's ConfigProvider
- For buttons, prefer the custom `Button` component over `antd Button`
- For modals, prefer the custom `Modal` component over `antd Modal`
- For tables, prefer the custom `Table` component for simple cases; use Ant Design Table for complex features (pagination, sorting, filtering)

## Build, Test, and Development Commands

### Local Development (Docker Compose)

```bash
# Start all infrastructure services + backend + frontend
docker compose up -d

# View logs for a specific service
docker compose logs -f backend

# Rebuild after dependency changes
docker compose up -d --build backend frontend
```

### Backend (Python / FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the dev server (auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run all tests
pytest

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v

# Run database migrations
alembic upgrade head
```

### Frontend (Next.js / TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 3000)
npm run dev

# Production build (use to verify no errors)
npm run build

# Run tests
npm test

# Run linter
npm run lint
```

## Coding Style & Naming Conventions

### Python (Backend)

- **Indentation**: 4 spaces, no tabs.
- **Style**: Follow PEP 8. Use type hints on all public functions.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- **Async**: Prefer `async/await` throughout; the app uses `asyncio` with `aiomysql`.
- **Models**: SQLAlchemy ORM models in `app/models/`, Pydantic schemas in `app/schemas/`.
- **Imports**: Group as stdlib → third-party → local, separated by blank lines.

### TypeScript (Frontend)

- **Indentation**: 2 spaces.
- **Style**: Follow the project ESLint config (`next lint`). Use TypeScript strict mode.
- **Naming**: `PascalCase` for components and types, `camelCase` for functions/variables, `UPPER_SNAKE_CASE` for constants.
- **State**: Use Zustand stores in `src/store/` for shared state; keep component state local when possible.
- **Styling**: Use CSS variables (`var(--ae-*)`) for all colors, radii, shadows. Tailwind utility classes for layout. Custom components from `@/components/ui` for UI elements.
- **Fonts**: `var(--ae-font-family)` for sans-serif, `var(--ae-font-family-serif)` for display headings. Never hardcode font families.
- **Animations**: Use `180ms ease` for hover transitions, `650ms cubic-bezier(.2,1,.2,1)` for entrance animations. Respect `prefers-reduced-motion`.

## Testing Guidelines

### Backend (pytest)

- **Framework**: pytest with `pytest-asyncio` (auto mode enabled).
- **Structure**: Tests mirror source layout — `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- **Naming**: Files `test_*.py`, classes `Test*`, functions `test_*`.
- **Markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`.
- **Fixtures**: Shared fixtures in `tests/conftest.py`; integration fixtures in `tests/integration/conftest.py`.
- **Coverage**: Aim for ≥80% on new code. Always test error paths and edge cases.

### Frontend (Jest + Testing Library)

- **Framework**: Jest 30 with `@testing-library/react` and `jest-environment-jsdom`.
- **Config**: `jest.config.js` with setup in `jest.setup.js`.
- **Naming**: Co-locate tests or use `__tests__/` directories. Test files: `*.test.ts(x)`.
- **Approach**: Test component behavior and user interactions, not implementation details.

## Commit & Pull Request Guidelines

### Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <short summary>
```

- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- **Scope**: Module name (e.g., `auth`, `api`, `memory-engine`, `frontend`, `design-system`)
- **Summary**: Imperative mood, lowercase, no period. E.g., `feat(auth): add JWT refresh token rotation`

### Pull Requests

- Include a clear description of what changed and why.
- Link related issues.
- Ensure all tests pass (`pytest` and `npm test`).
- Run `npm run build` to verify frontend compiles without errors.
- Include screenshots for frontend UI changes.
- Keep PRs focused — one feature or fix per PR.
- Request review from at least one team member.

## Security & Configuration

- **Never commit `.env`** — copy `.env.example` to `.env` and fill in secrets.
- Required secrets: `MYSQL_ROOT_PASSWORD`, `NEO4J_PASSWORD`, `MINIO_SECRET_KEY`, `SECRET_KEY`, `ENCRYPTION_KEY`.
- All API routes requiring authentication use JWT Bearer tokens.
- CORS, HTTPS redirect, rate limiting, and audit logging are configured as middleware in `app/main.py`.
- Database migrations use Alembic — always generate migrations with `alembic revision --autogenerate` and review before applying.

# MindMesh — Workspace Instructions

## Project Overview
MindMesh converts YouTube videos into personalized AI study guides. Multi-model pipeline using Groq (Llama 4 Scout / Whisper) for speed and OpenAI (gpt-5.4-mini) for long-context quality.

## Architecture
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS v4, TypeScript 5
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, Jinja2 prompts
- **Database:** Supabase (Postgres + pgvector + RLS + pg_cron)
- **AI Models:** Groq Llama-4-scout-17b (short guides), OpenAI gpt-5.4-mini (long guides, 400K context), Groq Whisper v3 Turbo (STT), text-embedding-3-small (embeddings)
- **Payments:** Stripe (Phase 3, webhooks already scaffolded)

## Monorepo Layout
```
backend/app/          # FastAPI — services, routers, prompts, models, utils
frontend/src/         # Next.js — app/, components/, hooks/, lib/, types/
docs/                 # Supplementary documentation
migrations/           # SQL migrations (Supabase)
```

## Build & Run Commands
```bash
# Backend
cd backend && python -m venv venv && .\venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && pnpm install && pnpm dev

# Tests
cd backend && pytest -v

# Lint
cd frontend && pnpm lint

# Both at once (Windows)
.\start.bat
```

## Code Conventions

### General
- Write complete, production-ready code — no placeholders (`// TODO`, `// ...`)
- Match existing file style: imports, naming, patterns
- Minimal-impact changes — smallest diff that fulfills the requirement
- Wrap external calls (APIs, DB, file I/O) in proper error handling
- Never expose secrets or API keys in client-side code

### Backend (Python)
- snake_case for variables, functions, modules
- Pydantic v2 models for all request/response schemas
- Custom exceptions via `MindMeshError` hierarchy (see `utils/errors.py`)
- Structured logging via `structlog` — never use `print()`
- Tenacity for retry logic on LLM/API calls
- Jinja2 templates for all LLM prompts (see `prompts/templates/`)
- Type hints on all public functions
- FastAPI `Depends()` for auth, rate limiting, settings injection

### Frontend (TypeScript/React)
- camelCase for variables/functions, PascalCase for components
- Functional components with hooks — no class components
- `'use client'` directive only where needed (event handlers, hooks, browser APIs)
- API calls go through `lib/api.ts` (`apiFetch<T>()` wrapper)
- Types defined in `types/index.ts` — keep in sync with backend schemas
- Tailwind utility classes — no inline styles, no CSS modules
- pnpm only — npm will break on Windows (TAR_ENTRY_ERROR)

## Auth Flow
- Supabase Auth (JWT) in production
- Dev Mode: `mindmesh-dev` cookie → bypasses auth, in-memory storage
- Demo Mode: `mindmesh-demo` cookie → mock data, no backend calls
- Backend JWT verification via `python-jose` in `dependencies.py`

## AI Model Routing
| Task | Model | Provider | Threshold |
|------|-------|----------|-----------|
| Triage | llama-3.1-8b-instant | Groq | First 2K tokens |
| Guide (short) | llama-4-scout-17b | Groq | < 13K tokens |
| Guide (long) | gpt-5.4-mini | OpenAI | >= 13K tokens |
| Quiz | llama-3.1-8b-instant | Groq | Guide JSON input |
| Embeddings | text-embedding-3-small | OpenAI | 512 dimensions |
| STT fallback | whisper-large-v3-turbo | Groq | When captions unavailable |

## Current Status (March 2026)
- **Phase 1 & 2:** 100% complete
- **Phase 3:** ~95% complete — all code shipped; one external ops task remains (create Stripe product in Dashboard → get `price_xxx` → set `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID` in `frontend/.env.local`)
- **Phase 4:** Polish & launch (not started — see `.github/CONTEXT.md` for priority order)

## Key Data Contracts

### `StudyGuideCore` JSON shape (what `guide_json` contains)
```json
{ "tldr": "...", "memory_questions": [...], "themes": [{ "theme_number": 1, "title": "...", "time_range": "...", "core_concept": "...", "mechanics": ["..."], "analogy_or_example": "...", "subtopics": [], "deep_dive": null }] }
```

### `StudyGuidePro` JSON shape (extends Core)
```json
{ ...core_fields, "reflection_question": "...", "quiz": [...] }
```

## Database Tables (Supabase — applied via 001_initial_schema.sql)
| Table | Purpose |
|-------|---------|
| `profiles` | Auth-linked profile, `tier`, `credits_remaining` |
| `processing_jobs` | Async job queue (`pending → processing → completed/failed`) |
| `study_guides` | Full guide output with `guide_json`, `guide_markdown` |
| `videos` | Cached video metadata (title, channel, duration) |
| `concepts` | Extracted concepts per guide (for embeddings) |
| `api_usage` | Per-user API cost tracking |
| `reflections` | Persisted Pro user reflection answers |

## Singleton DB Client
- `from app.dependencies import get_db` — FastAPI `Depends()` injection
- Falls back to `DevStore` (in-memory) when Supabase keys are placeholders
- Never instantiate `AsyncClient` directly in a service — always use `Depends(get_db)`

## Critical Anti-Patterns (Never Do)
- Never `print()` — use `structlog.get_logger()`
- Never hardcode prompts — use Jinja2 templates in `prompts/templates/`
- Never return raw dicts from API routes — use Pydantic response models
- Never access `supabase` directly in routers — use `db = Depends(get_db)`
- Never use `npm` — only `pnpm` (TAR_ENTRY_ERROR on Windows)
- Never put secrets in `NEXT_PUBLIC_*` except Supabase anon/url (safe by design)
- Never call backend directly from React components — use `lib/api.ts` functions

## Workflow Rules
- **Read `.github/CONTEXT.md` before significant work** — it is the authoritative source for current phase status, architectural decisions, and known gotchas. It overrides any stale information in this file.
- Plan before executing complex features — use the `@planner` agent to write `.github/PLAN.md`, then `@implementer` to execute, then `@auditor` to review.
- Use `@Explore` for read-only codebase Q&A instead of chaining multiple file reads in the main context.
- Identify security vulnerabilities proactively — refuse insecure approaches
- Challenge flawed architectural decisions directly
- After making changes, run the relevant build/test commands to verify
- Use branch isolation for new features
- **Update `.github/CONTEXT.md`** whenever an architectural decision is made, a phase changes, or a significant gotcha is discovered. Keep it accurate.

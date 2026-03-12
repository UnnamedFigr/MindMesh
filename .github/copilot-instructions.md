# MindMesh — Workspace Instructions

## Project Overview
MindMesh converts YouTube videos into personalized AI study guides. Multi-model pipeline using Groq (Llama 4 Scout / Whisper) for speed and OpenAI (GPT-4.1) for long-context quality.

## Architecture
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS v4, TypeScript 5
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, Jinja2 prompts
- **Database:** Supabase (Postgres + pgvector + RLS + pg_cron)
- **AI Models:** Groq Llama-4-scout-17b (short guides), OpenAI GPT-4.1 (long guides), Groq Whisper v3 Turbo (STT), text-embedding-3-small (embeddings)
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
| Guide (long) | gpt-4.1 | OpenAI | >= 13K tokens |
| Quiz | llama-3.1-8b-instant | Groq | Guide JSON input |
| Embeddings | text-embedding-3-small | OpenAI | 512 dimensions |
| STT fallback | whisper-large-v3-turbo | Groq | When captions unavailable |

## Current Status (March 2026)
- **Phase 1 & 2:** 100% complete (backend + frontend MVP operational)
- **Phase 3 (in progress):** Stripe integration, quiz UI, semantic search/associations
- **Phase 4:** Polish & launch (not started)

## Workflow Rules
- Plan before executing complex features — output a step-by-step plan first
- Identify security vulnerabilities proactively — refuse insecure approaches
- Challenge flawed architectural decisions directly
- After making changes, run the relevant build/test commands to verify
- Use branch isolation for new features
- When a major architectural pivot or important workflow decision happens, proactively suggest updating memory so repository context stays aligned with the current state

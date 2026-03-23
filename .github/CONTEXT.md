# MindMesh — Project Context & Decision Log

> **Purpose:** Ground AI agents and Copilot sessions in accurate project state.
> Read this file at the start of any significant work to avoid stale assumptions.
> Update this file whenever an architectural decision is made or a phase changes.

---

## Current State (Updated: March 23, 2026)

### Phase Completion
| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Foundation | ✅ 100% | Config, auth, DB schema, Supabase setup |
| Phase 2 — Core Pipeline | ✅ 100% | Guide gen, transcript, triage, full frontend |
| Phase 3 — Pro Features | ✅ ~95% | All code done; one external ops task remains |
| Phase 4 — Polish & Launch | ⬜ ~15% | Dev-mode+real-keys fix done, test suite fixed, demo entry and frontend cleanup improved |

### Phase 3 — One Remaining Task
- [ ] Create Stripe product in Dashboard → `€5/mo recurring` → copy `price_xxx` → set in `frontend/.env.local` as `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID`

### Workflow Hardening (March 19, 2026)
- Added `.github/WORKFLOW.md` as the central role-selection and handoff document.
- Added `.github/RAG-INDEX.md` to route common questions to authoritative files.
- Added retrieval and audit instruction docs under `.github/instructions/`.
- Updated agent definitions so major roles read `.github/CONTEXT.md` first.

### Frontend Cleanup And Demo Entry (March 19, 2026)
- Adopted the Next.js 16 `proxy.ts` file convention instead of `middleware.ts` to remove the framework deprecation warning.
- Added explicit remote image hosts in `frontend/next.config.ts` and migrated the main YouTube thumbnail surfaces to `next/image`.
- Cleaned frontend lint warnings in active app files and revalidated with `pnpm build` and `pnpm lint`.
- Updated `/demo` to enter demo mode and jump directly into a pre-generated demo guide instead of stopping at the dashboard.

---

## Infrastructure State

### Services
- **Backend:** FastAPI on `http://localhost:8000`, Python venv at `backend/venv/`
- **Frontend:** Next.js on `http://localhost:3000`, pnpm
- **Supabase project:** `qkjhqwsecfuhvaopxslh` — all 7 tables applied
- **Stripe CLI:** v1.37.8, account `acct_1TC48LPQujtWPrdK`, run `stripe listen` each dev session

### Database Tables (as of March 18, 2026)
`profiles`, `study_guides`, `videos`, `processing_jobs`, `api_usage`, `concepts`, `reflections`

### Dev Stack Startup Order
```powershell
# 1. Backend
cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000

# 2. Stripe webhook forwarding (needed for billing events)
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe

# 3. Frontend
cd frontend; pnpm dev
```

---

## Architectural Decisions

### Auth (fixed March 2026)
- **Decision:** Replace `python-jose` local JWT decode with `supabase.auth.get_user(token)` via `asyncio.to_thread`
- **Reason:** `SUPABASE_JWT_SECRET` env var is the anon JWT (not the HS256 signing secret). Local decode was failing with signature errors on every request.
- **File:** `backend/app/dependencies.py`
- **Config:** `supabase_jwt_secret` is optional (`= ""`) in `config.py` — intentional

### Dev Mode Trigger
- **Decision:** Dev mode originally only activated when `service_key.startswith("your-")` AND `environment=="development"`
- **Problem:** Once real Supabase keys are set, `is_dev_mode()` returns False, and `Bearer dev-mode` token fails auth.
- **Fix (March 18, 2026):** Added a second bypass in `get_current_user`: `token == "dev-mode" AND settings.environment == "development"` → returns dev user. Uses `contextvars.ContextVar` in `db.py` so `get_supabase()` returns DevStore (in-memory) for the entire dev-mode request, preventing FK constraint violations from hitting real Supabase with a non-existent dev user UUID.
- **Files:** `backend/app/dependencies.py`, `backend/app/db.py`, `backend/app/services/dev_store.py`
- **Dev user UUID:** `00000000-0000-0000-0000-000000000001` (defined in `dev_store.py` as `DEV_USER_ID`)

### Profile Auto-Provisioning
- **Decision:** `/api/credits` upserts a `profiles` row if none exists for the authenticated user
- **Reason:** The `handle_new_user` DB trigger only fires on new signups; existing users had no profile row after migrations were applied retroactively
- **File:** `backend/app/main.py`

### Stripe Keys Split
- **Decision:** `STRIPE_SECRET_KEY` (`sk_test_...`) lives in `backend/.env` only. `STRIPE_PUBLISHABLE_KEY` (`pk_test_...`) lives in `frontend/.env.local` as `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.
- **Reason:** Adding `STRIPE_PUBLISHABLE_KEY` to `backend/.env` crashes startup — Pydantic `Settings` has `extra = "forbid"`.
- **NEVER** add unknown env vars to `backend/.env` without a matching field in `config.py`.

### Stripe Local-Dev Activation Path
- **Decision:** Added `POST /api/billing/activate` endpoint in `backend/app/routers/billing.py` to handle upgrades when webhooks can't reach localhost.
- **How it works:** Stripe success URL contains `{CHECKOUT_SESSION_ID}` template (substituted by Stripe on redirect). Settings page extracts the session ID and calls `activateCheckoutSession(sessionId)` → `POST /api/billing/activate?session_id=…`. Backend calls `stripe.checkout.Session.retrieve(session_id)`, verifies `session.client_reference_id == user_id` (security), checks `session.payment_status in ("paid", "no_payment_required")`, then upserts `tier=pro, daily_credit_limit=15, credits_used=0` in Supabase `profiles`.
- **Security:** `client_reference_id` is set from the authenticated user's ID at checkout creation time and verified server-side — prevents one user from activating another's session.
- **Files:** `backend/app/routers/billing.py` (`activate_checkout_session`), `frontend/src/lib/api.ts` (`activateCheckoutSession`), `frontend/src/app/(dashboard)/settings/page.tsx` (useEffect on `?session_id=` param)
- **Also fixed (same session):** `_handle_checkout_completed` and `_handle_subscription_updated` in `webhooks.py` now reset `credits_used=0`; `billing.py` reconciliation updates `daily_credit_limit` and `credits_used` in both DB and in-memory; `worker.py` logs the actual selected `guide_model` instead of the settings default; `settings/page.tsx` wraps `useSearchParams` in a `<Suspense>` boundary (App Router requirement).

### Stripe Webhook Secret
- **Decision:** `STRIPE_WEBHOOK_SECRET` in `backend/.env` is the `whsec_...` from `stripe listen`, NOT the Stripe Dashboard webhook endpoint secret.
- **Consequence:** This secret changes if you re-run `stripe listen`. Update `backend/.env` after restarting the listener in a new CLI session.

### Database Migrations
- **Decision:** `001_initial_schema.sql` was applied via `psycopg2` direct connection (March 2026).
- **Decision:** `20260311_add_credit_reset_cron.sql` was skipped — `pg_cron` not available on Supabase free tier.
- **Decision:** `002_add_study_guides_video_fk.sql` adds FK `study_guides.video_id → videos.youtube_id` (applied March 18, 2026).
- **Reason:** Without this FK, PostgREST cannot resolve the `videos(title, ...)` relationship embedding in list/get queries — the library page silently shows zero guides.
- **Consequence:** Monthly credit reset is handled in `backend/app/services/credits.py` (Python-side logic), NOT via pg_cron.

### Model Routing
- **Groq `llama-4-scout-17b`:** transcript token count < 13,000 (short videos, free tier)
- **OpenAI `gpt-5.4-mini`:** transcript token count ≥ 13,000 (long videos; 400K context, $0.75/$4.50 per 1M)
- **Triage:** `llama-3.1-8b-instant` (fast/cheap, first 2K tokens)
- **Embeddings:** `text-embedding-3-small` at 512 dimensions via OpenAI
- **app runs local-only** — Render deployment dropped due to datacenter IP bot-detection on YouTube

---

## Known Gotchas

| Gotcha | Impact | Context |
|--------|--------|---------|
| `pnpm` only — never `npm` | TAR_ENTRY_ERROR on Windows | Frontend package manager |
| No `STRIPE_PUBLISHABLE_KEY` in `backend/.env` | Startup crash (Pydantic extra=forbid) | Stripe key split |
| `whsec_...` changes per `stripe listen` session | Webhook verification fails after restart | Must update `backend/.env` |
| `pg_cron` unavailable on Supabase free tier | Credit reset cron migration fails — ignore | credits.py handles reset |
| `SUPABASE_JWT_SECRET` is anon token, not signing secret | Local JWT decode fails — use `supabase.auth.get_user` | Auth flow |
| `is_dev_mode()` = False once real service key is set | Dev-mode token bypass uses `contextvars` to route DB to DevStore | Mode detection |
| `__pycache__` stale bytecode | `uvicorn --reload` may not pick up changes; clear `__pycache__` when code changes aren't taking effect | Backend debugging |
| Missing FK `study_guides → videos` | PostgREST can't join; library returns 0 guides | Fixed by `002_add_study_guides_video_fk.sql` |

---

## Key File Map

| Concern | File |
|---------|------|
| Workflow entry point | `.github/WORKFLOW.md` |
| Retrieval/source routing | `.github/RAG-INDEX.md` |
| Next.js request proxy | `frontend/src/proxy.ts` |
| Auth middleware | `backend/app/dependencies.py` |
| Settings / env vars | `backend/app/config.py` |
| Credits + profile provisioning | `backend/app/main.py` (inline route) |
| DB client singleton + dev context | `backend/app/db.py` |
| Dev-mode in-memory store | `backend/app/services/dev_store.py` |
| Guide generation | `backend/app/services/generator.py` |
| Worker pipeline (Pro: quiz, embeddings, associations) | `backend/app/services/worker.py` |
| Embeddings / associations | `backend/app/services/embeddings.py` |
| API types contract | `frontend/src/types/index.ts` |
| All frontend API calls | `frontend/src/lib/api.ts` |
| Auth hook | `frontend/src/hooks/useAuth.ts` |
| Guide viewer (quiz, associations, reflection) | `frontend/src/app/(dashboard)/guide/[id]/page.tsx` |
| Settings + billing | `frontend/src/app/(dashboard)/settings/page.tsx` |
| Stripe activation endpoint | `backend/app/routers/billing.py` (`activate_checkout_session`) |
| Reflection sync | `frontend/src/components/guide/ReflectionSection.tsx` |

---

## Agent Usage Guide

This workspace defines custom agents for structured work. **Use them.** Manual agent work increases context pollution and error rate.

### When to Use Each Agent

| Agent | Trigger | What It Does |
|-------|---------|-------------|
| `@planner` | Before any non-trivial feature | Writes a step-by-step plan to `.github/PLAN.md` |
| `@implementer` | After `@planner` finishes | Reads `.github/PLAN.md`, implements everything with zero placeholders |
| `@auditor` | After `@implementer` finishes | Reviews code for security, correctness, conventions — produces checklist report |
| `@phase3-implementer` | End-to-end Phase 3 slices spanning multiple layers | Implements coordinated Pro and billing features across backend, frontend, DB, and external flow |
| `@Explore` | When you need to understand existing code | Fast read-only Q&A without polluting main context |
| `@knowledge-curator` | Periodic (monthly or after major changes) | Keeps `.github/instructions/` in sync with codebase reality |

### Example Workflows

**Adding a new feature:**
```
1. @planner "Add semantic search to the guide library"
   → Writes plan to .github/PLAN.md
2. @implementer
   → Implements everything in the plan
3. @auditor
   → Reviews and produces a checklist
```

**Exploring before editing:**
```
@Explore "How does the quiz generation flow work from API to frontend?" (medium thoroughness)
→ Returns summary without clogging context with dozens of file reads
```

**Checking current state before starting a session:**
```
@Explore "What is incomplete or broken in the Phase 3 implementation?" (thorough)
```

## Workflow Notes

- Start substantial work from `.github/CONTEXT.md`, then use `.github/WORKFLOW.md` to choose the right role.
- Use `.github/RAG-INDEX.md` to find the authoritative file for a question instead of duplicating guidance.
- Keep pre-billing checkpoint work and Stripe activation work in separate commits.

---

## Phase 4 — Next Steps

Priority order for Phase 4 (when ready):

1. **Interactive demo** — pre-generated guide reachable without signup at `/demo`
2. **Security audit** — CSP headers, HTTPS enforcement, env var audit, rate-limit hardening
3. **E2E tests** — Playwright: signup → generate → view guide → quiz flow
4. **CI/CD** — GitHub Actions: lint, type-check, pytest on PR; deploy on merge to main
5. **Observability** — UptimeRobot health check, PostHog or Plausible analytics
6. **Performance** — Core Web Vitals audit, image optimization, bundle analysis
7. **Launch checklist** — Legal pages (Privacy, Terms), README polish, product hunt post

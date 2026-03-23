# Audit Report: Stripe Post-Payment Tier/Credits Fix
Date: March 23, 2026

## Summary
NEEDS FIXES — two post-implementation regressions found; core Stripe upgrade logic is correct but one will break the Next.js build.

## Findings

### [HIGH] `useSearchParams` used without a Suspense boundary in settings/page.tsx
- File: `frontend/src/app/(dashboard)/settings/page.tsx` line 4, 33
- Issue: `useSearchParams()` is called directly inside `SettingsPage`, the default-exported component. Next.js App Router requires that any Client Component calling `useSearchParams` must be wrapped in a `<Suspense>` boundary, or be an inner component rendered by a wrapper that provides one. Without it, Next.js will throw a build-time error or silently de-opt the entire route from static rendering, depending on the Next.js version. The login page (`app/(auth)/login/page.tsx`) demonstrates the correct pattern: an inner `LoginForm` component calls `useSearchParams` and the default export wraps it in `<Suspense>`.
- Fix: Extract the component body into an inner function `SettingsContent` that calls `useSearchParams`, then have `SettingsPage` (the default export) import `Suspense` from React and render `<Suspense><SettingsContent /></Suspense>`.

### [HIGH] `auditor.agent.md` mojibake fix regressed — encoding is now worse
- File: `.github/agents/auditor.agent.md` line 51 (and several others)
- Issue: The previous fix attempted to replace `â€"` with `—` but the file now contains `Ã¢â‚¬â€` — a different and more severely corrupted encoding sequence. The fix did not solve the problem; it introduced a deeper encoding corruption. The file needs to be written fresh with explicit UTF-8 encoding using `[System.IO.File]::WriteAllText(path, content, [System.Text.Encoding]::UTF8)` on Windows, or the affected lines must be patched via a tool that preserves the encoding correctly.
- Fix: Re-apply the em-dash fix using a write tool with explicit UTF-8 encoding (no BOM). Replace every occurrence of `Ã¢â‚¬â€` with `—` (U+2014).

### [MEDIUM] Reconciliation response returns stale `credits_used` in same request
- File: `backend/app/routers/billing.py` line 161, 176
- Issue: When `get_billing_status` reconciles a user from core to pro, it sets `credits_used = 0` in the DB but only updates `profile["tier"]` and `profile["daily_credit_limit"]` in memory. The line `credits_used = profile.get("credits_used", 0)` further down still reads the old (non-zero) value. The same HTTP response returns incorrect `credits_used` and `credits_remaining` for that call. In practice the settings page discards this response and immediately calls `refresh()` → `GET /api/credits`, so the user never sees it — but any caller relying on the `/api/billing/status` response for credits state will get a stale value.
- Fix: After `profile["daily_credit_limit"] = update_fields["daily_credit_limit"]`, add `if "credits_used" in update_fields: profile["credits_used"] = update_fields["credits_used"]`.

### [LOW] `_handle_subscription_updated` does not reset `credits_used` on renewal
- File: `backend/app/routers/webhooks.py` line 119-122
- Issue: When `customer.subscription.updated` fires with `status == "active"` (monthly renewal), the update sets `tier` and `daily_credit_limit` but does not reset `credits_used`. This is inconsistent with `_handle_checkout_completed`. On renewal day, the daily credit reset logic in `credits.py` would already have reset `credits_used`, so this is unlikely to be visible, but the inconsistency is worth noting.
- Fix: Add `"credits_used": 0` to the update dict in the `status == "active"` branch of `_handle_subscription_updated` for symmetry.

## What Was Correct

The three core Stripe upgrade bugs were fixed correctly:
- `_handle_checkout_completed` now resets `credits_used` to 0 on upgrade ✅
- `billing.py` reconciliation now also sets the correct `daily_credit_limit` ✅  
- `settings/page.tsx` now triggers backend reconciliation + UI refresh on `?upgraded=true` ✅
- `worker.py` now logs `guide_model` (actual model used) instead of `settings.guide_model` ✅

## Checklist

### Security
- [x] No secrets in frontend code or NEXT_PUBLIC_ vars (except Supabase anon/url)
- [x] No SQL string interpolation with user input
- [x] Stripe webhooks verified with `stripe.Webhook.construct_event()`
- [ ] Stripe webhook idempotency check via `stripe_events` table — **pre-existing gap, not introduced by this change**
- [x] No direct Supabase service key exposed to client
- [x] RLS not bypassed except in webhooks/worker with service key

### Backend Conventions
- [x] No `print()` — only `structlog.get_logger()`
- [x] No bare `Exception` — custom handling only
- [x] No raw dicts from routes — Pydantic response models used
- [x] No direct `AsyncClient` instantiation — uses `get_supabase()`
- [x] No inline prompts
- [x] `structlog` binds user_id in affected calls

### Frontend Conventions
- [ ] `useSearchParams` without Suspense boundary — **HIGH, see finding above**
- [x] All API calls go through `lib/api.ts` `apiFetch<T>()`
- [x] Types defined in `types/index.ts`
- [x] No inline styles — Tailwind classes only

### Correctness
- [x] Acceptance criteria from the bug report satisfied (tier/credits update after payment)
- [x] `log_api_usage` now uses actual selected model
- [ ] Frontend build not run after settings/page.tsx change — must verify `pnpm build` passes

## Verdict
NEEDS FIXES — resolve the HIGH findings (Suspense boundary and auditor.agent.md re-corruption), then the implementation is ready.

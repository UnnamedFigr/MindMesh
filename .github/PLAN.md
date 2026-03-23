---
description: "Model routing hardening — replace gpt-4.1 with gpt-5.4-mini, fix per-model context budgets, clean stale comments."
---

<!-- This file is the active plan artifact for the model-routing hardening slice. -->

# Plan: Model Routing Hardening (Local-First, 4-Hour Stability)

## Context
`gpt-4.1` is the current `guide_model_long` but the codebase has accumulated stale references to
`gpt-4.1-mini`, `gpt-4o-mini` (hardcoded in generator fallback), and outdated pricing comments.
The app runs local-only (Render dropped due to datacenter IP bot-detection).
Priority: maximum stability for 4-hour videos. `gpt-5.4-mini` (400K context, $0.75/$4.50 per 1M)
replaces `gpt-4.1` as the long-guide model.

## Done
- [x] Added `youtube_cookies_b64` field to `Settings` (fixes startup ValidationError).
- [x] InnerTube direct-API bypass (step 2 in transcript waterfall) — committed `17fa323`.
- [x] yt-dlp mobile player_client format error fix — committed `ceb349f`.
- [x] Switched `guide_model_long` from `gpt-4.1` to `gpt-5.4-mini`.
- [x] Added `_safe_transcript_budget()` and `_max_tokens_kwarg()` in `generator.py`.
- [x] Replaced the hardcoded fallback override with `settings.guide_model_long`.
- [x] Updated `worker.py`, `tokens.py`, `triage.py`, and guidance docs.
- [x] Verified backend tests (`56/56`) and frontend production build.

## Remaining
- [ ] Run the auditor pass on the completed slice.

## Acceptance Criteria
- [x] Backend starts and all 56 tests pass after every change.
- [x] `get_settings().guide_model_long` returns `"gpt-5.4-mini"`.
- [x] `generator.py` uses `settings.guide_model_long` instead of a hardcoded fallback model.
- [x] Per-model transcript budget helper exists and is used instead of a generic OpenAI check.
- [x] No active routing logic references `gpt-4.1-mini` or `gpt-4o-mini`.
- [x] Documentation files reflect the current model routing table.

## Tasks

### Task 1 — Update `guide_model_long` in config
- Files: `backend/app/config.py`
- What: Change default from `"gpt-4.1"` to `"gpt-5.4-mini"`.
- Why: `gpt-5.4-mini` has 400K context vs gpt-4.1's 1M but is cheaper and sufficient; better cost/stability for 4-hour single-pass.

### Task 2 — Fix generator.py fallback model and per-model budgets
- Files: `backend/app/services/generator.py`
- What:
  a. Add `_safe_transcript_budget(model_name) -> int` helper returning 200_000 for gpt-5.* / gpt-4.* and 90_000 for Groq.
  b. Replace `model_name = "gpt-4o-mini"` in `single_pass_fallback` branch with `settings.guide_model_long`.
  c. Replace `is_openai_model / max_transcript_tokens` block with call to `_safe_transcript_budget`.
  d. Update the "save cost" comment to reflect the current decision.

### Task 3 — Fix worker.py stale comments and cost estimate
- Files: `backend/app/services/worker.py`
- What:
  a. Update the "Step 4b" routing comment to say `gpt-5.4-mini` instead of `GPT-4.1`.
  b. Update `_estimate_cost()` stale comment and pricing values to `gpt-5.4-mini` ($0.75/$4.50 per 1M).

### Task 4 — Fix tokens.py docstring
- Files: `backend/app/utils/tokens.py`
- What: Update `get_processing_strategy` docstring to remove `GPT-4.1` / `GPT-4o-mini` references.

### Task 5 — Rewrite model section in IMPLEMENTATION_PLAN.md
- Files: `project-documentation/IMPLEMENTATION_PLAN.md`
- What: Replace any "Why Not GPT-4.1-mini" / stale model table with current routing and rationale.

### Task 6 — Update guidance files
- Files: `.github/CONTEXT.md`, `.github/copilot-instructions.md`, `.github/instructions/backend-python.instructions.md`
- What: Update model routing table to show `gpt-5.4-mini` for long guides.

## Risks
- Generator fallback currently silently overrides the model the worker chose; Task 2 fixes this.
- Pricing in `_estimate_cost` is monitoring-only (not billed), so wrong values are observability debt, not a billing bug.

## Validation
- `cd backend && pytest -v` must pass after each task.
- Manual: confirm `get_settings().guide_model_long == "gpt-5.4-mini"` after Task 1.

## Out Of Scope
- Stripe activation remains excluded from this slice.
- chunk-and-merge restoration deferred — gpt-5.4-mini's 400K context handles ≤200K transcripts in one pass.
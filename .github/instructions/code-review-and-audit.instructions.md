# Code Review And Audit Instructions

Use this file when reviewing a completed slice, preparing an audit handoff, or updating the repo's review rubric.

## Review Order
1. Read `.github/CONTEXT.md` for current phase status and known gotchas.
2. Read `.github/PLAN.md` for the intended scope.
3. Read the relevant layer instructions for the changed files.
4. Review changed files against correctness, security, conventions, and validation evidence.

## Required Review Checks

### Correctness
- The implemented slice satisfies the acceptance criteria in `.github/PLAN.md`.
- The changed files match the intended scope and do not hide unrelated edits.
- Error paths are handled explicitly for external calls and persistence operations.

### Security
- No secrets are added to tracked frontend files or `NEXT_PUBLIC_*` variables beyond allowed public values.
- Stripe webhooks verify signatures and avoid duplicate processing.
- User-scoped data remains protected by existing RLS and auth boundaries.

### Backend Conventions
- `structlog` is used instead of `print()`.
- Response models remain explicit and typed.
- Prompt text remains in Jinja2 templates, not inline strings.
- New persistence behavior checks Supabase responses instead of assuming success.

### Frontend Conventions
- API calls flow through `frontend/src/lib/api.ts`.
- No inline styles or ad hoc type drift are introduced.
- Client components are only used where browser APIs or event handlers require them.

### Database And Data Contracts
- Schema changes have migrations.
- Backend and frontend type contracts remain aligned.
- Relationship-dependent queries are backed by actual database constraints.

## Severity Guidance
- `CRITICAL`: security flaw, secret leak, data corruption risk, or exploitable auth issue
- `HIGH`: functional bug, broken contract, or strong convention violation likely to cause regressions
- `MEDIUM`: maintainability issue, missing validation, or partial workflow drift
- `LOW`: minor style or documentation gap that does not block merge

## Output Guidance
- Findings come first, ordered by severity.
- Keep summaries short.
- If no findings exist, say so explicitly and still note residual risk or test gaps.

## Update Triggers
- Repeated audit findings of the same class
- New security-sensitive subsystem
- Review rubric drift between agent files and repo instructions

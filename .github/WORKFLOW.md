# MindMesh Workflow

This file defines the operational workflow for the repository.
Read this before assigning work to an agent or changing project instructions.

## Source Of Truth
- `.github/CONTEXT.md` is the authoritative current-state document.
- `.github/PLAN.md` is the current task specification for the active implementation slice.
- `.github/error-patterns.md` is the anti-pattern catalog used during review.
- `.github/instructions/*.md` define layer-specific implementation rules.
- `.github/RAG-INDEX.md` is the retrieval map that points to the right source file.

## Role Assignment
- `@Explore`: use for read-only discovery, architecture tracing, and codebase Q&A before planning.
- `@planner`: use for any non-trivial feature, bug, refactor, or workflow-hardening slice that needs a task artifact in `.github/PLAN.md`.
- `@implementer`: use for normal execution after a plan exists.
- `@phase3-implementer`: use only for end-to-end Phase 3 slices that cross backend, frontend, database, and external billing or ops boundaries.
- `@auditor`: use after implementation completes and validation passes.
- `@knowledge-curator`: use after recurring findings, architecture shifts, or major framework changes to keep instructions and anti-pattern guidance aligned.

## Required Sequence
1. Read `.github/CONTEXT.md`.
2. Use `@Explore` if the change area is unclear.
3. Use `@planner` to write or refresh `.github/PLAN.md` for non-trivial work.
4. Use `@implementer` or `@phase3-implementer` to execute the plan.
5. Run validation for the touched layers.
6. Use `@auditor` to review the implemented slice.
7. Update `.github/CONTEXT.md` if the architecture, phase status, or known gotchas changed.
8. Use `@knowledge-curator` when the instruction layer needs maintenance, not for routine implementation.

## When To Use Phase3-Implementer
Use `@phase3-implementer` when the slice includes at least two of these together:
- backend Pro data contracts or worker-pipeline changes
- frontend Pro UI and API integration changes
- database migrations or billing-related persistence changes
- Stripe checkout, portal, webhook, or subscription state work

Do not use `@phase3-implementer` for isolated docs, simple bug fixes, or single-layer refactors.

## Commit Policy
- Keep the current pre-billing checkpoint separate from the later Stripe activation commit.
- Do not mix workflow or instruction hardening with payment setup in the same commit.
- Never commit local secrets or `.env.local`.

## Validation Policy
- Backend changes: `cd backend && pytest -v`
- Frontend changes: `cd frontend && pnpm build`
- Frontend behavioral or UI changes: `cd frontend && pnpm lint`
- Workflow or doc-only changes: manually verify links, role definitions, and source-of-truth references

## Retrieval Policy
- Prefer linking to an authoritative file instead of repeating a full rule in multiple docs.
- If a question is about current project reality, answer from `.github/CONTEXT.md` first.
- If a question is about implementation conventions, answer from the relevant instruction file.
- If a question is about review failures or forbidden patterns, answer from `.github/error-patterns.md`.

## IDE And Skill Baseline
Recommended local VS Code extensions:
- GitHub Copilot Chat
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- PostCSS Language Support
- Markdown All in One

Recommended repo capabilities to keep available:
- `@Explore`, `@planner`, `@implementer`, `@auditor`, `@knowledge-curator`, `@phase3-implementer`
- knowledge-bridge workflow for instruction maintenance

Machine-wide installation is environment-specific and should be performed locally, but this list is the repo baseline.

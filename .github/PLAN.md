---
description: "Current implementation plan and checkpoint status for the pre-billing workflow-hardening pass."
---

<!-- This file is the active plan artifact for the current workflow-hardening slice. -->

# Plan: Pre-Billing Checkpoint And Workflow Hardening

## Context
MindMesh already has the Phase 3 backend foundation, real-auth fixes, backend stability fixes, and the library join fix. What is still missing before the Stripe activation commit is a consistent workflow layer that records what is done, what remains, and where future agents should retrieve authoritative guidance.

## Done
- [x] Fixed real-auth guide generation and restored backend responsiveness.
- [x] Added dev-mode request routing via request-scoped DevStore behavior.
- [x] Fixed the library query by adding the `study_guides.video_id -> videos.youtube_id` foreign key migration.
- [x] Verified backend tests and frontend build after the Phase 3 stabilization changes.
- [x] Added frontend visibility for library fetch failures instead of silent empty-state debugging.
- [x] Replaced the placeholder planning artifact with a durable status and execution plan.
- [x] Added a central workflow document for agent role selection and handoffs.
- [x] Added a retrieval index and missing instruction files for retrieval hygiene and audit/review.
- [x] Updated agent definitions to read `.github/CONTEXT.md` first and align on a shared workflow.
- [x] Updated `.github/CONTEXT.md` so workflow entry points and `phase3-implementer` are discoverable.

## Remaining
- [ ] Keep Stripe product creation, price configuration, checkout validation, and webhook activation out of this commit.

## Acceptance Criteria
- [x] `.github/PLAN.md` records both completed work and remaining pre-billing work.
- [x] `.github/WORKFLOW.md` exists and describes the required role-based workflow for this repo.
- [x] `.github/RAG-INDEX.md` exists and maps common questions to authoritative files.
- [x] Retrieval and audit instruction files exist under `.github/instructions/`.
- [x] Planner, implementer, auditor, knowledge-curator, and phase3-implementer explicitly read `.github/CONTEXT.md` before substantial work.
- [x] `.github/CONTEXT.md` documents the workflow entry points and the role of `phase3-implementer`.
- [ ] Stripe activation remains explicitly excluded from this slice and left for the next commit.

## Tasks
### Task 1 — Replace Placeholder Planning With A Real Status Artifact
- Files: `.github/PLAN.md`
- What: Record what has already been completed, what remains before payment activation, the acceptance criteria for this slice, and the implementation/verification steps.
- Contracts: No application contracts change; this is a workflow artifact change only.

### Task 2 — Add Workflow And Retrieval Entry Points
- Files: `.github/WORKFLOW.md`, `.github/RAG-INDEX.md`
- What: Create one document that defines the operational workflow and one document that maps questions to authoritative files for retrieval.
- Contracts: Document-level contract only; no runtime code paths change.

### Task 3 — Fill Missing Instruction Gaps
- Files: `.github/instructions/rag-and-retrieval.instructions.md`, `.github/instructions/code-review-and-audit.instructions.md`
- What: Add specific instructions for retrieval hygiene, source-of-truth usage, and consistent audit/review execution.
- Contracts: Instruction-layer contract only; no backend/frontend/database runtime changes.

### Task 4 — Align Agent Definitions With The Workflow
- Files: `.github/agents/planner.agent.md`, `.github/agents/implementer.agent.md`, `.github/agents/auditor.agent.md`, `.github/agents/knowledge-curator.agent.md`, `.github/agents/phase3-implementer.agent.md`
- What: Make every major agent read `.github/CONTEXT.md` first, align the workflow and handoff expectations, and clarify when `phase3-implementer` should be used instead of the generic implementer.
- Contracts: Agent prompt contract changes only.

### Task 5 — Update Current Project Context
- Files: `.github/CONTEXT.md`
- What: Add the new workflow docs to the key file map, add `phase3-implementer` to the agent usage guide, and document the new context-first retrieval workflow.
- Contracts: Context documentation only.

## Risks
- Workflow docs drifting from reality: mitigate by keeping `.github/CONTEXT.md` authoritative and linking from all new docs instead of duplicating detailed architecture.
- Over-documenting the same rule in multiple places: mitigate by making `.github/RAG-INDEX.md` a router to authoritative sources, not a second copy.
- Accidental scope creep into Stripe activation: mitigate by explicitly keeping env and price setup out of this slice.

## Validation
- Docs: confirm all new workflow docs reference existing files and match the current repo layout.
- Agents: read each updated agent file and verify `.github/CONTEXT.md` is a required first step.
- Repo hygiene: ensure `.env.local` remains ignored and no payment env var is added in this slice.
- Manual: confirm the remaining Stripe work is clearly isolated as the next commit.

## Stripe Activation Scope (Explicitly Out Of This Commit)
- Create the Stripe product and recurring price in the Stripe Dashboard.
- Set `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID` in `frontend/.env.local`.
- Run checkout, portal, webhook, and billing-status reconciliation tests.
- Commit payment-system activation in the next commit only.

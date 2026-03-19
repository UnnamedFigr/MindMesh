# MindMesh Retrieval Index

Use this file to route questions to the right authoritative source.
Do not duplicate long-form guidance here; point to the real file.

## Current Project State
- Phase status, decisions, gotchas, next steps: `.github/CONTEXT.md`
- Global repo rules and conventions: `.github/copilot-instructions.md`
- Active implementation slice: `.github/PLAN.md`

## Workflow And Agents
- Role selection and handoff order: `.github/WORKFLOW.md`
- Planner role: `.github/agents/planner.agent.md`
- Implementer role: `.github/agents/implementer.agent.md`
- Auditor role: `.github/agents/auditor.agent.md`
- Knowledge-curator role: `.github/agents/knowledge-curator.agent.md`
- Specialized Phase 3 execution: `.github/agents/phase3-implementer.agent.md`

## Implementation Rules By Layer
- Backend/FastAPI/Pydantic/services: `.github/instructions/backend-python.instructions.md`
- Frontend/Next.js/React/Tailwind: `.github/instructions/frontend-react.instructions.md`
- Supabase/database/migrations/RLS: `.github/instructions/database.instructions.md`
- Testing/verification commands: `.github/instructions/testing.instructions.md`
- Retrieval hygiene and document indexing: `.github/instructions/rag-and-retrieval.instructions.md`
- Review and audit rubric: `.github/instructions/code-review-and-audit.instructions.md`

## Common Questions
- How does auth work today? `.github/CONTEXT.md`, then `backend/app/dependencies.py`
- Where do I change API contracts? `backend/app/models/requests.py`, `backend/app/models/responses.py`, and `frontend/src/types/index.ts`
- How should a new endpoint be added? `.github/instructions/backend-python.instructions.md` and `.github/prompts/add-endpoint.prompt.md`
- How should a migration be added? `.github/instructions/database.instructions.md` and `.github/prompts/add-migration.prompt.md`
- Where are repeated mistakes tracked? `.github/error-patterns.md`
- How should a review be run? `.github/instructions/code-review-and-audit.instructions.md` and `.github/agents/auditor.agent.md`
- When should knowledge-curator run? `.github/WORKFLOW.md` and `.github/agents/knowledge-curator.agent.md`
- When should phase3-implementer be used? `.github/WORKFLOW.md` and `.github/agents/phase3-implementer.agent.md`

## Retrieval Rules
- Start with `.github/CONTEXT.md` for current reality.
- Route to one authoritative file per question whenever possible.
- Update this index when a new source-of-truth document is added.

---
agent: agent
description: "Implement the next Phase 3 feature slice for MindMesh Pro features. Use when picking up Phase 3 work: quiz, associations, Stripe billing, or frontend Pro UI."
---

Implement the next Phase 3 slice for MindMesh, working autonomously end-to-end.

## Process

### 1. Orient: Read the Plan & Current State
- Read `plan-phase3RealityBasedExecution.prompt.md` for the full plan
- Run `cd backend && pytest -v` to see which tests pass today
- Check current git branch and status

### 2. Identify the Highest-Priority Incomplete Item
Phase 3 priority order:
1. Add `quiz: list[QuizQuestion]` to `StudyGuidePro` in `backend/app/prompts/schemas.py`
2. Wire worker Pro pipeline: quiz generation → associations → reflection persistence
3. Backend APIs: `GET /api/guides/{id}/associations`, `POST /api/quiz/{id}/submit`
4. Frontend: render `<QuizCard>` and `<AssociationsList>` on guide page
5. Stripe checkout/portal endpoints; billing activation

### 3. Implement the Slice
Follow all conventions from:
- `.github/instructions/backend-python.instructions.md`
- `.github/instructions/frontend-react.instructions.md`
- `.github/instructions/database.instructions.md`

Key contracts:
- `StudyGuidePro.quiz` shape: `[{ question, options: [str x4], correct_index, explanation }]`
- `associations` table: `guide_id_a, guide_id_b, similarity_score, user_id`
- DB access: always `db = Depends(get_db)`, never instantiate directly
- Logging: `structlog.get_logger()`, bind `user_id` and `job_id`

### 4. Validate
- `cd backend && pytest -v` — all must pass
- `cd frontend && pnpm build` — must exit 0
- `cd frontend && pnpm lint` — no errors

### 5. Commit
- Use git-commit skill or commit manually with conventional commit message
- Branch: `feature/phase3-<slice-name>` from `dev`

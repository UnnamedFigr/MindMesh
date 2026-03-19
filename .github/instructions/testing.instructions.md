---
description: "Use when writing, running, or modifying tests. Covers pytest for backend, test patterns, and verification commands."
applyTo: "backend/tests/**"
---
# Testing Conventions

## Backend Tests (pytest)
- Tests in `backend/tests/` — mirror the `app/` structure
- Run: `cd backend && pytest -v`
- Naming: `test_<module>.py` → `test_<function_name>()`
- Existing tests: `test_tokens.py`, `test_youtube.py`, `test_credits.py`, `test_errors.py`
- Mock external services (OpenAI, Groq, Supabase) — never make real API calls in tests
- Use `pytest.raises(MindMeshError)` for error path testing

## Frontend Verification
- Build check: `cd frontend && pnpm build` (must exit 0)
- Lint: `cd frontend && pnpm lint`
- No test framework currently configured — use build + lint as validation

## After Every Change
- Backend changes → run `pytest -v`
- Frontend changes → run `pnpm build` and `pnpm lint`
- Both → run the relevant commands for each side

## Mocking Supabase (`get_db` singleton)
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.dependencies import get_db

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": "test-id"}]))
    return db

# In test:
app.dependency_overrides[get_db] = lambda: mock_db
```

## Mocking Worker Dependencies
- Mock `generate_study_guide` to return a fixed `StudyGuideCore` dict
- Mock `fetch_transcript` with `AsyncMock(return_value=("transcript text", []))`
- Mock `triage_content` with a fixed `TriageResult` dict
- Never let worker tests hit real APIs or Supabase

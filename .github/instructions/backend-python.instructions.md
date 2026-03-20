---
description: "Use when writing, modifying, or reviewing Python backend code in the backend/ directory. Covers FastAPI patterns, Pydantic models, service architecture, error handling, and LLM integration."
applyTo: "backend/**/*.py"
---
# Backend Python Conventions

## FastAPI Patterns
- All routes use `async def` with proper `Depends()` injection
- Auth: `user = Depends(get_current_user)` on all protected endpoints
- Rate limiting: `Depends(check_rate_limit)` on creation endpoints
- Return Pydantic response models — never raw dicts
- Use `status_code=202` for async job creation, `200` for reads

## Error Handling
- Raise `MindMeshError` subclasses (never generic `Exception` or `HTTPException`)
- Hierarchy: `ValidationError(400)`, `TranscriptError(422)`, `TriageError(422)`, `GenerationError(502)`, `CreditError`, `RateLimitError`, `AuthError`
- All errors include `code` (machine-readable) and `user_message` (human-readable)
- Wrap LLM/API calls with tenacity: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))`

## Pydantic Models
- Request models in `models/requests.py`, response models in `models/responses.py`
- LLM output schemas in `prompts/schemas.py` — used with OpenAI Structured Outputs
- Always use `model_config = SettingsConfigDict(...)` for BaseSettings

## LLM Integration
- Groq uses OpenAI-compatible SDK (`base_url="https://api.groq.com/openai/v1"`)
- Prompts are Jinja2 templates in `prompts/templates/` — never hardcode prompts
- Token counting via `tiktoken` with `cl100k_base` encoding
- Route by token count: <13K → Groq Llama 4 Scout, ≥13K → OpenAI GPT-4.1

## Logging
- Use `structlog.get_logger()` — never `print()` or `logging.getLogger()`
- Always bind context: `log = log.bind(user_id=user_id, job_id=job_id)`

## Database (Supabase)
- Dev mode: `DevStore` (in-memory) when Supabase keys are placeholders
- Production: Supabase client with PostgREST builder pattern
- Always use `.execute()` and check response — Supabase errors are silent
- RLS enforced on all tables — service key bypasses RLS for admin operations

## Phase 3 Patterns

### Extending the Worker Pipeline (`services/worker.py`)
- After `render_guide_markdown()`, add Pro steps inside `if tier == "pro":` block
- Call `generate_quiz()` from `services/generator.py` → persist to `study_guides.guide_json["quiz"]`
- Call `compute_associations()` from `services/embeddings.py` → persist to `associations` table
- Call `persist_reflection()` if reflection text provided

### Pro Schema Extension (`prompts/schemas.py`)
- `StudyGuidePro(StudyGuideCore)` — add `quiz: list[QuizQuestion]` field
- `QuizQuestion` model: `{ question, options: list[str], correct_index: int, explanation }`
- All Pydantic validators must use `mode="before"` when cleaning LLM output

### Stripe Webhooks (`routers/webhooks.py`)
- Always verify `stripe.Webhook.construct_event()` before processing
- Idempotency: check `stripe_events` table before acting; insert after processing
- Update `users.tier` and `users.credits_remaining` via service key (bypasses RLS)
- Never use `db = Depends(get_db)` inside `webhooks.py` — use direct service key client

### Embeddings & Associations (`services/embeddings.py`)
- Use `text-embedding-3-small` (512 dims) for all guide chunks
- Store in `guide_embeddings` table; associations computed via pgvector cosine similarity
- Call `compute_and_store_associations(guide_id, user_id, db)` after guide generation

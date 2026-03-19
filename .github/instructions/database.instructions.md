---
description: "Use when writing SQL migrations, querying Supabase, designing RLS policies, or working with pgvector embeddings."
applyTo: "backend/migrations/**,backend/app/services/embeddings.py,backend/app/services/dev_store.py"
---
# Database Conventions (Supabase / Postgres)

## Migration File Naming
- Format: `YYYYMMDD_description.sql` (e.g., `20260312_add_quiz_to_guides.sql`)
- Files live in `backend/migrations/`
- Each migration must be idempotent: use `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`
- Never DROP or TRUNCATE in migrations — only ADD or ALTER

## Table & Column Conventions
- snake_case for all table and column names
- Every table has: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`
- Foreign keys: `user_id UUID REFERENCES users(id) ON DELETE CASCADE`
- Use `JSONB` for flexible/nested data (`guide_json`, `metadata`)
- Use `TEXT` not `VARCHAR` — no length limits unless required by business rule

## Row-Level Security (RLS)
- RLS must be enabled on ALL user-data tables: `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;`
- Standard user policy pattern:
  ```sql
  CREATE POLICY "users_own_rows" ON <table>
    FOR ALL USING (auth.uid() = user_id);
  ```
- Service-key operations (backend) bypass RLS — use only for admin/worker tasks
- Never expose service key to frontend — only anon key is safe in `NEXT_PUBLIC_`

## pgvector Usage
- Extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Embedding column: `embedding vector(512)` (text-embedding-3-small, 512 dims)
- Similarity search (cosine): `ORDER BY embedding <=> $1 LIMIT 5`
- Always create an IVFFLAT or HNSW index for production:
  ```sql
  CREATE INDEX ON guide_embeddings USING hnsw (embedding vector_cosine_ops);
  ```

## Key Tables Quick Reference
| Table | Key Columns |
|-------|-------------|
| `users` | `id`, `tier` (free/core/pro), `credits_remaining`, `stripe_customer_id` |
| `jobs` | `id`, `user_id`, `status` (pending/processing/completed/failed), `progress`, `result_id` |
| `study_guides` | `id`, `user_id`, `video_id`, `guide_json` (JSONB), `guide_markdown`, `tier`, `persona` |
| `guide_embeddings` | `id`, `guide_id`, `chunk_index`, `chunk_text`, `embedding vector(512)` |
| `associations` | `id`, `guide_id_a`, `guide_id_b`, `similarity_score`, `user_id` |
| `reflections` | `id`, `guide_id`, `user_id`, `question`, `answer` |
| `credit_transactions` | `id`, `user_id`, `delta`, `reason`, `job_id` |
| `stripe_events` | `id`, `stripe_event_id` (UNIQUE), `processed_at` |

## Supabase Client Patterns (Python)
```python
# SELECT with filter
result = await db.table("study_guides").select("*").eq("user_id", user_id).execute()
rows = result.data  # list[dict]

# INSERT
result = await db.table("jobs").insert({"user_id": user_id, "status": "pending"}).execute()
new_id = result.data[0]["id"]

# UPDATE
await db.table("jobs").update({"status": "completed"}).eq("id", job_id).execute()

# UPSERT (idempotent insert)
await db.table("stripe_events").upsert({"stripe_event_id": event_id}).execute()
```

## pg_cron (Scheduled Jobs)
- Used for monthly credit reset: defined in `migrations/20260311_add_credit_reset_cron.sql`
- Never add pg_cron jobs from application code — migrations only

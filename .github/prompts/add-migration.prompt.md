---
agent: agent
description: "Create a new Supabase SQL migration for MindMesh. Use when adding a table, column, index, RLS policy, or pg_cron job."
---

Create a new SQL migration for the MindMesh Supabase database.

## Input: What to Migrate
$MIGRATION_DESCRIPTION

## Step-by-Step Process

### 1. Read Existing Migrations
- Read all files in `backend/migrations/` to understand existing schema
- Identify the highest existing migration number for ordering

### 2. Create Migration File
- Filename: `YYYYMMDD_snake_case_description.sql` — use today's date
- Location: `backend/migrations/`

### 3. Migration Rules
- **Idempotent**: use `IF NOT EXISTS` for CREATE statements, `ON CONFLICT DO NOTHING` for inserts
- **Never DROP**: never drop columns, tables, or indexes in a migration
- **RLS required**: every new user-data table needs RLS enabled + user ownership policy
- **Timestamps**: every new table must have `created_at TIMESTAMPTZ DEFAULT NOW()`
- **UUIDs**: use `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`

### 4. Standard RLS Block (include for every new table)
```sql
ALTER TABLE "<table_name>" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_<table_name>" ON "<table_name>"
  FOR ALL USING (auth.uid() = user_id);
```

### 5. Update DevStore (if new table)
- Read `backend/app/services/dev_store.py`
- Add in-memory storage for the new table so dev mode still works

### 6. Verify
- SQL must be syntactically valid Postgres
- Run `cd backend && pytest -v` — ensure no tests broke

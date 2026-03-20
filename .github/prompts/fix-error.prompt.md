---
agent: agent
description: "Diagnose and fix a backend or frontend error in MindMesh. Use when given an error message, traceback, or broken test to investigate and resolve."
---

Systematically diagnose and fix the reported error.

## Input: The Error
$ERROR_OR_DESCRIPTION

## Diagnosis Process

### 1. Gather Context
- Identify which layer: backend Python, frontend TypeScript, or DB/migration
- Read the file where the error originates (traceback line numbers are authoritative)
- Read imported dependencies to understand expected contracts

### 2. Backend Errors
- Check Pydantic validation errors → look at schema in `prompts/schemas.py` or `models/`
- Check `MindMeshError` subclass hierarchy in `utils/errors.py` for correct error type
- Check for missing `await` on `async` Supabase calls
- Check `structlog` binding — missing `user_id`/`job_id` in context

### 3. Frontend Errors
- Check TypeScript type mismatch → compare `types/index.ts` with actual API response
- Check for missing `'use client'` on components using hooks or event handlers
- Check `apiFetch` usage — response type must match backend Pydantic model
- Check `pnpm build` output (not just dev server) for type errors

### 4. Fix
- Make the minimal change that resolves the error — do not refactor surrounding code
- Preserve existing behavior for non-error paths

### 5. Verify
- Backend: `cd backend && pytest -v`
- Frontend: `cd frontend && pnpm build && pnpm lint`
- Confirm the original error no longer reproduces

---
agent: agent
description: "Implement a new FastAPI endpoint with Pydantic models, frontend API client function, and TypeScript types. Use when asked to add a new API route, backend feature, or data endpoint."
---

Implement a new API endpoint end-to-end for the MindMesh project following these exact conventions:

## Input: What to Build
$ENDPOINT_DESCRIPTION

## Step-by-Step Process

### 1. Read Before Writing
- Read `backend/app/models/responses.py` and `requests.py` to understand existing schemas
- Read `frontend/src/types/index.ts` to understand existing TypeScript types
- Read `frontend/src/lib/api.ts` to understand the `apiFetch` pattern
- Read the closest existing router in `backend/app/routers/` for the pattern to follow

### 2. Backend: Pydantic Schemas
- Add request model (if POST/PUT) to `backend/app/models/requests.py`
- Add response model to `backend/app/models/responses.py`
- Use `BaseModel` with field descriptions; all fields typed

### 3. Backend: Service Logic
- Create or update the relevant service in `backend/app/services/`
- Wrap DB calls with proper error handling using `MindMeshError` subclasses
- Use `structlog.get_logger()` for all logging — never `print()`
- Use `Depends(get_db)` for database access — never instantiate directly

### 4. Backend: Router
- Add route to the relevant file in `backend/app/routers/`
- Use `db: AsyncClient = Depends(get_db)` and `user = Depends(get_current_user)`
- Return the Pydantic response model — never a raw dict
- Use HTTP 200 for reads, 202 for async job creation, 201 for sync creation

### 5. Frontend: Types
- Add the TypeScript interface to `frontend/src/types/index.ts`
- Mirror the Pydantic model exactly: same field names (camelCase JS ↔ snake_case Python handled by the API)
- Note: the backend returns snake_case; frontend types should match the JSON wire format

### 6. Frontend: API Client
- Add a function to `frontend/src/lib/api.ts` using `apiFetch<T>()`
- Pattern: `export async function getXxx(id: string): Promise<XxxResponse>`

### 7. Verification
- Run `cd backend && pytest -v` — all tests must pass
- Run `cd frontend && pnpm build` — must exit 0

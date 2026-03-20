---
description: "Use when writing, modifying, or reviewing React/TypeScript frontend code. Covers Next.js 16 App Router, React 19 patterns, Tailwind CSS v4, Supabase Auth, and API integration."
applyTo: "frontend/src/**/*.{ts,tsx}"
---
# Frontend React/TypeScript Conventions

## Next.js 16 App Router
- Server Components by default — add `'use client'` only for event handlers, hooks, browser APIs
- Route groups: `(auth)` for login/signup, `(dashboard)` for protected routes
- Middleware in `src/middleware.ts` handles Supabase session refresh
- Use `revalidatePath()` after mutations — App Router caches aggressively

## React 19 Patterns
- Functional components only — no class components
- Custom hooks: `useAuth`, `useCredits`, `useJobStatus` in `hooks/`
- State: React hooks (`useState`, `useEffect`) + Zustand if needed
- Props: Destructure in function signature with TypeScript interfaces

## TypeScript
- Types in `types/index.ts` — keep in sync with backend Pydantic schemas
- `Persona = "beginner" | "academic" `
- `Tier = "free" | "core" | "pro"`
- `JobStatus = "pending" | "processing" | "completed" | "failed"`
- Never use `any` — prefer `unknown` and narrow with type guards

## API Integration
- All calls go through `lib/api.ts` → `apiFetch<T>()` wrapper
- Auto-injects Supabase JWT or dev token
- Demo/dev mode interceptors return mock data from `lib/demo.ts`
- Never call backend directly from components — always via api.ts functions

## Styling
- Tailwind CSS v4 utility classes only — no inline styles, no CSS modules
- Use `cn()` helper from `lib/utils.ts` for conditional classes
- Icons from `lucide-react` — consistent icon library
- Mobile-first responsive design

## Auth Modes
- Production: Supabase Auth (JWT in cookie)
- Dev: `mindmesh-dev` cookie → real backend, dev user
- Demo: `mindmesh-demo` cookie → mock data only

## Package Manager
- **pnpm only** — npm causes TAR_ENTRY_ERROR on Windows
- `pnpm install`, `pnpm dev`, `pnpm build`, `pnpm lint`

## Phase 3 Pro UI Patterns

### Pro Tier Gating
```tsx
// In any Pro-only section:
if (tier !== 'pro') {
  return <UpgradeCTA feature="quiz" />;  // or inline upgrade prompt
}
```

### Guide Page Rendering Contract (`app/(dashboard)/guide/[id]/page.tsx`)
- `guideData.guide_json` is the raw `StudyGuideCore | StudyGuidePro` object
- `guideData.tier` determines which sections to render
- Add new sections by appending after the existing `<ReflectionCard>` block
- Quiz: `guideData.guide_json?.quiz` → pass to `<QuizCard questions={...} />`
- Associations: fetched separately via `getAssociations(id)` from `lib/api.ts`

### Adding New API Client Functions (`lib/api.ts`)
- Pattern: `export async function getFoo(id: string): Promise<FooResponse>`
- Always use `apiFetch<T>(path, options)` — handles auth, dev/demo modes
- Types for responses must be defined in `types/index.ts` first

### Component Locations
- `components/guide/` — guide page-specific components (QuizCard, AssociationsList…)
- `components/ui/` — reusable primitives (Button, Card, Badge…)
- `components/forms/` — form components (GuideForm, SearchBar…)

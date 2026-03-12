# MindMesh Project Summary & Context

**Last Updated:** March 2026

This file serves as the definitive "regain context instantly" document for the MindMesh project. Feed this file to the AI assistant at the start of any new coding session to instantly align it with the project's current state, architecture, and immediate next steps.

---

## 🚀 Project Overview
MindMesh is a sophisticated web application that converts any YouTube video into a personalized, structured study guide in seconds. It uses a multi-model AI pipeline (Groq + Llama 3/4 + OpenAI GPT-4.1) and STT (Whisper) fallback to ensure fast, high-quality extractions. 

**Core Stack:**
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS v4, Zustand.
- **Backend:** Python 3.12+, FastAPI, Pydantic v2.
- **Database/Auth:** Supabase (Postgres, pgvector, pg_cron).
- **AI/LLM:** Groq (Llama-4-scout-17b/Whisper-large-v3-turbo) for speed, OpenAI (GPT-4.1) for massive context windows.
- **Monetization:** Stripe (planned for Phase 3).

---

## ✅ What's Completed (Phase 1 & Phase 2 - 100% Done)
We have successfully built the complete foundation and core pipeline of the application. The system is end-to-end operational for generating guides.

### Backend Achievements:
- **Triage & Pipeline Routing:** Built highly optimized multi-model routing. Short videos (<13k tokens) go to Groq (Llama 4 Scout) for rapid generation. Long videos go to OpenAI (GPT-4.1) or fallback to GPT-4o-mini to avoid rate limits/429 errors.
- **Transcript Extraction Strategy:** Waterfall approach: 1) DB Cache -> 2) YouTube Manual Captions -> 3) YouTube Auto Captions -> 4) Groq Whisper v3 fallback.
- **Auth & Database:** Supabase Auth is fully integrated. Profiles are auto-created via triggers. `pg_cron` is configured to automatically reset user credits daily at midnight.
- **Generative Quality & Prompting:** Refined output schemas and prompts using Jinja2 templates (Beginner, Academic, Practitioner). Fixed AI output regressions and schema definition bleed from Llama 4 Scout.
- **JWT Auth:** Fixed an issue where the JWT token was not correctly parsed/transmitted during video analysis (non-demo mode).

### Frontend Achievements:
- **Build Quality:** The Next.js frontend has a completely clean build (`Exit code 0`). Fixed all lingering strict TypeScript errors (e.g., `GuideJSON` QuickBrief typing), React Hook warnings (`useRef` vs `useEffect` in `useJobStatus.ts`), and HTML hydration errors (nested `<button>` logic swapped to accessible `<div>` roles in `ThemeBlock`).
- **UI/UX Polish:** 
  - fully implemented the `CreditsGate` component to gracefully handle and block 0-credit states (credits exhaustion UX).
  - Built `ThemeBlock` collapsible components to improve Guide Viewer readability on mobile.
  - Implemented clickable timestamps in the generated guide that correctly open YouTube to the specific time.

---

## 🚧 Current Status & Next Steps (Phase 3: Pro Features)
The remaining work is exclusively focused on **Phase 3 (Pro Features & Monetization)** and **Phase 4 (Launch Polish)**.

### Immediate Next Tasks (Phase 3):
1. **Stripe Integration & Webhooks:**
   - Integrate Stripe checkout for Pro tier subscriptions.
   - Build FastAPI `/api/webhooks/stripe` handlers to catch payment success and upgrade users in Supabase.
2. **Pro Feature: Active Recall Quizzes:**
   - Expose the Pro "Quizzes" UI in the Guide Viewer frontend.
   - Ensure the backend properly leverages `GPT-4.1-nano` to generate 3 targeted questions per study guide.
3. **Pro Feature: Semantic Search / Web of Associations:**
   - Finalize the `text-embedding-3-small` pipeline to embed concepts into `pgvector`.
   - Build UI to query and connect past study guides based on conceptual overlap.

## 🧠 Workflows & Conventions
- **Agent Workflow:** Always require Implementation Plans, Task Lists, and Walkthrough Artifacts before executing large features. Adhere to the Context-Task-Constraint framework.
- **Branch Isolation:** Each new feature (e.g., Stripe, Vector Search) must be built on an isolated Git branch, PR'd, and verified before merging to `dev`.
- **Testing:** Verify all components locally and ensure zero build/lint errors before committing. Ensure responsive UI design.

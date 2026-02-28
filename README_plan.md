# MindMesh

**YouTube → AI Study Guide Generator**

MindMesh converts any YouTube video into a personalized, structured study guide in seconds. Choose your learning persona (Beginner, Academic, or Practitioner), and our AI pipeline builds a guide tailored to your level.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start (Windows)](#quick-start-windows)
- [Quick Start (macOS / Linux)](#quick-start-macos--linux)
- [Environment Variables](#environment-variables)
- [Dev Mode (No Supabase)](#dev-mode-no-supabase)
- [Running the App](#running-the-app)
- [Project Structure](#project-structure)
- [Key Technologies](#key-technologies)
- [Troubleshooting](#troubleshooting)

---

## Architecture

| Layer | Tech | Purpose |
|-------|------|---------|
| Frontend | Next.js 16 (App Router), React 19, Tailwind CSS v4 | SSR landing page, SPA dashboard |
| Backend | FastAPI, Python 3.13, Pydantic v2 | API + async AI pipeline |
| Database | Supabase (Postgres + pgvector) | Auth, storage, vector search |
| AI (short videos) | Groq `llama-3.3-70b-versatile` | Fast guide generation (<30 min) |
| AI (long videos) | OpenAI `gpt-4.1` | Reliable generation (30+ min) |
| AI (triage) | Groq `llama-3.1-8b-instant` | Content classification |
| STT Fallback | Groq Whisper v3 Turbo | Audio transcription when captions unavailable |

---

## Prerequisites

Install these **before** cloning the project:

| Tool | Version | Install |
|------|---------|---------|
| **Node.js** | 22.x (LTS) | [nodejs.org](https://nodejs.org/) |
| **pnpm** | 10.x | `npm install -g pnpm` (after Node.js) |
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **Git** | any | [git-scm.com](https://git-scm.com/) |
| **ffmpeg** | any | [ffmpeg.org](https://ffmpeg.org/download.html) — needed for Whisper audio fallback |

> **Important:** This project uses **pnpm** for the frontend. Do NOT use npm — it will fail with TAR_ENTRY_ERROR on Windows.

---

## Quick Start (Windows)

```powershell
# 1. Clone the repo
git clone https://github.com/Kostakurta8/MindMesh.git
cd MindMesh

# 2. Set up the backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -e ".[dev]"

# 3. Create backend .env file
copy .env.example .env
# Then open backend\.env and fill in your API keys (see Environment Variables below)

# 4. Set up the frontend
cd ..\frontend
pnpm install

# 5. Create frontend .env.local file
copy .env.local.example .env.local
# Then open frontend\.env.local and fill in your values (see Environment Variables below)

# 6. Run everything (from project root)
cd ..
.\start.bat
```

The `start.bat` script opens two terminal windows:
- **Backend** on `http://localhost:8000`
- **Frontend** on `http://localhost:3000`

Visit `http://localhost:3000` in your browser.

---

## Quick Start (macOS / Linux)

```bash
# 1. Clone the repo
git clone https://github.com/UnnamedFigr/MindMesh.git
cd MindMesh

# 2. Set up the backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 3. Create backend .env file
cp .env.example .env
# Then edit backend/.env and fill in your API keys (see Environment Variables below)

# 4. Set up the frontend
cd ../frontend
pnpm install

# 5. Create frontend .env.local file
cp .env.local.example .env.local
# Then edit frontend/.env.local and fill in your values (see Environment Variables below)

# 6. Run backend (terminal 1)
cd ../backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 7. Run frontend (terminal 2)
cd ../frontend
pnpm dev
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** | OpenAI API key — used for GPT-4.1 (long videos) and embeddings |
| `GROQ_API_KEY` | **Yes** | Groq API key — used for Llama models (short videos) and Whisper STT |
| `SUPABASE_URL` | **Yes*** | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | **Yes*** | Supabase service role key |
| `SUPABASE_JWT_SECRET` | **Yes*** | Supabase JWT secret |
| `YOUTUBE_API_KEY` | No | YouTube Data API key (optional metadata enrichment) |
| `STRIPE_SECRET_KEY` | No | Stripe key (for payments — not needed in dev) |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook secret |
| `ALLOWED_ORIGINS` | No | CORS origins (default: `http://localhost:3000`) |
| `ENVIRONMENT` | No | `development` or `production` |

> *\* Supabase keys are required in production. For local development, leave them as placeholders and the app runs in **Dev Mode** with in-memory storage (see below).*

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | **Yes*** | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **Yes*** | Supabase anonymous/public key |
| `NEXT_PUBLIC_API_URL` | **Yes** | Backend URL (default: `http://localhost:8000`) |

> *\* For dev mode, any placeholder value works.*

### Getting API Keys

1. **OpenAI** → [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Groq** → [console.groq.com/keys](https://console.groq.com/keys)
3. **Supabase** → [supabase.com/dashboard](https://supabase.com/dashboard) → Project Settings → API
4. **YouTube** (optional) → [console.cloud.google.com](https://console.cloud.google.com/) → YouTube Data API v3

---

## Dev Mode (No Supabase)

If your Supabase service key is a placeholder (`your-service-role-key-here`), the backend automatically enters **Dev Mode**:

- All data is stored **in-memory** (resets on restart)
- No Supabase connection needed
- A dev user with `pro` tier and 999 credits is auto-created
- Access via `http://localhost:3000/dev` (sets the `mindmesh-dev` cookie)

This is the easiest way to develop and test locally.

---

## Running the App

### Option A: `start.bat` (Windows only)

Double-click `start.bat` or run it from a terminal. It starts both backend and frontend in separate windows.

### Option B: Manual (any OS)

**Terminal 1 — Backend:**
```bash
cd backend
# Activate venv (Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate)
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
pnpm dev
```

### Useful URLs

| URL | Description |
|-----|-------------|
| `http://localhost:3000` | Frontend app |
| `http://localhost:3000/dev` | Dev mode (bypasses auth) |
| `http://localhost:8000/docs` | Backend API docs (Swagger) |
| `http://localhost:8000/health` | Health check |

---

## Project Structure

```
MindMesh/
├── start.bat                # Windows launcher (backend + frontend)
├── backend/
│   ├── .env.example         # Template for environment variables
│   ├── pyproject.toml       # Python dependencies & project config
│   ├── app/
│   │   ├── main.py          # FastAPI app factory + middleware
│   │   ├── config.py        # Settings (env vars via Pydantic)
│   │   ├── routers/         # API endpoints (guides, jobs)
│   │   ├── services/        # Business logic
│   │   │   ├── worker.py    # Background job pipeline orchestrator
│   │   │   ├── generator.py # Study guide generation (Groq/OpenAI)
│   │   │   ├── transcript.py# Transcript fetching (YouTube API → Whisper)
│   │   │   ├── triage.py    # Content classification
│   │   │   ├── credits.py   # Credit system
│   │   │   └── dev_store.py # In-memory storage for dev mode
│   │   ├── prompts/
│   │   │   ├── schemas.py   # Pydantic output schemas for LLM
│   │   │   └── templates/   # Jinja2 prompt templates
│   │   ├── models/          # Request/response models
│   │   └── utils/           # YouTube parser, token counter, errors
│   ├── migrations/          # SQL migration files
│   └── tests/               # pytest tests
├── frontend/
│   ├── .env.local.example   # Template for environment variables
│   ├── package.json         # Node dependencies (use pnpm!)
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # UI components
│   │   ├── hooks/           # React hooks (useAuth, useJobStatus, etc.)
│   │   ├── lib/             # API client, Supabase, utilities
│   │   └── types/           # TypeScript type definitions
│   └── public/              # Static assets
└── docs/                    # Additional documentation
```

---

## Key Technologies

| Category | Technology | Why |
|----------|-----------|-----|
| Frontend framework | Next.js 16 + React 19 | App Router, SSR, modern React |
| Styling | Tailwind CSS v4 | Utility-first, fast iteration |
| State management | Zustand | Lightweight, minimal boilerplate |
| Backend framework | FastAPI | Async, auto-docs, type-safe |
| AI (short videos) | Groq Llama 3.3 70B | Fast inference, free tier available |
| AI (long videos) | OpenAI GPT-4.1 | 1M context window, handles long transcripts |
| Transcripts | youtube-transcript-api | Free YouTube captions extraction |
| STT fallback | Groq Whisper v3 Turbo | When YouTube captions unavailable |
| Token counting | tiktoken | Accurate GPT-compatible token counts |
| Prompting | Jinja2 | Templated, maintainable prompts |
| Package manager | pnpm | Fast, disk-efficient (npm broken on this project) |

---

## Troubleshooting

### `npm install` fails with TAR_ENTRY_ERROR
Use **pnpm** instead. This is a known npm bug on Windows with long paths:
```bash
npm install -g pnpm
pnpm install
```

### Backend won't start — port 8000 in use
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### Frontend lock file error
```powershell
# Delete stale lock
Remove-Item -Force frontend\.next\dev\lock
# Then restart
cd frontend && pnpm dev
```

### `ModuleNotFoundError` in backend
Make sure the virtual environment is activated and dependencies are installed:
```bash
cd backend
.\venv\Scripts\activate   # Windows
source venv/bin/activate   # Mac/Linux
pip install -e ".[dev]"
```

### Videos over 30 minutes fail
Long videos (30+ min) are routed to OpenAI GPT-4.1. Make sure your `OPENAI_API_KEY` in `backend/.env` is valid and has credits.

### "Our AI is experiencing issues" error
Check the backend terminal for the actual error. Common causes:
- Invalid or expired API key
- Groq/OpenAI rate limit hit — wait 60 seconds
- Network connectivity issue

---

## License

Private — All rights reserved.

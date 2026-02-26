# MindMesh

Turn any YouTube video into a study guide. Paste a link, pick your learning style, and get a structured guide in ~30 seconds.

## What it does

- Extracts transcripts from YouTube videos
- Uses AI to create study guides with key themes, takeaways, and quizzes
- Adapts to different learning styles (beginner, academic, practitioner)

## Tech stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS
- **Backend**: FastAPI (Python 3.12+)
- **Database**: Supabase (PostgreSQL)
- **AI**: Groq (Llama) for short videos, OpenAI GPT-4 for long ones

---

## Setup

### Prerequisites

- Node.js 22.x
- pnpm (`npm install -g pnpm`)
- Python 3.12+
- ffmpeg (for audio transcription fallback)

### 1. Clone and install

```bash
git clone https://github.com/your-repo/MindMesh.git
cd MindMesh
```

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -e ".[dev]"
```

Create `backend/.env`:

```
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### 3. Frontend setup

```bash
cd ../frontend
pnpm install
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running it

### Quick way (Windows)

Just run `start.bat` from the project root. It opens both servers.

### Manual way

Terminal 1 (backend):
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (frontend):
```bash
cd frontend
pnpm dev
```

Then open http://localhost:3000

---

## Dev mode

If you don't have Supabase set up, just put placeholder values in the `.env` files. The app will run in dev mode with in-memory storage.

Go to http://localhost:3000/dev to bypass auth.

---

## API docs
Backend API docs available at http://localhost:8000/docs when running.
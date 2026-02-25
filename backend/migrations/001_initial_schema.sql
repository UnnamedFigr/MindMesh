-- ============================================================
-- MindMesh Database Schema
-- Run this in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector for embeddings
-- CREATE EXTENSION IF NOT EXISTS pg_cron;  -- Supabase Pro only

-- ============================================================
-- PROFILES (extends Supabase auth.users)
-- ============================================================
CREATE TABLE public.profiles (
  id                  UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email               TEXT NOT NULL,
  display_name        TEXT,
  tier                TEXT NOT NULL DEFAULT 'core'
                        CHECK (tier IN ('core', 'pro')),
  stripe_customer_id  TEXT UNIQUE,
  stripe_subscription_id TEXT,
  credits_used        INT NOT NULL DEFAULT 0,
  credits_reset_at    TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '1 day')::date::timestamptz,
  daily_credit_limit  INT NOT NULL DEFAULT 3,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_select_own" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_update_own" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- ============================================================
-- VIDEOS (shared cache — one row per YouTube video)
-- ============================================================
CREATE TABLE public.videos (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  youtube_id              TEXT NOT NULL UNIQUE,
  title                   TEXT,
  channel_name            TEXT,
  duration_seconds        INT,
  thumbnail_url           TEXT,
  transcript_raw          TEXT,
  transcript_timestamped  JSONB,       -- [{start, duration, text}, ...]
  token_count             INT,
  language_detected       TEXT DEFAULT 'en',
  transcript_source       TEXT CHECK (transcript_source IN
                            ('manual_caption', 'auto_caption', 'whisper')),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS — any authenticated user can read (shared cache)
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "videos_read_authenticated" ON public.videos
  FOR SELECT USING (auth.role() = 'authenticated');

-- Service role can insert/update (backend only)
CREATE POLICY "videos_insert_service" ON public.videos
  FOR INSERT WITH CHECK (true);
CREATE POLICY "videos_update_service" ON public.videos
  FOR UPDATE USING (true);

-- ============================================================
-- STUDY GUIDES (per-user, cached by video + persona + tier)
-- ============================================================
CREATE TABLE public.study_guides (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  video_id          TEXT NOT NULL,      -- youtube_id reference
  persona           TEXT NOT NULL CHECK (persona IN ('beginner', 'academic', 'practitioner')),
  tier              TEXT NOT NULL CHECK (tier IN ('core', 'pro', 'free')),
  guide_json        JSONB NOT NULL,
  guide_markdown    TEXT NOT NULL,
  triage_result     JSONB,
  processing_strategy TEXT,
  token_count       INT,
  is_bookmarked     BOOLEAN DEFAULT FALSE,
  last_viewed_at    TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE public.study_guides ENABLE ROW LEVEL SECURITY;
CREATE POLICY "guides_select_own" ON public.study_guides FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "guides_update_own" ON public.study_guides FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "guides_delete_own" ON public.study_guides FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "guides_insert_service" ON public.study_guides
  FOR INSERT WITH CHECK (true);

-- Index for common queries
CREATE INDEX idx_study_guides_user ON public.study_guides(user_id, created_at DESC);
CREATE INDEX idx_study_guides_video ON public.study_guides(video_id, persona);

-- ============================================================
-- PROCESSING JOBS (async queue)
-- ============================================================
CREATE TABLE public.processing_jobs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  youtube_url     TEXT NOT NULL,
  persona         TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  progress        INT NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  current_step    TEXT,
  error_message   TEXT,
  result_id       UUID,               -- References study_guides(id) on completion
  credits_charged INT NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
);

-- RLS
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "jobs_select_own" ON public.processing_jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "jobs_insert_service" ON public.processing_jobs
  FOR INSERT WITH CHECK (true);
CREATE POLICY "jobs_update_service" ON public.processing_jobs
  FOR UPDATE USING (true);

-- Index for active job lookups
CREATE INDEX idx_jobs_user_status ON public.processing_jobs(user_id, status);

-- ============================================================
-- API USAGE TRACKING (cost monitoring)
-- ============================================================
CREATE TABLE public.api_usage (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES public.profiles(id),
  job_id            UUID REFERENCES public.processing_jobs(id),
  model             TEXT NOT NULL,
  input_tokens      INT NOT NULL,
  output_tokens     INT NOT NULL,
  estimated_cost_usd NUMERIC(10,6) NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE public.api_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "usage_select_own" ON public.api_usage FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "usage_insert_service" ON public.api_usage
  FOR INSERT WITH CHECK (true);

-- ============================================================
-- CONCEPTS (Pro: vector embeddings for Web of Associations)
-- ============================================================
CREATE TABLE public.concepts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  guide_id        UUID NOT NULL REFERENCES public.study_guides(id) ON DELETE CASCADE,
  concept_name    TEXT NOT NULL,
  concept_description TEXT,
  embedding       VECTOR(512),     -- text-embedding-3-small at 512 dims (cost optimized)
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_concepts_embedding ON public.concepts
  USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_concepts_guide ON public.concepts(guide_id);

-- RLS
ALTER TABLE public.concepts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "concepts_select_service" ON public.concepts FOR SELECT USING (true);
CREATE POLICY "concepts_insert_service" ON public.concepts
  FOR INSERT WITH CHECK (true);
CREATE POLICY "concepts_delete_service" ON public.concepts
  FOR DELETE USING (true);

-- ============================================================
-- REFLECTIONS (Pro: user's reflection answers)
-- ============================================================
CREATE TABLE public.reflections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  study_guide_id  UUID NOT NULL REFERENCES public.study_guides(id) ON DELETE CASCADE,
  content         TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE public.reflections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reflections_select_own" ON public.reflections FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "reflections_insert_own" ON public.reflections FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Auto-create profile on user sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER videos_updated_at
  BEFORE UPDATE ON public.videos
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER jobs_updated_at
  BEFORE UPDATE ON public.processing_jobs
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Atomic credit deduction (prevents race conditions)
CREATE OR REPLACE FUNCTION public.deduct_credits(p_user_id UUID, p_cost INT)
RETURNS BOOLEAN AS $$
DECLARE
  v_result BOOLEAN;
BEGIN
  UPDATE public.profiles
  SET credits_used = credits_used + p_cost
  WHERE id = p_user_id
    AND credits_used + p_cost <= daily_credit_limit
  RETURNING TRUE INTO v_result;

  RETURN COALESCE(v_result, FALSE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Vector similarity search for concepts
CREATE OR REPLACE FUNCTION public.match_concepts(
  query_embedding VECTOR(512),
  match_threshold FLOAT,
  match_count INT,
  exclude_guide_id UUID
)
RETURNS TABLE (
  id UUID,
  guide_id UUID,
  concept_name TEXT,
  concept_description TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.guide_id,
    c.concept_name,
    c.concept_description,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM public.concepts c
  WHERE c.guide_id != exclude_guide_id
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Search guides by concept similarity
CREATE OR REPLACE FUNCTION public.match_guides_by_concept(
  query_embedding VECTOR(512),
  p_user_id UUID,
  match_count INT
)
RETURNS TABLE (
  guide_id UUID,
  video_id TEXT,
  persona TEXT,
  max_similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sg.id AS guide_id,
    sg.video_id,
    sg.persona,
    MAX(1 - (c.embedding <=> query_embedding)) AS max_similarity
  FROM public.concepts c
  JOIN public.study_guides sg ON sg.id = c.guide_id
  WHERE sg.user_id = p_user_id
  GROUP BY sg.id, sg.video_id, sg.persona
  ORDER BY max_similarity DESC
  LIMIT match_count;
END;
$$;

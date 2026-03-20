-- ============================================================
-- Add FK from study_guides.video_id → videos.youtube_id
-- This enables PostgREST relationship embedding (joins).
-- ============================================================

ALTER TABLE public.study_guides
  ADD CONSTRAINT fk_study_guides_video
  FOREIGN KEY (video_id)
  REFERENCES public.videos(youtube_id)
  ON DELETE CASCADE;

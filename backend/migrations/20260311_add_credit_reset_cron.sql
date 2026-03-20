-- Reset credits daily at midnight UTC
SELECT cron.schedule(
  'reset-daily-credits',
  '0 0 * * *',
  $$UPDATE public.profiles
    SET credits_used = 0,
        credits_reset_at = NOW() + INTERVAL '1 day'
    WHERE credits_reset_at <= NOW()$$
);

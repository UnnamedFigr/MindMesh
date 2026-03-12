"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { getJobStatus } from "@/lib/api";
import type { Job } from "@/types";

interface UseJobStatusOptions {
  pollInterval?: number; // ms, default 2500
  onComplete?: (resultId: string) => void;
  onError?: (error: string) => void;
}

export function useJobStatus(
  jobId: string | null,
  options: UseJobStatusOptions = {}
) {
  const { pollInterval = 2500, onComplete, onError } = options;
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Keep refs current
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    if (!jobId) return;

    try {
      const status = await getJobStatus(jobId);
      setJob(status);
      setError(null);

      if (status.status === "completed") {
        stopPolling();
        if (status.result_id) {
          onCompleteRef.current?.(status.result_id);
        }
      } else if (status.status === "failed") {
        stopPolling();
        onErrorRef.current?.(status.error_message || "Job failed");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch status";
      setError(message);
    }
  }, [jobId, stopPolling]);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setError(null);
      return;
    }

    setLoading(true);
    
    // Initial fetch
    poll().then(() => setLoading(false));

    // Start polling
    intervalRef.current = setInterval(poll, pollInterval);

    return () => stopPolling();
  }, [jobId, pollInterval, poll, stopPolling]);

  return { job, loading, error, stopPolling };
}

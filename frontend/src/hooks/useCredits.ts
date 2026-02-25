"use client";

import { useEffect, useState, useCallback } from "react";
import { getCredits } from "@/lib/api";
import type { CreditStatus } from "@/types";

export function useCredits() {
  const [credits, setCredits] = useState<CreditStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCredits();
      setCredits(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch credits");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { credits, loading, error, refresh };
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { isDemoMode, isDevMode, disableDemoMode, DEMO_USER, DEV_USER } from "@/lib/demo";
import { getBillingStatus } from "@/lib/api";
import type { User, Session } from "@supabase/supabase-js";

export function useAuth() {
  const bootMode = useMemo(() => {
    const dev = typeof window !== "undefined" && isDevMode();
    const demo = typeof window !== "undefined" && !dev && isDemoMode();
    const bootUser = dev
      ? (DEV_USER as unknown as User)
      : demo
        ? (DEMO_USER as unknown as User)
        : null;

    return { dev, demo, bootUser };
  }, []);

  const [user, setUser] = useState<User | null>(bootMode.bootUser);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(!bootMode.dev && !bootMode.demo);
  const demo = bootMode.demo;
  const dev = bootMode.dev;
  const router = useRouter();

  // Stable client reference — createClient() is cheap but re-creating it on
  // every render would register duplicate onAuthStateChange listeners.
  const supabase = useMemo(() => createClient(), []);

  useEffect(() => {
    // Skip Supabase auth in dev/demo mode
    if (bootMode.dev || bootMode.demo) return;

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);

      // Reconcile Stripe billing tier on sign-in (fire-and-forget)
      if (_event === "SIGNED_IN") {
        getBillingStatus().catch(() => {
          /* best-effort: ignore failures in dev/offline */
        });
      }
    });

    return () => subscription.unsubscribe();
  }, [bootMode.demo, bootMode.dev, supabase]);

  const signOut = useCallback(async () => {
    if (demo || dev) {
      disableDemoMode();
      router.push("/");
      return;
    }
    await supabase.auth.signOut();
  }, [demo, dev, router, supabase]);

  return { user, session, loading, signOut, isDemo: demo, isDev: dev };
}

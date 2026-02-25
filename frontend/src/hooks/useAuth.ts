"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { isDemoMode, isDevMode, disableDemoMode, DEMO_USER, DEV_USER } from "@/lib/demo";
import type { User, Session } from "@supabase/supabase-js";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [dev, setDev] = useState(false);
  const router = useRouter();

  const supabase = createClient();

  useEffect(() => {
    // Check dev mode first (uses real backend)
    if (isDevMode()) {
      setUser(DEV_USER as unknown as User);
      setDev(true);
      setLoading(false);
      return;
    }

    // Check demo mode (mock data)
    if (isDemoMode()) {
      setUser(DEMO_USER as unknown as User);
      setDemo(true);
      setLoading(false);
      return;
    }

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
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = useCallback(async () => {
    if (demo || dev) {
      disableDemoMode();
      router.push("/");
      return;
    }
    await supabase.auth.signOut();
  }, [demo, dev, router]);

  return { user, session, loading, signOut, isDemo: demo, isDev: dev };
}

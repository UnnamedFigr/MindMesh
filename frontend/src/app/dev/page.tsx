"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { enableDevMode } from "@/lib/demo";

/**
 * /dev — sets the dev mode cookie and redirects to dashboard.
 * Dev mode uses the real backend (OpenAI, Groq, YouTube) with in-memory storage.
 */
export default function DevEntryPage() {
  const router = useRouter();

  useEffect(() => {
    enableDevMode();
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-600 font-medium">Entering dev mode...</p>
        <p className="text-gray-400 text-sm mt-1">Real AI backend · In-memory storage</p>
      </div>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { enableDemoMode } from "@/lib/demo";

/**
 * /demo — sets the demo cookie and redirects to dashboard.
 */
export default function DemoEntryPage() {
  const router = useRouter();

  useEffect(() => {
    enableDemoMode();
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-500">Entering demo mode...</p>
      </div>
    </div>
  );
}

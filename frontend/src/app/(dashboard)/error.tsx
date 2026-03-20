"use client";

import { useEffect } from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-16">
      <div className="mx-auto max-w-md text-center">
        <div className="mb-4 text-4xl">😵</div>
        <h2 className="mb-2 text-xl font-bold text-gray-900">
          Failed to load this page
        </h2>
        <p className="mb-6 text-sm text-gray-600">
          {error.message || "Something went wrong. Please try again."}
        </p>
        <div className="flex justify-center gap-3">
          <button
            onClick={reset}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Retry
          </button>
          <a
            href="/dashboard"
            className="rounded-lg border border-gray-300 px-5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

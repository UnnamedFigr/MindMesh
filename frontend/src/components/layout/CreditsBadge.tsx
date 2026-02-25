"use client";

import { useCredits } from "@/hooks/useCredits";
import { formatTimeUntilReset } from "@/lib/utils";
import { Target } from "lucide-react";

export default function CreditsBadge() {
  const { credits, loading } = useCredits();

  if (loading || !credits) {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 text-gray-400 text-sm">
        <Target className="w-4 h-4" />
        <span>...</span>
      </div>
    );
  }

  const isLow = credits.credits_remaining <= 1;
  const isExhausted = credits.credits_remaining <= 0;

  return (
    <div
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${
        isExhausted
          ? "bg-red-100 text-red-700"
          : isLow
          ? "bg-yellow-100 text-yellow-700"
          : "bg-indigo-100 text-indigo-700"
      }`}
      title={
        credits.reset_at
          ? `Resets in ${formatTimeUntilReset(credits.reset_at)}`
          : undefined
      }
    >
      <Target className="w-4 h-4" />
      <span>
        {credits.credits_remaining}/{credits.daily_credit_limit}
      </span>
    </div>
  );
}

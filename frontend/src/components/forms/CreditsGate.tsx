"use client";

import { useCredits } from "@/hooks/useCredits";
import { formatTimeUntilReset } from "@/lib/utils";
import Button from "@/components/ui/Button";
import { AlertCircle, Clock, Crown } from "lucide-react";
import Link from "next/link";

interface CreditsGateProps {
  children: React.ReactNode;
}

export default function CreditsGate({ children }: CreditsGateProps) {
  const { credits, loading } = useCredits();

  if (loading || !credits) return <>{children}</>;

  const isExhausted = credits.credits_remaining <= 0;

  if (!isExhausted) return <>{children}</>;

  return (
    <div className="relative">
      {/* Blurred content */}
      <div className="pointer-events-none select-none opacity-30 blur-[2px]">
        {children}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-w-md mx-4 text-center animate-scale-in">
          <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            You&apos;re out of credits
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            You&apos;ve used all {credits.daily_credit_limit} of your daily credits.
            {credits.reset_at && (
              <span className="flex items-center justify-center gap-1 mt-2 text-gray-400">
                <Clock className="w-3.5 h-3.5" />
                Resets in {formatTimeUntilReset(credits.reset_at)}
              </span>
            )}
          </p>
          <div className="space-y-2">
            {credits.tier !== "pro" && (
              <Link href="/pricing" className="block">
                <Button className="w-full" size="lg">
                  <Crown className="w-4 h-4 mr-2" />
                  Upgrade to Pro
                </Button>
              </Link>
            )}
            <Link href="/library" className="block">
              <Button variant="secondary" className="w-full">
                Browse Library
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

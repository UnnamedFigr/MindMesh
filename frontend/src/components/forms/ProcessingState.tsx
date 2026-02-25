"use client";

import { cn } from "@/lib/utils";
import { STEP_LABELS } from "@/types";
import type { Job } from "@/types";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

interface ProcessingStateProps {
  job: Job | null;
  error?: string | null;
}

const STEP_ORDER = [
  "queued",
  "validating_video",
  "fetching_transcript",
  "checking_credits",
  "analyzing_content",
  "generating_guide",
  "saving_results",
  "done",
];

export default function ProcessingState({ job, error }: ProcessingStateProps) {
  if (!job && !error) return null;

  const isComplete = job?.status === "completed";
  const isFailed = job?.status === "failed" || !!error;
  const progress = job?.progress ?? 0;
  const stepLabel =
    job?.current_step && STEP_LABELS[job.current_step]
      ? STEP_LABELS[job.current_step]
      : "Processing...";

  const currentStepIndex = job?.current_step
    ? STEP_ORDER.indexOf(job.current_step)
    : 0;
  const totalSteps = STEP_ORDER.length - 1; // exclude "queued"

  return (
    <div className="w-full space-y-4">
      {/* Progress Bar */}
      <div className="relative w-full h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn(
            "absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out",
            isFailed
              ? "bg-red-500"
              : isComplete
              ? "bg-green-500"
              : "bg-indigo-500"
          )}
          style={{ width: `${progress}%` }}
        />
        {!isComplete && !isFailed && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        )}
      </div>

      {/* Status Label */}
      <div className="flex items-center gap-2 text-sm">
        {isFailed ? (
          <>
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-red-600 font-medium">
              {job?.error_message || error || "Something went wrong"}
            </span>
          </>
        ) : isComplete ? (
          <>
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            <span className="text-green-600 font-medium">
              Study guide ready!
            </span>
          </>
        ) : (
          <>
            <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
            <span className="text-gray-600">{stepLabel}</span>
            <span className="text-gray-400 ml-auto text-xs">
              Step {Math.max(1, currentStepIndex)}/{totalSteps} &middot; {progress}%
            </span>
          </>
        )}
      </div>
    </div>
  );
}

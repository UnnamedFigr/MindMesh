"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createGuide } from "@/lib/api";
import { useJobStatus } from "@/hooks/useJobStatus";
import { isValidYouTubeUrl, extractVideoId, getYouTubeThumbnail } from "@/lib/utils";
import ProcessingState from "@/components/forms/ProcessingState";
import CreditsGate from "@/components/forms/CreditsGate";
import Button from "@/components/ui/Button";
import { Sparkles, ArrowRight, Link2, X } from "lucide-react";
import { PERSONA_OPTIONS } from "@/types";
import type { Persona, Job } from "@/types";

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [persona, setPersona] = useState<Persona>("beginner");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);

  const router = useRouter();
  const isValid = url.length > 0 && isValidYouTubeUrl(url);
  const videoId = extractVideoId(url);

  const { job } = useJobStatus(currentJob?.job_id ?? null, {
    onComplete: (resultId: string) => {
      router.push(`/guide/${resultId}`);
    },
    onError: (errorMsg: string) => {
      setError(errorMsg || "Something went wrong. Please try again.");
      setCurrentJob(null);
    },
  });

  const handleSubmit = async () => {
    if (!isValid) return;

    setSubmitting(true);
    setError(null);

    try {
      const response = await createGuide(url, persona);
      setCurrentJob({
        job_id: response.job_id,
        status: "pending",
        progress: 0,
        current_step: "queued",
        error_message: null,
        result_id: null,
        created_at: new Date().toISOString(),
        completed_at: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to start processing.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasted = e.clipboardData.getData("text");
    if (pasted && isValidYouTubeUrl(pasted)) {
      e.preventDefault();
      setUrl(pasted.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && isValid && !submitting) {
      handleSubmit();
    }
  };

  // Show processing state
  if (currentJob) {
    return (
      <div className="max-w-lg mx-auto mt-16">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-1 text-center">
            Building your study guide
          </h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            This usually takes 15–30 seconds.
          </p>
          <ProcessingState job={job || currentJob} error={error} />
          {error && (
            <div className="mt-6 text-center">
              <Button
                variant="secondary"
                onClick={() => {
                  setCurrentJob(null);
                  setError(null);
                }}
              >
                Try Again
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto mt-4">
      {/* Simple header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 rounded-full px-3 py-1 text-xs font-medium mb-3">
          <Sparkles className="w-3 h-3" />
          Paste a link, get a guide
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          What do you want to learn?
        </h1>
      </div>

      <CreditsGate>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-5 animate-scale-in">
          {/* URL Input — big and prominent */}
          <div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Link2 className="w-4 h-4 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Paste a YouTube URL here..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onPaste={handlePaste}
                onKeyDown={handleKeyDown}
                autoComplete="off"
                className="w-full pl-10 pr-10 py-3.5 rounded-xl border border-gray-200 bg-gray-50 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all"
              />
              {url && (
                <button
                  onClick={() => setUrl("")}
                  title="Clear URL"
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            {url && !isValid && (
              <p className="text-xs text-red-500 mt-1.5 ml-1">
                Please enter a valid YouTube URL
              </p>
            )}
          </div>

          {/* Video thumbnail preview */}
          {videoId && (
            <div className="flex items-center gap-3 bg-gray-50 rounded-xl p-3 border border-gray-100 animate-in fade-in duration-200">
              <img
                src={getYouTubeThumbnail(videoId)}
                alt="Video thumbnail"
                className="w-24 h-16 object-cover rounded-lg flex-shrink-0"
              />
              <div className="min-w-0">
                <p className="text-xs text-gray-500">Video detected</p>
                <p className="text-sm text-gray-700 font-medium truncate">
                  {videoId}
                </p>
              </div>
            </div>
          )}

          {/* Persona selector — compact inline */}
          <div>
            <p className="text-xs text-gray-500 font-medium mb-2">
              Learning style
            </p>
            <div className="grid grid-cols-2 gap-3">
              {PERSONA_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setPersona(opt.id)}
                  className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all text-center ${persona === opt.id
                      ? "border-indigo-500 bg-indigo-50"
                      : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                >
                  <span className="text-xl mb-1">{opt.emoji}</span>
                  <span className="text-xs font-semibold text-gray-900">
                    {opt.name}
                  </span>
                  <span className="text-[10px] text-gray-500 mt-0.5 leading-tight">
                    {opt.description}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <Button
            onClick={handleSubmit}
            disabled={!isValid || submitting}
            loading={submitting}
            className="w-full"
            size="lg"
          >
            Generate Study Guide
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>

          <p className="text-[11px] text-gray-400 text-center">
            Uses 1 credit per guide. Free tier: 3 credits/day.
          </p>
        </div>
      </CreditsGate>
    </div>
  );
}

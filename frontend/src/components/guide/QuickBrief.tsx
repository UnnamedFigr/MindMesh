"use client";

import type { QuickBrief as QuickBriefType } from "@/types";
import { Zap, CheckCircle2, Quote, Clock, BarChart3 } from "lucide-react";

interface QuickBriefProps {
  brief: QuickBriefType;
}

export default function QuickBrief({ brief }: QuickBriefProps) {
  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6 mb-6">
      {/* Hook */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Zap className="w-4 h-4 text-indigo-600" />
        </div>
        <div>
          <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">
            TL;DR
          </p>
          <p className="text-gray-900 font-medium leading-relaxed">
            {brief.hook}
          </p>
        </div>
      </div>

      {/* Key Takeaways */}
      <div className="space-y-2 mb-4">
        {brief.key_takeaways?.map((takeaway, i) => (
          <div key={i} className="flex items-start gap-2.5 ml-11">
            <CheckCircle2 className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-gray-700 leading-relaxed">{takeaway}</p>
          </div>
        ))}
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-4 ml-11 pt-3 border-t border-indigo-100">
        {/* Clickbait score */}
        {brief.clickbait_score && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>
              Title accuracy:{" "}
              <span className="font-semibold text-gray-700">
                {brief.clickbait_score.score}/10
              </span>
            </span>
          </div>
        )}

        {/* Time saved */}
        {brief.time_saved_minutes > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Clock className="w-3.5 h-3.5" />
            <span>
              ~{brief.time_saved_minutes} min saved
            </span>
          </div>
        )}
      </div>

      {/* Highlight quote */}
      {brief.highlight_quote && (
        <div className="ml-11 mt-3 pt-3 border-t border-indigo-100">
          <div className="flex items-start gap-2">
            <Quote className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm italic text-gray-600 leading-relaxed">
                &ldquo;{brief.highlight_quote}&rdquo;
              </p>
              {brief.highlight_quote_timestamp && (
                <p className="text-xs text-gray-400 mt-1 font-mono">
                  {brief.highlight_quote_timestamp}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

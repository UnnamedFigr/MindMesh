"use client";

import { useState } from "react";
import type { ThemeBlock as ThemeBlockType } from "@/types";
import { ChevronDown, Clock, Lightbulb, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThemeBlockProps {
  theme: ThemeBlockType;
  index: number;
  defaultOpen?: boolean;
  onTimestampClick?: (timeStr: string) => void;
}

export default function ThemeBlock({
  theme,
  index,
  defaultOpen = false,
  onTimestampClick,
}: ThemeBlockProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [subtopicsOpen, setSubtopicsOpen] = useState(false);
  const [deepDiveOpen, setDeepDiveOpen] = useState(false);

  const colors = [
    { bg: "bg-blue-50", border: "border-blue-200", accent: "text-blue-600", dot: "bg-blue-500" },
    { bg: "bg-emerald-50", border: "border-emerald-200", accent: "text-emerald-600", dot: "bg-emerald-500" },
    { bg: "bg-violet-50", border: "border-violet-200", accent: "text-violet-600", dot: "bg-violet-500" },
    { bg: "bg-amber-50", border: "border-amber-200", accent: "text-amber-600", dot: "bg-amber-500" },
    { bg: "bg-rose-50", border: "border-rose-200", accent: "text-rose-600", dot: "bg-rose-500" },
    { bg: "bg-cyan-50", border: "border-cyan-200", accent: "text-cyan-600", dot: "bg-cyan-500" },
  ];

  const color = colors[index % colors.length];

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-300 overflow-hidden",
        isOpen ? `${color.border} ${color.bg}` : "border-gray-200 bg-white hover:border-gray-300"
      )}
    >
      {/* Header — always visible, clickable */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left cursor-pointer"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
      >
        <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-white text-xs font-bold", color.dot)}>
          {theme.theme_number ?? index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm truncate">
            {theme.title}
          </h3>
          {!isOpen && (
            <p className="text-xs text-gray-500 truncate mt-0.5">
              {theme.core_concept}
            </p>
          )}
        </div>
        {theme.time_range && (
          <button
            onClick={(e) => {
              e.stopPropagation(); // Prevent toggling the accordion
              if (onTimestampClick) {
                // time_range is like "05:22 - 08:15". Pass the start time.
                const startMatch = theme.time_range.match(/^(\d{1,2}:\d{2}(?::\d{2})?)/);
                if (startMatch) {
                  onTimestampClick(startMatch[1]);
                }
              }
            }}
            className={cn(
              "text-xs font-mono flex items-center gap-1 flex-shrink-0 mr-2 transition-colors",
              onTimestampClick ? "text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 px-1.5 py-0.5 rounded" : "text-gray-400"
            )}
          >
            <Clock className="w-3 h-3" />
            {theme.time_range}
          </button>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-gray-400 transition-transform duration-300 flex-shrink-0",
            isOpen && "rotate-180"
          )}
        />
      </div>

      {/* Content — collapsible */}
      <div
        className={cn(
          "grid transition-all duration-300",
          isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">
          <div className="px-5 pb-5 space-y-4">
            {/* Core Concept */}
            <p className="text-sm text-gray-700 leading-relaxed">
              {theme.core_concept}
            </p>

            {/* Mechanics */}
            {theme.mechanics && theme.mechanics.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5" />
                  How It Works
                </p>
                <ul className="space-y-1.5">
                  {theme.mechanics.map((point, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className={cn("w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0", color.dot)} />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Analogy / Example */}
            {theme.analogy_or_example && (
              <div className={cn("text-sm italic text-gray-600 border-l-3 pl-3 py-1", color.border)}>
                💡 {theme.analogy_or_example}
              </div>
            )}

            {/* Subtopics — Expandable */}
            {theme.subtopics && theme.subtopics.length > 0 && (
              <div className="border-t pt-3 mt-3">
                <button
                  onClick={() => setSubtopicsOpen(!subtopicsOpen)}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  <ChevronRight
                    className={cn(
                      "w-3.5 h-3.5 transition-transform duration-200",
                      subtopicsOpen && "rotate-90"
                    )}
                  />
                  Subtopics ({theme.subtopics.length})
                </button>
                <div
                  className={cn(
                    "grid transition-all duration-200 mt-2",
                    subtopicsOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  )}
                >
                  <div className="overflow-hidden">
                    <ul className="space-y-1.5">
                      {theme.subtopics.map((subtopic, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className={cn("w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0", color.dot)} />
                          {subtopic}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Deep Dive — Expandable */}
            {theme.deep_dive && (
              <div className="border-t pt-3 mt-3">
                <button
                  onClick={() => setDeepDiveOpen(!deepDiveOpen)}
                  className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider hover:text-indigo-700 transition-colors"
                >
                  <ChevronRight
                    className={cn(
                      "w-3.5 h-3.5 transition-transform duration-200",
                      deepDiveOpen && "rotate-90"
                    )}
                  />
                  Deep Dive
                </button>
                <div
                  className={cn(
                    "grid transition-all duration-200 mt-2",
                    deepDiveOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  )}
                >
                  <div className="overflow-hidden">
                    <div className="space-y-3">
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {theme.deep_dive.explanation}
                      </p>
                      {theme.deep_dive.technical_detail && (
                        <div className="bg-gray-50 rounded-lg p-3 text-sm">
                          <span className="font-semibold text-gray-700">Technical Detail: </span>
                          <span className="text-gray-600">{theme.deep_dive.technical_detail}</span>
                        </div>
                      )}
                      {theme.deep_dive.related_concept && (
                        <div className="bg-indigo-50 rounded-lg p-3 text-sm">
                          <span className="font-semibold text-indigo-700">Related Concept: </span>
                          <span className="text-indigo-600">{theme.deep_dive.related_concept}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

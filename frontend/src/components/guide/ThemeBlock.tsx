"use client";

import { useState } from "react";
import type { ThemeBlock as ThemeBlockType } from "@/types";
import { ChevronDown, Clock, Lightbulb, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThemeBlockProps {
  theme: ThemeBlockType;
  index: number;
  defaultOpen?: boolean;
}

export default function ThemeBlock({
  theme,
  index,
  defaultOpen = false,
}: ThemeBlockProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [subtopicsOpen, setSubtopicsOpen] = useState(false);

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
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
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
          <span className="text-xs text-gray-400 font-mono flex items-center gap-1 flex-shrink-0 mr-2">
            <Clock className="w-3 h-3" />
            {theme.time_range}
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-gray-400 transition-transform duration-300 flex-shrink-0",
            isOpen && "rotate-180"
          )}
        />
      </button>

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
          </div>
        </div>
      </div>
    </div>
  );
}

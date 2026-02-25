"use client";

import { cn } from "@/lib/utils";
import { PERSONA_OPTIONS, type Persona } from "@/types";

interface PersonaSelectorProps {
  selected: Persona;
  onChange: (persona: Persona) => void;
  disabled?: boolean;
}

export default function PersonaSelector({
  selected,
  onChange,
  disabled,
}: PersonaSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {PERSONA_OPTIONS.map((option) => (
        <button
          key={option.id}
          onClick={() => !disabled && onChange(option.id)}
          disabled={disabled}
          className={cn(
            "relative flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2",
            selected === option.id
              ? "border-indigo-500 bg-indigo-50 shadow-sm"
              : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <span className="text-2xl mb-2">{option.emoji}</span>
          <span className="font-semibold text-gray-900 text-sm">
            {option.name}
          </span>
          <span className="text-xs text-gray-500 text-center mt-1">
            {option.description}
          </span>
          {selected === option.id && (
            <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-500" />
          )}
        </button>
      ))}
    </div>
  );
}

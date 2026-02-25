"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import { CheckCircle, XCircle, HelpCircle } from "lucide-react";
import type { QuizQuestion } from "@/types";

interface QuizCardProps {
  question: QuizQuestion;
  index: number;
}

export default function QuizCard({ question, index }: QuizCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);

  const correctAnswer = question.options[question.correct_index];
  const isCorrect = selectedAnswer === correctAnswer;

  const handleSelect = (option: string) => {
    if (revealed) return;
    setSelectedAnswer(option);
  };

  const handleReveal = () => {
    if (!selectedAnswer) return;
    setRevealed(true);
  };

  const handleReset = () => {
    setSelectedAnswer(null);
    setRevealed(false);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-start gap-3 mb-4">
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-semibold">
          {index + 1}
        </span>
        <p className="text-gray-900 font-medium leading-relaxed">
          {question.question}
        </p>
      </div>

      <div className="space-y-2 ml-10">
        {question.options.map((option, i) => {
          const letter = String.fromCharCode(65 + i); // A, B, C, D
          const isSelected = selectedAnswer === option;
          const isAnswer = option === correctAnswer;

          let optionStyle =
            "border-gray-200 hover:border-indigo-300 hover:bg-indigo-50";
          if (isSelected && !revealed) {
            optionStyle = "border-indigo-500 bg-indigo-50";
          }
          if (revealed && isAnswer) {
            optionStyle = "border-green-500 bg-green-50";
          }
          if (revealed && isSelected && !isCorrect) {
            optionStyle = "border-red-500 bg-red-50";
          }

          return (
            <button
              key={i}
              onClick={() => handleSelect(option)}
              disabled={revealed}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors flex items-center gap-3 ${optionStyle} disabled:cursor-default`}
            >
              <span className="flex-shrink-0 w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-medium">
                {letter}
              </span>
              <span className="text-sm text-gray-700">{option}</span>
              {revealed && isAnswer && (
                <CheckCircle className="w-4 h-4 text-green-600 ml-auto flex-shrink-0" />
              )}
              {revealed && isSelected && !isCorrect && (
                <XCircle className="w-4 h-4 text-red-600 ml-auto flex-shrink-0" />
              )}
            </button>
          );
        })}
      </div>

      <div className="ml-10 mt-4 flex items-center gap-3">
        {!revealed ? (
          <Button
            size="sm"
            onClick={handleReveal}
            disabled={!selectedAnswer}
          >
            Check Answer
          </Button>
        ) : (
          <Button size="sm" variant="secondary" onClick={handleReset}>
            Try Again
          </Button>
        )}
        {revealed && (
          <div className="flex items-center gap-2 text-sm">
            {isCorrect ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-green-700 font-medium">Correct!</span>
              </>
            ) : (
              <>
                <HelpCircle className="w-4 h-4 text-amber-600" />
                <span className="text-amber-700">
                  {question.explanation}
                </span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

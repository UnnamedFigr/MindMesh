"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import type { MemoryQuestions } from "@/types";

interface RefreshableQuestionsProps {
    questions: MemoryQuestions[];
}

export default function RefreshableQuestions({ questions }: RefreshableQuestionsProps) {
    const [startIndex, setStartIndex] = useState(0);
    const [revealed, setRevealed] = useState<Set<number>>(new Set());

    const BATCH_SIZE = 3;
    const currentBatch = questions.slice(startIndex, startIndex + BATCH_SIZE);

    const handleRefresh = () => {
        const nextIndex = startIndex + BATCH_SIZE;
        setStartIndex(nextIndex >= questions.length ? 0 : nextIndex);
        setRevealed(new Set());
    };

    const toggleReveal = (index: number) => {
        setRevealed((prev) => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };

    const totalBatches = Math.ceil(questions.length / BATCH_SIZE);
    const currentBatchNum = Math.floor(startIndex / BATCH_SIZE) + 1;

    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-6">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-teal-50 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        🧠 Memory Check
                    </h2>
                    <p className="text-sm text-gray-500 mt-0.5">
                        Test your understanding — {currentBatchNum} of {totalBatches}
                    </p>
                </div>
                <button
                    onClick={handleRefresh}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition-colors duration-200"
                >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Refresh
                </button>
            </div>

            {/* Questions */}
            <div className="p-6 space-y-3">
                {currentBatch.map((q, i) => {
                    const globalIndex = startIndex + i;
                    const isRevealed = revealed.has(globalIndex);

                    return (
                        <div
                            key={`${startIndex}-${i}`}
                            className="rounded-xl border border-gray-100 bg-gray-50 overflow-hidden"
                        >
                            <button
                                onClick={() => toggleReveal(globalIndex)}
                                className="w-full px-4 py-3 text-left text-sm font-medium text-gray-800 hover:bg-gray-100 transition-colors flex items-center justify-between"
                            >
                                <span>Q{globalIndex + 1}: {q.question}</span>
                                <span
                                    className={`text-xs text-gray-400 transition-transform duration-200 ${isRevealed ? "rotate-180" : ""}`}
                                >
                                    ▼
                                </span>
                            </button>
                            {isRevealed && (
                                <div className="px-4 py-3 text-sm text-gray-600 bg-white border-t border-gray-100">
                                    {q.answer}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

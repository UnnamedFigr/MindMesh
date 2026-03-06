"use client";

import { useState, useEffect, useRef } from "react";
import Button from "@/components/ui/Button";
import { PenLine, Save, CheckCircle2, Lightbulb, X } from "lucide-react";

interface ReflectionSectionProps {
  guideId: string;
  prompts?: string[];
}

interface Note {
  id: string;
  text: string;
  timestamp: number;
}

export default function ReflectionSection({
  guideId,
  prompts,
}: ReflectionSectionProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [text, setText] = useState("");
  const [saved, setSaved] = useState(false);
  const [activePrompt, setActivePrompt] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load saved reflection from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(`reflection-${guideId}`);
    if (stored) {
      try {
        const parsedNotes = JSON.parse(stored);
        if (Array.isArray(parsedNotes)) {
          setNotes(parsedNotes);
        } else {
          setNotes([{ id: 'legacy-note', text: parsedNotes, timestamp: Date.now() }])
        }
      } catch (error) {
        setNotes([{ id: "legacy-note", text: stored, timestamp: Date.now() }]);
      }
    }
  }, [guideId]);

  const handleSave = () => {
    if (!text.trim()) return;
    const newNote: Note = {
      id: Date.now().toString(),
      text: text.trim(),
      timestamp: Date.now(),
    };

    const updatedNotes = [newNote, ...notes];
    setNotes(updatedNotes);
    localStorage.setItem(`reflection-${guideId}`, JSON.stringify(updatedNotes));
    setText("");
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };
  const handleDeleteNote = (idToRemove: string) => {
    const updatedNotes = notes.filter((note) => note.id !== idToRemove);
    setNotes(updatedNotes);
    localStorage.setItem(`reflection-${guideId}`, JSON.stringify(updatedNotes));
  }
  const handlePromptClick = (prompt: string, index: number) => {
    setActivePrompt(index);
    const prefix = text ? `${text}\n\n` : "";
    setText(`${prefix}**${prompt}**\n`);
    setTimeout(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(
        textareaRef.current.value.length,
        textareaRef.current.value.length
      );
    }, 50);
  };

  const defaultPrompts = [
    "What was the most surprising thing I learned?",
    "How does this connect to something I already know?",
    "What would I explain differently to a friend?",
  ];

  const reflectionPrompts = prompts?.length ? prompts : defaultPrompts;

  return (

    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-amber-50 to-orange-50">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <PenLine className="w-5 h-5 text-amber-600" />
          Reflect & Internalize
        </h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Writing helps you process and retain what you learned
        </p>
      </div>

      <div className="p-6 space-y-4">
        {/* Prompt Chips */}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
            Reflection Prompts
          </p>
          <div className="flex flex-wrap gap-2">
            {reflectionPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handlePromptClick(prompt, i)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-all duration-200 ${activePrompt === i
                  ? "bg-amber-100 border-amber-300 text-amber-800"
                  : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700"
                  }`}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setSaved(false);
          }}
          placeholder="Write your thoughts, connections, and takeaways here..."
          className="w-full min-h-[160px] rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent focus:bg-white transition-all duration-200 resize-y"
        />
        {/* Render Saved Notes */}
        {notes.length > 0 && (
          <div className="mt-8 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 border-t border-gray-100 pt-6">Past Reflections</h3>
            <div className="space-y-3">
              {notes.map((note) => (
                <div key={note.id} className="p-4 relative group bg-amber-50 rounded-xl border border-amber-100 text-sm text-gray-800 whitespace-pre-wrap">
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    className="absolute top-3 right-3 p-1 text-amber-600/40 hover:text-red-500 hover:bg-white rounded-md opacity-0 group-hover:opacity-100 transition-all duration-200"
                    aria-label="Delete note"
                  >
                    <X className="w-5 h-5" />
                  </button>

                  <div className="pr-6">
                    {note.text}
                  </div>
                  <p className="text-xs text-amber-600/60 mt-2 font-medium">
                    {new Date(note.timestamp).toLocaleDateString()} at {new Date(note.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Save Button */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-400">
            {text.length > 0 ? `${text.split(/\s+/).filter(Boolean).length} words` : "Start writing..."}
          </p>
          <div className="flex items-center gap-2">
            {saved && (
              <span className="text-xs text-green-600 flex items-center gap-1 animate-fade-in">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Saved
              </span>
            )}
            <Button
              size="sm"
              variant="secondary"
              onClick={handleSave}
              disabled={!text.trim()}
            >
              <Save className="w-3.5 h-3.5 mr-1.5" />
              Save Reflection
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

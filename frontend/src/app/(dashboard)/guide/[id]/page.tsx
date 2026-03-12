"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getGuide, deleteGuide } from "@/lib/api";
import ReflectionSection from "@/components/guide/ReflectionSection";
import RefreshableQuestions from "@/components/guide/RefreshableQuestions";
import ThemeBlock from "@/components/guide/ThemeBlock";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Skeleton from "@/components/ui/Skeleton";
import {
  ArrowLeft,
  Clock,
  User,
  Trash2,
  ExternalLink,
  BookOpen,
  Share2,
  Copy,
  Check,
} from "lucide-react";
import { formatDate, getYouTubeThumbnail } from "@/lib/utils";
import type { StudyGuide } from "@/types";

export default function GuideViewerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [guide, setGuide] = useState<StudyGuide | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState<"link" | "md" | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchGuide = async () => {
      try {
        const data = await getGuide(id);
        setGuide(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load guide.");
      } finally {
        setLoading(false);
      }
    };
    fetchGuide();
  }, [id]);

  const handleDelete = async () => {
    if (!guide || !confirm("Delete this study guide? This cannot be undone."))
      return;
    setDeleting(true);
    try {
      await deleteGuide(guide.id);
      router.push("/library");
    } catch {
      setDeleting(false);
    }
  };

  const copyToClipboard = async (text: string, type: "link" | "md") => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // Fallback
    }
  };

  const handleTimestampClick = (timeStr: string) => {
    if (!guide?.youtube_id) return;
    
    // Convert "MM:SS" or "HH:MM:SS" to seconds for YouTube URL parameter
    const parts = timeStr.split(':').map(Number);
    let seconds = 0;
    if (parts.length === 2) {
      seconds = parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    }

    const url = `https://youtube.com/watch?v=${guide.youtube_id}&t=${seconds}s`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !guide) {
    return (
      <div className="max-w-3xl mx-auto text-center py-16">
        <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Guide not found
        </h2>
        <p className="text-gray-500 mb-6">{error || "This guide may have been deleted."}</p>
        <Button variant="secondary" onClick={() => router.push("/library")}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Library
        </Button>
      </div>
    );
  }

  const thumbnail =
    guide.video_id ? getYouTubeThumbnail(guide.video_id) : null;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => router.push("/library")}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Library
      </button>

      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden mb-6">
        <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {thumbnail && (
              <img
                src={thumbnail}
                alt={guide.title}
                className="w-full sm:w-48 h-28 object-cover rounded-lg flex-shrink-0 shadow-sm"
              />
            )}
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                {guide.title}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                <Badge variant={guide.persona === "beginner" ? "info" : guide.persona === "academic" ? "success" : "warning"}>
                  <User className="w-3 h-3 mr-1" />
                  {guide.persona}
                </Badge>
                {guide.channel_name && (
                  <span className="text-xs text-gray-500 font-medium">
                    {guide.channel_name}
                  </span>
                )}
                <span className="flex items-center gap-1 text-xs text-gray-400">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDate(guide.created_at)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 px-6 py-3 border-t border-gray-100 bg-white">
          <a
            href={`https://youtube.com/watch?v=${guide.youtube_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-indigo-600 hover:text-indigo-500 flex items-center gap-1"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Watch Video
          </a>
          <button
            onClick={() => copyToClipboard(window.location.href, "link")}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 ml-3"
          >
            {copied === "link" ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Share2 className="w-3.5 h-3.5" />
            )}
            {copied === "link" ? "Copied!" : "Share"}
          </button>
          <button
            onClick={() => copyToClipboard(guide.guide_markdown, "md")}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 ml-3"
          >
            {copied === "md" ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
            {copied === "md" ? "Copied!" : "Copy Markdown"}
          </button>
          <div className="flex-1" />
          <Button
            variant="danger"
            size="sm"
            onClick={handleDelete}
            loading={deleting}
          >
            <Trash2 className="w-3.5 h-3.5 mr-1" />
            Delete
          </Button>
        </div>
      </div>

      {/* TL;DR Section */}
      {guide.guide_json?.tldr && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              📋 TL;DR
            </h2>
          </div>
          <div className="px-6 py-4">
            <p className="text-sm text-gray-700 leading-relaxed">{guide.guide_json.tldr}</p>
          </div>
        </div>
      )}

      {/* Theme Blocks */}
      {guide.guide_json?.themes && guide.guide_json.themes.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
              🧩
            </span>
            Key Themes
          </h2>
          <div className="space-y-2">
            {guide.guide_json.themes.map((theme, i) => (
              <ThemeBlock 
                key={i} 
                theme={theme} 
                index={i} 
                defaultOpen={i === 0} 
                onTimestampClick={handleTimestampClick}
              />
            ))}
          </div>
        </div>
      )}

      {/* Memory Questions */}
      {guide.guide_json?.memory_questions && guide.guide_json.memory_questions.length > 0 && (
        <RefreshableQuestions questions={guide.guide_json.memory_questions} />
      )}
      {/* Reflection & Notes Section */}
      <div className="mb-6">
        <ReflectionSection
          guideId={guide.id}
          prompts={guide.guide_json?.reflection_question ? [guide.guide_json.reflection_question] : undefined}
        />
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getGuides, deleteGuide } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { SkeletonCard } from "@/components/ui/Skeleton";
import {
  Search,
  BookOpen,
  Clock,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
} from "lucide-react";
import { formatDate, getYouTubeThumbnail } from "@/lib/utils";
import type { StudyGuideListItem, Persona } from "@/types";

const PERSONA_FILTERS: { label: string; value: Persona | "all" }[] = [
  { label: "All", value: "all" },
  { label: "🌱 Beginner", value: "beginner" },
  { label: "🎓 Academic", value: "academic" },
  { label: "⚡ Practitioner", value: "practitioner" },
];

const PERSONA_EMOJI: Record<string, string> = {
  beginner: "🌱",
  academic: "🎓",
  practitioner: "⚡",
};

const PAGE_SIZE = 9;

export default function LibraryPage() {
  const router = useRouter();
  const [guides, setGuides] = useState<StudyGuideListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [persona, setPersona] = useState<Persona | "all">("all");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  const handleDelete = async (e: React.MouseEvent, guideId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this study guide? This cannot be undone.")) return;
    try {
      await deleteGuide(guideId);
      fetchGuides();
    } catch {
      // ignore
    }
  };

  const fetchGuides = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGuides(
        page,
        PAGE_SIZE,
        search || undefined,
        persona === "all" ? undefined : persona,
      );
      setGuides(data.guides);
      setTotalCount(data.total);
    } catch {
      // Silently fail — user sees empty state
    } finally {
      setLoading(false);
    }
  }, [page, search, persona]);

  useEffect(() => {
    fetchGuides();
  }, [fetchGuides]);

  // Reset page on filter changes
  useEffect(() => {
    setPage(1);
  }, [search, persona]);

  return (
    <div>
      {/* Header row */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Library
          </h1>
          {!loading && (
            <p className="text-xs text-gray-400 mt-0.5">
              {totalCount} guide{totalCount !== 1 ? "s" : ""}
            </p>
          )}
        </div>
        <Button
          size="sm"
          onClick={() => router.push("/dashboard")}
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          New Guide
        </Button>
      </div>

      {/* Search + filters — single row */}
      <div className="flex flex-col sm:flex-row gap-2 mb-5">
        <div className="flex-1 max-w-sm">
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>
        <div className="flex gap-1.5">
          {PERSONA_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setPersona(f.value)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                persona === f.value
                  ? "bg-indigo-100 text-indigo-700"
                  : "bg-white text-gray-500 hover:bg-gray-50 border border-gray-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : guides.length === 0 ? (
        <div className="text-center py-20">
          <BookOpen className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <h2 className="text-base font-semibold text-gray-900 mb-1">
            {search || persona !== "all"
              ? "No matches"
              : "No guides yet"}
          </h2>
          <p className="text-sm text-gray-500 mb-5">
            {search || persona !== "all"
              ? "Try different search terms or filters."
              : "Create your first study guide from a YouTube video."}
          </p>
          {!search && persona === "all" && (
            <Button onClick={() => router.push("/dashboard")}>
              Create First Guide
            </Button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {guides.map((guide) => (
              <div
                key={guide.id}
                role="button"
                tabIndex={0}
                onClick={() => router.push(`/guide/${guide.id}`)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") router.push(`/guide/${guide.id}`); }}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden text-left hover:shadow-md hover:border-gray-300 hover:-translate-y-0.5 transition-all duration-200 group cursor-pointer"
              >
                {/* Thumbnail */}
                <div className="relative">
                  <img
                    src={getYouTubeThumbnail(guide.video_id)}
                    alt={guide.title}
                    className="w-full h-32 object-cover"
                  />
                  <span className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded-md px-1.5 py-0.5 text-[10px] font-medium text-gray-700">
                    {PERSONA_EMOJI[guide.persona]} {guide.persona}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, guide.id)}
                    title="Delete guide"
                    className="absolute top-2 left-2 p-1.5 rounded-md bg-white/90 backdrop-blur-sm text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-500 hover:bg-red-50 transition-all duration-200"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {/* Info */}
                <div className="p-3">
                  <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5 group-hover:text-indigo-700 transition-colors">
                    {guide.title}
                  </h3>
                  <div className="flex items-center justify-between text-[11px] text-gray-400">
                    <span className="truncate">{guide.channel_name}</span>
                    <span className="flex items-center gap-1 flex-shrink-0 ml-2">
                      <Clock className="w-3 h-3" />
                      {formatDate(guide.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                title="Previous page"
                className="p-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-gray-500">
                {page} / {totalPages}
              </span>
              <button
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
                title="Next page"
                className="p-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

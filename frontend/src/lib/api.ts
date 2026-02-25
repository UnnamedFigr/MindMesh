/**
 * Backend API client.
 * All requests include the Supabase access token for authentication.
 * In demo mode, all calls return mock data from lib/demo.ts.
 * In dev mode, calls go to the real backend with a dev auth token.
 */

import { createClient } from "@/lib/supabase/client";
import {
  isDemoMode,
  isDevMode,
  demoGetCredits,
  demoGetGuides,
  demoGetGuide,
  demoCreateGuide,
  demoGetJobStatus,
  demoDeleteGuide,
} from "@/lib/demo";
import type {
  CreditStatus,
  GuideListResponse,
  Job,
  JobCreatedResponse,
  StudyGuide,
  Persona,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Helper ─────────────────────────────────────────────────────

async function getAuthHeaders(): Promise<Record<string, string>> {
  // Dev mode: send a dev token (backend accepts it when ENVIRONMENT=development)
  if (isDevMode()) {
    return {
      Authorization: "Bearer dev-mode",
      "Content-Type": "application/json",
    };
  }

  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Not authenticated");
  }

  return {
    Authorization: `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  };
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message =
      errorData?.error?.message ||
      errorData?.detail?.message ||
      `API error: ${response.status}`;
    const error = new Error(message) as Error & {
      status: number;
      code: string;
    };
    error.status = response.status;
    error.code = errorData?.error?.code || errorData?.detail?.code || "UNKNOWN";
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// ── Guides ─────────────────────────────────────────────────────

export async function createGuide(
  youtubeUrl: string,
  persona: Persona
): Promise<JobCreatedResponse> {
  if (isDemoMode()) return demoCreateGuide(youtubeUrl, persona);
  return apiFetch<JobCreatedResponse>("/api/guides", {
    method: "POST",
    body: JSON.stringify({ youtube_url: youtubeUrl, persona }),
  });
}

export async function getGuides(
  page = 1,
  perPage = 12,
  search?: string,
  persona?: Persona
): Promise<GuideListResponse> {
  if (isDemoMode()) return demoGetGuides(page, perPage, search, persona);
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (search) params.set("search", search);
  if (persona) params.set("persona", persona);

  return apiFetch<GuideListResponse>(`/api/guides?${params}`);
}

export async function getGuide(guideId: string): Promise<StudyGuide> {
  if (isDemoMode()) {
    const guide = demoGetGuide(guideId);
    if (!guide) throw new Error("Guide not found");
    return guide;
  }
  return apiFetch<StudyGuide>(`/api/guides/${guideId}`);
}

export async function deleteGuide(guideId: string): Promise<void> {
  if (isDemoMode()) return demoDeleteGuide(guideId);
  return apiFetch<void>(`/api/guides/${guideId}`, { method: "DELETE" });
}

// ── Jobs ───────────────────────────────────────────────────────

export async function getJobStatus(jobId: string): Promise<Job> {
  if (isDemoMode()) return demoGetJobStatus(jobId);
  return apiFetch<Job>(`/api/jobs/${jobId}`);
}

// ── Credits ────────────────────────────────────────────────────

export async function getCredits(): Promise<CreditStatus> {
  if (isDemoMode()) return demoGetCredits();
  return apiFetch<CreditStatus>("/api/credits");
}

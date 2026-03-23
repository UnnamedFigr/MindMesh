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
  AssociationListResponse,
  CheckoutSessionResponse,
  CreditStatus,
  GuideListResponse,
  Job,
  JobCreatedResponse,
  PortalSessionResponse,
  Reflection,
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

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      "Unable to connect to the server. Please make sure the backend is running."
    );
  }

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

// ── Associations (Pro) ─────────────────────────────────────────

export async function getAssociations(
  guideId: string
): Promise<AssociationListResponse> {
  if (isDemoMode()) return { guide_id: guideId, associations: [] };
  return apiFetch<AssociationListResponse>(
    `/api/guides/${guideId}/associations`
  );
}

// ── Reflections (Pro) ──────────────────────────────────────────

export async function getReflection(
  guideId: string
): Promise<Reflection | null> {
  if (isDemoMode()) return null;
  return apiFetch<Reflection | null>(`/api/guides/${guideId}/reflection`);
}

export async function saveReflection(
  guideId: string,
  content: string
): Promise<Reflection> {
  if (isDemoMode()) {
    throw new Error("Reflections are not available in demo mode");
  }
  return apiFetch<Reflection>(`/api/guides/${guideId}/reflection`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

// ── Billing ────────────────────────────────────────────────────

export async function createCheckoutSession(
  priceId: string,
  successUrl: string,
  cancelUrl: string
): Promise<CheckoutSessionResponse> {
  return apiFetch<CheckoutSessionResponse>("/api/billing/checkout", {
    method: "POST",
    body: JSON.stringify({
      price_id: priceId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
  });
}

export async function createPortalSession(): Promise<PortalSessionResponse> {
  return apiFetch<PortalSessionResponse>("/api/billing/portal", {
    method: "POST",
  });
}

export async function getBillingStatus(): Promise<CreditStatus> {
  return apiFetch<CreditStatus>("/api/billing/status");
}

export async function activateCheckoutSession(sessionId: string): Promise<CreditStatus> {
  return apiFetch<CreditStatus>(
    `/api/billing/activate?session_id=${encodeURIComponent(sessionId)}`,
    { method: "POST" }
  );
}

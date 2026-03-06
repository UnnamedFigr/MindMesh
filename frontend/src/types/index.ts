// ── Persona Types ──────────────────────────────────────────────
export type Persona = "beginner" | "academic" | "practitioner";
export type Tier = "free" | "core" | "pro";

// ── Job Types ──────────────────────────────────────────────────
export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_step: string | null;
  error_message: string | null;
  result_id: string | null;
  created_at: string;
  completed_at: string | null;
}

// ── Guide Types ────────────────────────────────────────────────
export interface StudyGuideListItem {
  id: string;
  video_id: string;
  title: string;
  channel_name: string;
  thumbnail_url: string | null;
  persona: Persona;
  tier: Tier;
  created_at: string;
}

export interface StudyGuide {
  id: string;
  video_id: string;
  youtube_id: string;
  title: string;
  channel_name: string;
  thumbnail_url: string | null;
  persona: Persona;
  tier: Tier;
  guide_json: GuideJSON | null;
  guide_markdown: string;
  triage_result: TriageResult | null;
  created_at: string;
}

export interface GuideJSON {
  tldr?: string;
  memory_questions?: MemoryQuestions[] | null;
  themes: ThemeBlock[];
  quiz?: QuizQuestion[];
  reflection_question?: string;
}

export interface MemoryQuestions {
  question: string;
  answer: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface ThemeBlock {
  theme_number: number;
  title: string;
  time_range: string;
  core_concept: string;
  mechanics: string[];
  analogy_or_example: string;
  subtopics?: string[];
  deep_dive?: DeepDive;
}

export interface DeepDive {
  explanation: string;
  technical_detail?: string;
  related_concept?: string;
}

export interface TriageResult {
  is_educational: boolean;
  confidence: number;
  content_type: string;
  language: string;
  primary_topic: string;
  estimated_complexity: string;
  reason: string;
}

// ── Credit Types ───────────────────────────────────────────────
export interface CreditStatus {
  credits_used: number;
  daily_credit_limit: number;
  credits_remaining: number;
  reset_at?: string;
  tier: Tier;
}

// ── API Response Types ─────────────────────────────────────────
export interface APIError {
  error: {
    code: string;
    message: string;
  };
}

export interface GuideListResponse {
  guides: StudyGuideListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface JobCreatedResponse {
  job_id: string;
  message: string;
}

// ── Component Props ────────────────────────────────────────────
export interface PersonaOption {
  id: Persona;
  name: string;
  emoji: string;
  description: string;
}

export const PERSONA_OPTIONS: PersonaOption[] = [
  {
    id: "beginner",
    name: "Beginner",
    emoji: "🌱",
    description: "Simple language, everyday analogies",
  },
  {
    id: "academic",
    name: "Academic",
    emoji: "🎓",
    description: "Technical depth, mechanisms, frameworks",
  },
];

// ── Processing Steps ───────────────────────────────────────────
export const STEP_LABELS: Record<string, string> = {
  queued: "Queued...",
  validating_video: "Validating video...",
  fetching_transcript: "Fetching transcript...",
  checking_credits: "Checking credits...",
  analyzing_content: "Analyzing content...",
  generating_guide: "Building your study guide...",
  saving_results: "Saving results...",
  done: "Complete!",
};

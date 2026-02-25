"""
Pydantic output schemas for OpenAI Structured Outputs.

These models define the EXACT JSON structure that GPT must return.
OpenAI's Structured Outputs mode guarantees valid JSON matching these schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Triage Output ─────────────────────────────────────────────────────


class TriageResult(BaseModel):
    """Classification result from the triage service (GPT-4.1-nano)."""

    is_educational: bool = Field(
        ..., description="Whether the content is educational."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0–1.0)."
    )
    content_type: str = Field(
        ...,
        description=(
            "Content category: lecture, tutorial, podcast, interview, "
            "documentary, workshop, entertainment, music, other"
        ),
    )
    language: str = Field(
        ..., description="ISO 639-1 language code (e.g., 'en', 'es')."
    )
    primary_topic: str = Field(
        ..., description="Brief 1-sentence topic summary."
    )
    estimated_complexity: str = Field(
        ..., description="beginner, intermediate, or advanced"
    )
    reason: str = Field(
        ..., description="One-sentence explanation of the classification."
    )


# ── Study Guide Output (Core Tier) ───────────────────────────────────


class ClickbaitScore(BaseModel):
    """Assessment of title vs. actual content alignment."""

    score: int = Field(
        ..., ge=1, le=10, description="1 = pure clickbait, 10 = perfectly accurate title"
    )
    verdict: str = Field(
        ..., description="1-sentence assessment of the title's accuracy."
    )


class QuickBrief(BaseModel):
    """At-a-glance summary section of the study guide."""

    clickbait_score: ClickbaitScore
    time_saved_minutes: int = Field(
        ..., ge=0, description="Estimated minutes saved by reading the guide vs. watching."
    )
    hook: str = Field(
        ..., description="Punchy 1-sentence summary of the video's core thesis."
    )
    key_takeaways: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 key takeaways, each starting with an emoji.",
    )
    highlight_quote: str = Field(
        ..., description="Most impactful or memorable quote from the video."
    )
    highlight_quote_timestamp: str = Field(
        ..., description="Timestamp of the quote in MM:SS format."
    )


class ThemeBlock(BaseModel):
    """A thematic section of the study guide."""

    theme_number: int = Field(..., ge=1, description="Sequential theme number.")
    title: str = Field(..., description="Descriptive theme title.")
    time_range: str = Field(
        ..., description="Video time range, e.g. 'MM:SS – MM:SS' or 'H:MM:SS – H:MM:SS' for longer videos."
    )
    core_concept: str = Field(
        ..., description="1–2 sentence explanation of the core concept."
    )
    mechanics: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Up to 6 bullet points explaining how/why (the mechanics).",
    )
    analogy_or_example: str = Field(
        ..., description="A real-world analogy or concrete example."
    )


class StudyGuideCore(BaseModel):
    """Core tier study guide output (free users)."""

    quick_brief: QuickBrief
    themes: list[ThemeBlock] = Field(
        ...,
        min_length=2,
        description="Thematic breakdown (2+ themes based on content length).",
    )


# ── Pro Tier Extensions ──────────────────────────────────────────────


class QuizQuestion(BaseModel):
    """A multiple-choice quiz question for active recall."""

    question: str = Field(..., description="The quiz question.")
    options: list[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Exactly 4 answer options (A–D).",
    )
    correct_index: int = Field(
        ..., ge=0, le=3, description="Index of the correct answer (0–3)."
    )
    explanation: str = Field(
        ..., description="Brief explanation of why this is correct."
    )
    timestamp: str = Field(
        ..., description="Where in the video the answer can be found (MM:SS)."
    )


class StudyGuidePro(StudyGuideCore):
    """Pro tier study guide output (paid users) — extends Core."""

    quiz: list[QuizQuestion] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 active recall quiz questions.",
    )
    reflection_question: str = Field(
        ...,
        description=(
            "An open-ended reflection question connecting the material to the learner's life."
        ),
    )

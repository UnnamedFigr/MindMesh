"""
Pydantic output schemas for OpenAI Structured Outputs.

These models define the EXACT JSON structure that GPT must return.
OpenAI's Structured Outputs mode guarantees valid JSON matching these schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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



class MemoryQuestions(BaseModel):
    question: str = Field(
        ..., description="The question to be asked."
    )
    answer: str = Field(
        ..., description="The answer to the question."
    )

class DeepDive(BaseModel):
    """Optional deep-dive content nested under a subtopic."""

    explanation: str = Field(
        default=None, description="Detailed explanation or advanced concept (2-4 sentences)."
    )
    technical_detail: str = Field(
        default=None, description="Optional technical detail or mechanism."
    )
    related_concept: str = Field(
        default=None, description="Optional related concept or framework."
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
    subtopics: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Optional 2-4 expandable subtopics that break down the theme into finer concepts.",
    )
    deep_dive: DeepDive = Field(
        default=None, description="Optional deep-dive content for advanced learners."
    )


class StudyGuideCore(BaseModel):
    """Core tier study guide output (free users)."""

    tldr: str = Field(
        ..., description="A concise TL;DR summary of the video, dynamically scaled to the video's length and complexity (2-8 sentences).",
    )
    memory_questions: list[MemoryQuestions] = Field(
        ...,
        min_length=3,
        max_length=15,
        description="A dynamically scaled list of 3-15 memory questions depending on video length and complexity.",
    )
    themes: list[ThemeBlock] = Field(
        ...,
        min_length=2,
        description="Thematic breakdown (2+ themes based on content length).",
    )

    @model_validator(mode="before")
    @classmethod
    def drop_empty_mechanic_themes(cls, data: dict) -> dict:
        """Remove themes where the LLM returned an empty mechanics list."""
        if isinstance(data, dict) and "themes" in data:
            data["themes"] = [
                t for t in data["themes"]
                if not isinstance(t, dict) or t.get("mechanics")
            ]
        return data


# ── Pro Tier Extensions ──────────────────────────────────────────────


class QuizQuestion(BaseModel):
    """A single multiple-choice quiz question."""

    question: str = Field(..., description="The quiz question text.")
    options: list[str] = Field(
        ..., min_length=4, max_length=4, description="Exactly 4 answer options (A–D)."
    )
    correct_index: int = Field(
        ..., ge=0, le=3, description="0-based index of the correct answer."
    )
    explanation: str = Field(
        ..., description="Brief explanation of why the correct answer is right."
    )


class StudyGuidePro(StudyGuideCore):
    """Pro tier study guide output (paid users) — extends Core."""

    reflection_question: str = Field(
        ...,
        description=(
            "An open-ended reflection question connecting the material to the learner's life."
        ),
    )
    quiz: list[QuizQuestion] = Field(
        default_factory=list,
        min_length=0,
        max_length=10,
        description="3–5 multiple-choice quiz questions for active recall.",
    )

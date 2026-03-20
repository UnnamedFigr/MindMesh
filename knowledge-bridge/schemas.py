"""Pydantic schemas for all Gemini structured-output responses.

These are generic — they carry no MindMesh-specific logic.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Extraction schemas ──────────────────────────────────────────

class BestPractice(BaseModel):
    category: str = Field(
        description="Short label, e.g. 'API Design', 'Error Handling', 'Testing'."
    )
    rule: str = Field(
        description="A concrete, directive best-practice statement."
    )
    rationale: str = Field(
        description="Why this practice matters."
    )
    evidence_source: str = Field(
        description="Which source document this came from."
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="How strongly the source supports this practice."
    )
    applicable_to: list[Literal["backend", "frontend", "database", "testing", "general"]] = Field(
        description="Which layers this practice applies to."
    )


class BestPracticesResponse(BaseModel):
    practices: list[BestPractice]
    source_summary: str = Field(
        description="One-paragraph summary of what the sources collectively cover."
    )
    gaps_noted: list[str] = Field(
        description="Topics the sources do not cover well.",
        default_factory=list,
    )


class AntiPattern(BaseModel):
    category: str = Field(
        description="Short label, e.g. 'Security', 'Performance', 'Architecture'."
    )
    pattern: str = Field(
        description="Description of the problematic pattern to avoid."
    )
    why_bad: str = Field(
        description="Why this pattern is harmful or risky."
    )
    preferred_alternative: str = Field(
        description="What to do instead."
    )
    evidence_source: str = Field(
        description="Which source document this came from."
    )


class AntiPatternsResponse(BaseModel):
    anti_patterns: list[AntiPattern]


# ── Clarification schema ────────────────────────────────────────

class ClarificationAnswer(BaseModel):
    question: str
    answer: str = Field(
        description="Direct answer grounded in the source documents."
    )
    source_references: list[str] = Field(
        description="Specific source sections or documents that informed this answer.",
        default_factory=list,
    )
    confidence: Literal["high", "medium", "low"]
    follow_up_suggestions: list[str] = Field(
        description="Useful follow-up questions based on the answer.",
        default_factory=list,
    )


# ── Refinement schema ───────────────────────────────────────────

class InstructionDelta(BaseModel):
    section: str = Field(
        description="Section heading where the change applies."
    )
    change_type: Literal["add", "update", "remove"]
    current_text: Optional[str] = Field(
        default=None,
        description="Existing text to replace or remove. Null for 'add'.",
    )
    proposed_text: str = Field(
        description="New or replacement text."
    )
    rationale: str = Field(
        description="Why this change improves the instruction."
    )
    source_evidence: str = Field(
        description="Which source supports this change."
    )


class RefinementResponse(BaseModel):
    deltas: list[InstructionDelta]
    unchanged_sections: list[str] = Field(
        description="Sections that are already well-covered by the sources.",
        default_factory=list,
    )
    new_sections_suggested: list[str] = Field(
        description="New sections worth adding to the instruction file.",
        default_factory=list,
    )

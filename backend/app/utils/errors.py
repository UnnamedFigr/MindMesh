"""
MindMesh custom exception hierarchy.

Every error carries a machine-readable `code` and a human-friendly `user_message`.
The global exception handler in main.py catches these and returns structured JSON.
"""

from __future__ import annotations


class MindMeshError(Exception):
    """Base exception for all MindMesh errors."""

    code: str = "INTERNAL_ERROR"
    user_message: str = "Something went wrong. Please try again."
    status_code: int = 500

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        user_message: str | None = None,
        status_code: int | None = None,
    ):
        self.detail = detail or self.user_message
        if code:
            self.code = code
        if user_message:
            self.user_message = user_message
        if status_code:
            self.status_code = status_code
        super().__init__(self.detail)


class ValidationError(MindMeshError):
    """Invalid user input (URL, parameters, etc.)."""

    code = "VALIDATION_ERROR"
    user_message = "Invalid input. Please check and try again."
    status_code = 400


class TranscriptError(MindMeshError):
    """YouTube / Whisper transcript failures."""

    code = "TRANSCRIPT_ERROR"
    user_message = (
        "We couldn't extract a transcript from this video. "
        "It may be private, age-restricted, or lack spoken content."
    )
    status_code = 422


class TriageError(MindMeshError):
    """Content triage / classification failures."""

    code = "TRIAGE_ERROR"
    user_message = (
        "This content appears to be entertainment rather than educational. "
        "MindMesh works best with lectures, tutorials, and informational videos."
    )
    status_code = 422


class GenerationError(MindMeshError):
    """OpenAI study guide generation failures."""

    code = "GENERATION_ERROR"
    user_message = (
        "Something went wrong generating your guide. "
        "Please try again — this won't cost a credit."
    )
    status_code = 502


class CreditError(MindMeshError):
    """Rate limit or credit exhaustion."""

    code = "CREDIT_EXHAUSTED"
    user_message = "You've used all your daily credits. Upgrade to Pro for 15/day."
    status_code = 429


class RateLimitError(MindMeshError):
    """Too many requests or concurrent jobs."""

    code = "RATE_LIMITED"
    user_message = "Please wait a moment before submitting another request."
    status_code = 429


class SpendCapError(MindMeshError):
    """Global daily spend cap reached."""

    code = "SPEND_CAP_REACHED"
    user_message = "We're experiencing high traffic. Please try again later."
    status_code = 503


class AuthError(MindMeshError):
    """Authentication / authorization failures."""

    code = "AUTH_ERROR"
    user_message = "Please sign in to continue."
    status_code = 401

"""
API request schemas — Pydantic models for incoming HTTP requests.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateGuideRequest(BaseModel):
    """Request body for POST /api/guides."""

    youtube_url: str = Field(
        ...,
        description="YouTube video URL (any format)",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    persona: str = Field(
        ...,
        description="Learning persona: beginner or academic",
        pattern="^(beginner|academic)$",
        example="beginner",
    )


class RetryJobRequest(BaseModel):
    """Request body for POST /api/jobs/{id}/retry."""

    pass

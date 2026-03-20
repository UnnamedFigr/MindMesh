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


class SaveReflectionRequest(BaseModel):
    """Request body for POST /api/guides/{id}/reflection."""

    content: str = Field(
        ..., min_length=1, max_length=5000, description="The user's reflection text."
    )


class CheckoutRequest(BaseModel):
    """Request body for POST /api/billing/checkout."""

    price_id: str = Field(..., description="Stripe Price ID for the Pro subscription.")
    success_url: str = Field(..., description="URL to redirect after successful payment.")
    cancel_url: str = Field(..., description="URL to redirect if user cancels checkout.")

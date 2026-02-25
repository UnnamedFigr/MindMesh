"""
API response schemas — Pydantic models for outgoing HTTP responses.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-friendly error message")
    detail: str | None = Field(None, description="Additional technical detail (dev only)")


class JobCreatedResponse(BaseModel):
    """Response for POST /api/guides — job accepted."""

    job_id: str
    status: str = "pending"
    message: str = "Study guide generation started"


class JobStatusResponse(BaseModel):
    """Response for GET /api/jobs/{id}."""

    job_id: str
    status: str
    progress: int = 0
    current_step: str | None = None
    error_message: str | None = None
    result_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class VideoInfo(BaseModel):
    """Video metadata embedded in responses."""

    youtube_id: str
    title: str | None = None
    channel_name: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None


class StudyGuideResponse(BaseModel):
    """Full study guide response for GET /api/guides/{id}."""

    id: str
    video_id: str
    youtube_id: str
    title: str
    channel_name: str
    thumbnail_url: str | None = None
    persona: str
    tier: str
    guide_json: dict[str, object] | None = None
    guide_markdown: str = ""
    triage_result: dict[str, object] | None = None
    transcript_timestamped: list[dict[str, object]] | None = None
    created_at: datetime


class StudyGuideListItem(BaseModel):
    """Summary item for GET /api/guides (library list)."""

    id: str
    video_id: str
    title: str
    channel_name: str
    thumbnail_url: str | None = None
    persona: str
    tier: str
    created_at: datetime


class StudyGuideListResponse(BaseModel):
    """Paginated list of study guides."""

    guides: list[StudyGuideListItem]
    total: int
    page: int
    per_page: int


class CreditStatusResponse(BaseModel):
    """Credit balance information."""

    credits_used: int
    daily_credit_limit: int
    credits_remaining: int
    reset_at: datetime | None = None
    tier: str = "free"
    tier: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    environment: str
    version: str = "0.1.0"

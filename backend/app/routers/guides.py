"""
Guides router — study guide CRUD operations.

Endpoints:
  POST /api/guides          — Create a new study guide (starts job)
  GET  /api/guides          — List user's guides
  GET  /api/guides/{id}     — Get a specific guide
  DELETE /api/guides/{id}   — Delete a guide
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

import structlog

from app.dependencies import check_rate_limit, get_current_user, mark_job_finished, mark_job_started
from app.models.requests import CreateGuideRequest
from app.models.responses import (
    ErrorResponse,
    JobCreatedResponse,
    StudyGuideListResponse,
    StudyGuideListItem,
    StudyGuideResponse,
)
from app.services.credits import check_credits, get_credit_cost
from app.services.worker import check_existing_guide, create_job, process_job
from app.utils.youtube import extract_video_id, validate_video

logger = structlog.get_logger()

router = APIRouter(prefix="/api/guides", tags=["guides"])

@router.options("")
async def options_guides():
    # FastAPI's CORSMiddleware should have already set the appropriate headers.
    # This explicit OPTIONS handler just ensures a 200 OK response if it's hit.
    return {"status": "ok"}

@router.post(
    "",
    response_model=JobCreatedResponse,
    status_code=202,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
async def create_guide(
    request: CreateGuideRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    _rate_ok: None = Depends(check_rate_limit),
):
    """
    Start generating a study guide for a YouTube video.

    Returns a job ID that can be polled for status.
    """
    from app.config import get_settings

    settings = get_settings()
    user_id = user["sub"]

    # Extract and validate video ID
    video_id = extract_video_id(request.youtube_url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_URL", "message": "Invalid YouTube URL."},
        )

    # Check for existing guide (no duplicate creation)
    existing_id = await check_existing_guide(
        video_id, request.persona, user_id, _get_supabase()
    )
    if existing_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "GUIDE_EXISTS",
                "message": "You already have a guide for this video with this persona.",
                "guide_id": existing_id,
            },
        )

    # Check credits
    credit_cost = get_credit_cost()
    await check_credits(user_id, credit_cost, _get_supabase())

    # Create job
    job_id = await create_job(user_id, request.youtube_url, request.persona, _get_supabase())

    # Mark rate limit
    mark_job_started(user_id)

    # Start background processing
    background_tasks.add_task(
        _run_job,
        job_id=job_id,
        user_id=user_id,
        youtube_url=request.youtube_url,
        video_id=video_id,
        persona=request.persona,
    )

    logger.info(
        "guide.creation_started",
        job_id=job_id,
        user_id=user_id,
        video_id=video_id,
        persona=request.persona,
    )

    return JobCreatedResponse(
        job_id=job_id,
        message="Study guide generation started. Poll /api/jobs/{job_id} for status.",
    )


@router.get("", response_model=StudyGuideListResponse)
async def list_guides(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
    search: str | None = Query(None, max_length=200),
    persona: str | None = Query(None, pattern="^(beginner|academic|practitioner)$"),
):
    """List the current user's study guides with pagination."""
    user_id = user["sub"]
    supabase = _get_supabase()

    query = (
        supabase.table("study_guides")
        .select("id, video_id, persona, tier, created_at, videos(title, channel_name, thumbnail_url)", count="exact")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if persona:
        query = query.eq("persona", persona)
    if search:
        query = query.or_(f"videos.title.ilike.%{search}%,videos.channel_name.ilike.%{search}%")

    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    response = query.execute()

    items = []
    for row in response.data or []:
        video = row.get("videos", {}) or {}
        items.append(StudyGuideListItem(
            id=row["id"],
            video_id=row["video_id"],
            title=video.get("title", "Unknown"),
            channel_name=video.get("channel_name", "Unknown"),
            thumbnail_url=video.get("thumbnail_url"),
            persona=row["persona"],
            tier=row["tier"],
            created_at=row["created_at"],
        ))

    total = response.count or len(items)

    return StudyGuideListResponse(
        guides=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/{guide_id}",
    response_model=StudyGuideResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_guide(guide_id: str, user: dict = Depends(get_current_user)):
    """Get a specific study guide by ID."""
    user_id = user["sub"]
    supabase = _get_supabase()

    response = (
        supabase.table("study_guides")
        .select("*, videos(title, channel_name, thumbnail_url, youtube_id, transcript_timestamped)")
        .eq("id", guide_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Guide not found."})

    row = response.data
    video = row.get("videos", {}) or {}

    return StudyGuideResponse(
        id=row["id"],
        video_id=row["video_id"],
        youtube_id=video.get("youtube_id", row["video_id"]),
        title=video.get("title", "Unknown"),
        channel_name=video.get("channel_name", "Unknown"),
        thumbnail_url=video.get("thumbnail_url"),
        persona=row["persona"],
        tier=row["tier"],
        guide_json=row.get("guide_json"),
        guide_markdown=row.get("guide_markdown", ""),
        triage_result=row.get("triage_result"),
        transcript_timestamped=video.get("transcript_timestamped"),
        created_at=row["created_at"],
    )


@router.delete("/{guide_id}", status_code=204)
async def delete_guide(guide_id: str, user: dict = Depends(get_current_user)):
    """Delete a study guide."""
    user_id = user["sub"]
    supabase = _get_supabase()

    # Verify ownership
    existing = (
        supabase.table("study_guides")
        .select("id")
        .eq("id", guide_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Guide not found."})

    supabase.table("study_guides").delete().eq("id", guide_id).execute()

    # Also clean up concepts
    try:
        supabase.table("concepts").delete().eq("guide_id", guide_id).execute()
    except Exception:
        pass  # Non-fatal


# ── Helpers ────────────────────────────────────────────────────

def _get_supabase():
    """Get Supabase client (service role for backend ops). Uses in-memory dev store in dev mode."""
    from app.services.dev_store import is_dev_mode, get_dev_client

    if is_dev_mode():
        return get_dev_client()

    from supabase import create_client
    from app.config import get_settings

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def _run_job(job_id: str, user_id: str, youtube_url: str, video_id: str, persona: str):
    """Wrapper to run job and clean up rate limit state."""
    try:
        await process_job(
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            video_id=video_id,
            persona=persona,
            supabase_client=_get_supabase(),
        )
    finally:
        mark_job_finished(user_id)

"""
Jobs router — job status polling.

Endpoints:
  GET /api/jobs/{job_id}  — Get job status (for polling during generation)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

import structlog

from app.dependencies import get_current_user
from app.models.responses import ErrorResponse, JobStatusResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_job_status(job_id: str, user: dict = Depends(get_current_user)):
    """
    Get the current status of a processing job.

    Frontend polls this endpoint every 2-3 seconds during generation.
    """
    user_id = user["sub"]
    supabase = _get_supabase()

    response = (
        supabase.table("processing_jobs")
        .select("id, status, progress, current_step, error_message, result_id, created_at, completed_at")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Job not found."},
        )

    row = response.data

    return JobStatusResponse(
        job_id=row["id"],
        status=row["status"],
        progress=row.get("progress", 0),
        current_step=row.get("current_step"),
        error_message=row.get("error_message"),
        result_id=row.get("result_id"),
        created_at=row["created_at"],
        completed_at=row.get("completed_at"),
    )


def _get_supabase():
    """Get Supabase client. Uses in-memory dev store in dev mode."""
    from app.services.dev_store import is_dev_mode, get_dev_client

    if is_dev_mode():
        return get_dev_client()

    from supabase import create_client
    from app.config import get_settings

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)

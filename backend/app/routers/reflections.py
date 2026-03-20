"""
Reflections router — Pro tier reflection persistence.

Endpoints:
  POST /api/guides/{guide_id}/reflection  — Save or update a reflection
  GET  /api/guides/{guide_id}/reflection  — Load saved reflection
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.db import get_supabase
from app.dependencies import get_current_user
from app.models.requests import SaveReflectionRequest
from app.models.responses import ReflectionResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/guides", tags=["reflections"])


@router.post(
    "/{guide_id}/reflection",
    response_model=ReflectionResponse,
    status_code=200,
)
async def save_reflection(
    guide_id: str,
    request: SaveReflectionRequest,
    user: dict = Depends(get_current_user),
) -> ReflectionResponse:
    """
    Save or update the user's reflection for a guide.

    If a reflection already exists it is replaced (upsert by user_id + study_guide_id).
    """
    supabase = get_supabase()
    user_id = user["sub"]

    log = logger.bind(user_id=user_id, guide_id=guide_id)

    # Verify guide ownership
    guide_check = (
        supabase.table("study_guides")
        .select("id")
        .eq("id", guide_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not guide_check.data:
        raise HTTPException(status_code=404, detail="Guide not found")

    # Delete existing reflection first (manual upsert — reflections table has no unique constraint)
    supabase.table("reflections").delete().eq("study_guide_id", guide_id).eq(
        "user_id", user_id
    ).execute()

    result = (
        supabase.table("reflections")
        .insert(
            {
                "user_id": user_id,
                "study_guide_id": guide_id,
                "content": request.content,
            }
        )
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save reflection")

    row = result.data[0]
    log.info("reflection.saved", reflection_id=row["id"])

    return ReflectionResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        study_guide_id=str(row["study_guide_id"]),
        content=row["content"],
        created_at=row["created_at"],
    )


@router.get(
    "/{guide_id}/reflection",
    response_model=ReflectionResponse | None,
)
async def get_reflection(
    guide_id: str,
    user: dict = Depends(get_current_user),
) -> ReflectionResponse | None:
    """Load the user's saved reflection for a guide. Returns null if none exists."""
    supabase = get_supabase()
    user_id = user["sub"]

    result = (
        supabase.table("reflections")
        .select("*")
        .eq("study_guide_id", guide_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    row = result.data[0]
    return ReflectionResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        study_guide_id=str(row["study_guide_id"]),
        content=row["content"],
        created_at=row["created_at"],
    )

"""
Associations router — Web of Associations (Pro tier).

Endpoints:
  GET  /api/guides/{guide_id}/associations  — Related guides via concept similarity
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.db import get_supabase
from app.dependencies import get_current_user
from app.models.responses import AssociationItem, AssociationListResponse
from app.services.embeddings import find_similar_guides

logger = structlog.get_logger()

router = APIRouter(prefix="/api/guides", tags=["associations"])


@router.get(
    "/{guide_id}/associations",
    response_model=AssociationListResponse,
)
async def get_associations(
    guide_id: str,
    user: dict = Depends(get_current_user),
) -> AssociationListResponse:
    """
    Return guides semantically related to the requested guide.

    Requires the guide to have stored concept embeddings (Pro tier, generated
    by the background worker after guide creation). Returns empty list gracefully
    when no embeddings exist yet.
    """
    supabase = get_supabase()
    user_id = user["sub"]

    log = logger.bind(user_id=user_id, guide_id=guide_id)

    # Verify ownership and fetch guide_json for query text
    guide_res = (
        supabase.table("study_guides")
        .select("id,guide_json")
        .eq("id", guide_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not guide_res.data:
        raise HTTPException(status_code=404, detail="Guide not found")

    guide_json = guide_res.data[0].get("guide_json") or {}

    # Build query text from tldr or first theme title
    query_text = guide_json.get("tldr", "")
    if not query_text:
        themes = guide_json.get("themes", [])
        if themes:
            query_text = themes[0].get("title", "")

    if not query_text:
        return AssociationListResponse(guide_id=guide_id, associations=[])

    # Find similar guides using concept embeddings
    similar = await find_similar_guides(query_text, user_id, supabase, limit=6)
    if not similar:
        return AssociationListResponse(guide_id=guide_id, associations=[])

    # Exclude current guide
    other_guide_ids = [
        str(item["guide_id"]) for item in similar if str(item["guide_id"]) != guide_id
    ]
    if not other_guide_ids:
        return AssociationListResponse(guide_id=guide_id, associations=[])

    similarity_map = {str(item["guide_id"]): float(item["max_similarity"]) for item in similar}

    # Batch fetch guide metadata
    guides_res = (
        supabase.table("study_guides")
        .select("id,video_id,created_at")
        .in_("id", other_guide_ids)
        .execute()
    )
    if not guides_res.data:
        return AssociationListResponse(guide_id=guide_id, associations=[])

    # Batch fetch video titles
    video_ids = list({g["video_id"] for g in guides_res.data})
    videos_res = (
        supabase.table("videos")
        .select("youtube_id,title,channel_name,thumbnail_url")
        .in_("youtube_id", video_ids)
        .execute()
    )
    videos_map = {v["youtube_id"]: v for v in (videos_res.data or [])}

    associations = []
    for g in guides_res.data:
        v = videos_map.get(g["video_id"], {})
        associations.append(
            AssociationItem(
                guide_id=str(g["id"]),
                title=v.get("title") or "Untitled",
                channel_name=v.get("channel_name") or "",
                thumbnail_url=v.get("thumbnail_url"),
                similarity_score=similarity_map.get(str(g["id"]), 0.0),
                created_at=g["created_at"],
            )
        )

    # Sort by similarity descending
    associations.sort(key=lambda a: a.similarity_score, reverse=True)

    log.info("associations.fetched", count=len(associations))
    return AssociationListResponse(guide_id=guide_id, associations=associations[:5])

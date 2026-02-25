"""
Embeddings service for Web of Associations (Pro tier).

Generates concept embeddings using OpenAI text-embedding-3-small
and stores them in Supabase pgvector for similarity search.
"""

from __future__ import annotations

import structlog
from openai import AsyncOpenAI

from app.config import get_settings
from app.utils.errors import GenerationError

logger = structlog.get_logger()

# Model config
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512  # Reduced from 1536 for cost savings


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Uses OpenAI text-embedding-3-small with 512 dimensions.
    """
    if not texts:
        return []

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        return [item.embedding for item in response.data]
    except Exception as exc:
        logger.error("embeddings.generation_failed", error=str(exc), text_count=len(texts))
        raise GenerationError(
            f"Embedding generation failed: {exc}",
            code="EMBEDDING_FAILED",
            user_message="Failed to generate concept associations.",
        )


async def store_concept_embeddings(
    guide_id: str,
    concepts: list[dict],
    supabase_client,
) -> None:
    """
    Extract concepts from a guide and store their embeddings.

    concepts: list of {"name": str, "description": str}
    """
    if not concepts:
        return

    texts = [f"{c['name']}: {c['description']}" for c in concepts]
    embeddings = await generate_embeddings(texts)

    rows = []
    for concept, embedding in zip(concepts, embeddings):
        rows.append({
            "guide_id": guide_id,
            "concept_name": concept["name"],
            "concept_description": concept.get("description", ""),
            "embedding": embedding,
        })

    try:
        supabase_client.table("concepts").insert(rows).execute()
        logger.info("embeddings.stored", guide_id=guide_id, count=len(rows))
    except Exception as exc:
        # Non-fatal: guide still works without associations
        logger.warning("embeddings.store_failed", guide_id=guide_id, error=str(exc))


async def find_related_concepts(
    guide_id: str,
    concept_name: str,
    supabase_client,
    *,
    limit: int = 5,
    threshold: float = 0.7,
) -> list[dict]:
    """
    Find concepts related to a given concept across all of a user's guides.

    Uses pgvector cosine similarity search.
    """
    # First get the embedding for the query concept
    embeddings = await generate_embeddings([concept_name])
    if not embeddings:
        return []

    query_embedding = embeddings[0]

    try:
        # Use Supabase RPC for vector similarity search
        response = supabase_client.rpc(
            "match_concepts",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit,
                "exclude_guide_id": guide_id,
            },
        ).execute()

        if not response.data:
            return []

        return [
            {
                "concept_name": row["concept_name"],
                "concept_description": row["concept_description"],
                "guide_id": row["guide_id"],
                "similarity": row["similarity"],
            }
            for row in response.data
        ]
    except Exception as exc:
        logger.warning("embeddings.search_failed", error=str(exc))
        return []


async def find_similar_guides(
    text: str,
    user_id: str,
    supabase_client,
    *,
    limit: int = 5,
) -> list[dict]:
    """Find guides with similar concepts to a given text."""
    embeddings = await generate_embeddings([text])
    if not embeddings:
        return []

    try:
        response = supabase_client.rpc(
            "match_guides_by_concept",
            {
                "query_embedding": embeddings[0],
                "p_user_id": user_id,
                "match_count": limit,
            },
        ).execute()

        return response.data or []
    except Exception as exc:
        logger.warning("embeddings.guide_search_failed", error=str(exc))
        return []

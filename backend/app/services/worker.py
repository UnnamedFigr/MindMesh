"""
Background job worker service.

Orchestrates the full study guide pipeline:
1. Validate + fetch transcript
2. Triage content
3. Generate guide
4. Store results
5. Update job status
"""

from __future__ import annotations

import asyncio
import traceback
import uuid
from datetime import datetime, timezone

import structlog

from app.config import get_settings
from app.services.credits import (
    check_global_spend_cap,
    deduct_credits,
    get_credit_cost,
    log_api_usage,
    refund_credits,
)
from app.services.generator import generate_study_guide, render_guide_markdown
from app.services.transcript import fetch_transcript
from app.services.triage import triage_content
from app.utils.errors import (
    CreditError,
    GenerationError,
    MindMeshError,
    SpendCapError,
    TranscriptError,
    TriageError,
)
from app.utils.tokens import count_tokens, get_processing_strategy
from app.utils.youtube import validate_video

logger = structlog.get_logger()


async def update_job_status(
    job_id: str,
    status: str,
    supabase_client,
    *,
    progress: int | None = None,
    step: str | None = None,
    error_message: str | None = None,
    result_id: str | None = None,
) -> None:
    """Update job status in the database."""
    update_data: dict = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if progress is not None:
        update_data["progress"] = progress
    if step:
        update_data["current_step"] = step
    if error_message:
        update_data["error_message"] = error_message
    if result_id:
        update_data["result_id"] = result_id
    if status in ("completed", "failed"):
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()

    supabase_client.table("processing_jobs").update(update_data).eq("id", job_id).execute()


async def create_job(user_id: str, youtube_url: str, persona: str, supabase_client) -> str:
    """Create a new processing job and return its ID."""
    job_id = str(uuid.uuid4())
    supabase_client.table("processing_jobs").insert({
        "id": job_id,
        "user_id": user_id,
        "youtube_url": youtube_url,
        "persona": persona,
        "status": "pending",
        "progress": 0,
        "current_step": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return job_id


async def check_existing_guide(
    video_id: str, persona: str, user_id: str, supabase_client
) -> str | None:
    """Check if user already has a guide for this video + persona combo."""
    response = (
        supabase_client.table("study_guides")
        .select("id")
        .eq("video_id", video_id)
        .eq("persona", persona)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]["id"]
    return None


async def process_job(
    job_id: str,
    user_id: str,
    youtube_url: str,
    video_id: str,
    persona: str,
    supabase_client,
) -> None:
    """
    Main job processing pipeline.

    Runs as a background task. Updates job status at each step.
    """
    settings = get_settings()
    credit_cost = 0
    credits_deducted = False

    log = logger.bind(job_id=job_id, user_id=user_id, video_id=video_id)

    # Create a shared Groq client (OpenAI-compatible) for triage + generation
    from openai import OpenAI as _OpenAI

    openai_client = _OpenAI(
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
        timeout=300.0,
    )

    try:
        # ── Step 1: Validate video ─────────────────────────────
        await update_job_status(
            job_id, "processing", supabase_client, progress=5, step="validating_video"
        )
        log.info("job.step.validate")

        metadata = await validate_video(video_id)
        if not metadata:
            raise TranscriptError(
                "Could not validate video",
                code="VIDEO_INVALID",
                user_message="This video doesn't appear to exist or is not accessible.",
            )

        # ── Step 2: Check global spend cap ──────────────────────
        await check_global_spend_cap(supabase_client)

        # ── Step 3: Fetch transcript ───────────────────────────
        await update_job_status(
            job_id, "processing", supabase_client, progress=15, step="fetching_transcript"
        )
        log.info("job.step.transcript")

        transcript_data = await fetch_transcript(video_id, supabase_client)
        transcript_raw = transcript_data["transcript_raw"] if isinstance(transcript_data, dict) else transcript_data
        if not transcript_raw or len(str(transcript_raw).strip()) < 50:
            raise TranscriptError(
                "Transcript too short or empty",
                code="TRANSCRIPT_EMPTY",
                user_message="Could not extract enough text from this video. Try a different video.",
            )

        # Build a timestamped version for the LLM so theme time_range is accurate
        timestamped_segments = transcript_data.get("transcript_timestamped", []) if isinstance(transcript_data, dict) else []
        if timestamped_segments:
            transcript_for_llm = _format_transcript_with_timestamps(timestamped_segments)
            # Estimate video duration from the last transcript segment
            last_seg = timestamped_segments[-1]
            estimated_duration = int(last_seg.get("start", 0)) + int(last_seg.get("duration", 10))
            metadata.duration_seconds = estimated_duration
        else:
            transcript_for_llm = str(transcript_raw)

        # ── Step 4: Analyze transcript size ────────────────────
        # Use the ACTUAL text that will be sent to the LLM for token counting,
        # not the plain text (timestamped version is larger due to [MM:SS] prefixes)
        token_count = count_tokens(transcript_for_llm)
        strategy = get_processing_strategy(token_count)

        if strategy == "reject":
            raise TranscriptError(
                f"Transcript too long: {token_count} tokens",
                code="TRANSCRIPT_TOO_LONG",
                user_message="This video is too long to process. Maximum supported length is ~8 hours.",
            )

        log.info("job.tokens", tokens=token_count, strategy=strategy)

        # ── Step 4b: Choose AI model ──────────────────────────
        # Short videos → Groq (fast, free)
        # Long videos (30min+ / >15K tokens) → OpenAI GPT-4.1 (larger context, more reliable)
        duration = metadata.duration_seconds if metadata else None
        use_openai = (
            token_count > settings.long_video_token_threshold
            or (duration is not None and duration > 1800)
        )

        if use_openai:
            guide_client = _OpenAI(
                api_key=settings.openai_api_key,
                timeout=300.0,
            )
            guide_model = settings.guide_model_long
            log.info("job.model_routing", model=guide_model, reason="long_video")
        else:
            guide_client = openai_client  # Groq
            guide_model = settings.guide_model
            log.info("job.model_routing", model=guide_model, reason="short_video")

        # ── Step 5: Deduct credits ─────────────────────────────
        await update_job_status(
            job_id, "processing", supabase_client, progress=25, step="checking_credits"
        )

        credit_cost = get_credit_cost()
        await deduct_credits(user_id, credit_cost, supabase_client)
        credits_deducted = True

        # ── Step 6: Triage content ─────────────────────────────
        await update_job_status(
            job_id, "processing", supabase_client, progress=35, step="analyzing_content"
        )
        log.info("job.step.triage")

        # triage_content raises TriageError if content is non-educational
        triage_result = await triage_content(str(transcript_raw), openai_client)

        # ── Step 7: Generate study guide ───────────────────────
        await update_job_status(
            job_id, "processing", supabase_client, progress=50, step="generating_guide"
        )
        log.info("job.step.generate", strategy=strategy)

        # Determine tier from profile
        profile = (
            supabase_client.table("profiles")
            .select("tier")
            .eq("id", user_id)
            .single()
            .execute()
        )
        tier = profile.data["tier"] if profile.data else "free"

        guide_result = await generate_study_guide(
            transcript_raw=transcript_for_llm,
            token_count=token_count,
            persona=persona,
            tier=tier,
            openai_client=guide_client,
            video_title=metadata.title if metadata else "Unknown",
            channel_name=metadata.channel_name if metadata else "Unknown",
            duration_seconds=metadata.duration_seconds if metadata else None,
            model_name=guide_model,
        )

        await update_job_status(
            job_id, "processing", supabase_client, progress=80, step="saving_results"
        )

        # guide_result contains: content_json, content_markdown, input_tokens, output_tokens
        guide_json = guide_result["content_json"]
        markdown_content = guide_result["content_markdown"]
        output_tokens = guide_result.get("output_tokens", 0)

        # ── Step 8: Store study guide ──────────────────────────
        guide_id = str(uuid.uuid4())

        # Upsert video record
        timestamped = transcript_data.get("transcript_timestamped", []) if isinstance(transcript_data, dict) else []
        supabase_client.table("videos").upsert({
            "youtube_id": video_id,
            "title": metadata.title if metadata else "Unknown",
            "channel_name": metadata.channel_name if metadata else "Unknown",
            "thumbnail_url": metadata.thumbnail_url if metadata else None,
            "transcript_raw": str(transcript_raw),
            "transcript_timestamped": timestamped,
            "token_count": token_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="youtube_id").execute()

        # Store guide
        supabase_client.table("study_guides").insert({
            "id": guide_id,
            "user_id": user_id,
            "video_id": video_id,
            "persona": persona,
            "tier": tier,
            "guide_json": guide_json,
            "guide_markdown": markdown_content,
            "triage_result": triage_result.model_dump() if triage_result and hasattr(triage_result, "model_dump") else None,
            "processing_strategy": strategy,
            "token_count": token_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        # ── Step 9: Log usage ──────────────────────────────────
        estimated_cost = _estimate_cost(token_count, strategy, tier)
        await log_api_usage(
            user_id=user_id,
            job_id=job_id,
            model=settings.guide_model,
            input_tokens=token_count,
            output_tokens=output_tokens or int(token_count * 0.3),
            estimated_cost_usd=estimated_cost,
            supabase_client=supabase_client,
        )

        # ── Done ───────────────────────────────────────────────
        await update_job_status(
            job_id,
            "completed",
            supabase_client,
            progress=100,
            step="done",
            result_id=guide_id,
        )
        log.info("job.completed", guide_id=guide_id, tokens=token_count)

    except MindMeshError as exc:
        log.warning("job.failed.known", error=exc.code, message=str(exc))
        await update_job_status(
            job_id, "failed", supabase_client, error_message=exc.user_message
        )
        if credits_deducted:
            await refund_credits(user_id, credit_cost, supabase_client)

    except Exception as exc:
        log.error("job.failed.unexpected", error=str(exc), trace=traceback.format_exc())
        await update_job_status(
            job_id,
            "failed",
            supabase_client,
            error_message="An unexpected error occurred. Please try again.",
        )
        if credits_deducted:
            await refund_credits(user_id, credit_cost, supabase_client)


def _format_transcript_with_timestamps(segments: list[dict]) -> str:
    """
    Build a transcript string with inline timestamps so the LLM can
    produce accurate time_range values for each theme.

    Output format:
        [00:00] First segment text.
        [00:15] Second segment text.
        ...
    """
    parts: list[str] = []
    for seg in segments:
        start = seg.get("start", 0)
        text = seg.get("text", "")
        h = int(start // 3600)
        m = int((start % 3600) // 60)
        s = int(start % 60)
        if h > 0:
            ts = f"{h}:{m:02d}:{s:02d}"
        else:
            ts = f"{m:02d}:{s:02d}"
        parts.append(f"[{ts}] {text}")
    return "\n".join(parts)


def _estimate_cost(token_count: int, strategy: str, tier: str) -> float:
    """Rough cost estimation for monitoring purposes."""
    settings = get_settings()

    # GPT-4.1-mini pricing: $0.40 / 1M input, $1.60 / 1M output
    input_cost_per_m = 0.40
    output_cost_per_m = 1.60

    output_tokens_est = int(token_count * 0.3)

    # Triage cost (nano): negligible (~$0.0001)
    triage_cost = 0.0001

    if strategy == "chunk_and_merge":
        # Multiple calls: ~1.5x input + merge step
        input_cost = (token_count * 1.5 / 1_000_000) * input_cost_per_m
        output_cost = (output_tokens_est * 1.5 / 1_000_000) * output_cost_per_m
    else:
        input_cost = (token_count / 1_000_000) * input_cost_per_m
        output_cost = (output_tokens_est / 1_000_000) * output_cost_per_m

    total = triage_cost + input_cost + output_cost

    # Pro tier: quiz adds ~30% more tokens
    if tier == "pro":
        total *= 1.3

    return round(total, 6)

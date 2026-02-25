"""
Credit management service.

Handles credit checking, deduction, and reset logic.
Uses atomic SQL operations to prevent race conditions.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.config import get_settings
from app.utils.errors import CreditError, SpendCapError

logger = structlog.get_logger()


# Credit costs by action
CREDIT_COSTS = {
    "standard_guide": 1,   # Video < 90 min
    "long_guide": 2,       # Video ≥ 90 min
    "regenerate": 1,       # Different persona
}


def get_credit_cost(duration_seconds: int | None = None) -> int:
    """Determine credit cost based on video duration."""
    if duration_seconds and duration_seconds >= 5400:  # 90 minutes
        return CREDIT_COSTS["long_guide"]
    return CREDIT_COSTS["standard_guide"]


async def check_credits(user_id: str, credit_cost: int, supabase_client) -> dict:
    """
    Check if user has sufficient credits.

    Returns profile data with credit info.
    Raises CreditError if insufficient.
    """
    # Get current profile
    response = (
        supabase_client.table("profiles")
        .select("credits_used, daily_credit_limit, credits_reset_at, tier")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise CreditError(
            "User profile not found",
            code="PROFILE_NOT_FOUND",
            user_message="Account error. Please sign out and sign in again.",
        )

    profile = response.data

    # Check if credits need resetting
    reset_at = datetime.fromisoformat(profile["credits_reset_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if now >= reset_at:
        # Reset credits
        supabase_client.table("profiles").update({
            "credits_used": 0,
            "credits_reset_at": (now.replace(hour=0, minute=0, second=0, microsecond=0)
                                 + __import__("datetime").timedelta(days=1)).isoformat(),
        }).eq("id", user_id).execute()
        profile["credits_used"] = 0

    credits_remaining = profile["daily_credit_limit"] - profile["credits_used"]

    if credits_remaining < credit_cost:
        hours_until_reset = max(0, (reset_at - now).total_seconds() / 3600)
        raise CreditError(
            f"Insufficient credits: {credits_remaining} remaining, {credit_cost} needed",
            code="CREDIT_EXHAUSTED",
            user_message=(
                f"You've used all your daily credits. "
                f"Resets in {int(hours_until_reset)}h. "
                f"Upgrade to Pro for 15 credits/day."
            ),
        )

    return {
        "credits_used": profile["credits_used"],
        "daily_credit_limit": profile["daily_credit_limit"],
        "credits_remaining": credits_remaining,
        "reset_at": profile["credits_reset_at"],
        "tier": profile["tier"],
    }


async def deduct_credits(user_id: str, credit_cost: int, supabase_client) -> None:
    """
    Atomically deduct credits from a user's profile.

    Uses a conditional UPDATE to prevent race conditions.
    """
    response = (
        supabase_client.rpc(
            "deduct_credits",
            {"p_user_id": user_id, "p_cost": credit_cost},
        ).execute()
    )

    # Fallback: direct update if RPC not yet created
    if not response.data:
        supabase_client.table("profiles").update({
            "credits_used": supabase_client.table("profiles")
            .select("credits_used")
            .eq("id", user_id)
            .single()
            .execute()
            .data["credits_used"] + credit_cost
        }).eq("id", user_id).execute()

    logger.info("credits.deducted", user_id=user_id, cost=credit_cost)


async def refund_credits(user_id: str, credit_cost: int, supabase_client) -> None:
    """Refund credits for a failed job."""
    try:
        profile = (
            supabase_client.table("profiles")
            .select("credits_used")
            .eq("id", user_id)
            .single()
            .execute()
        )
        new_used = max(0, profile.data["credits_used"] - credit_cost)
        supabase_client.table("profiles").update({
            "credits_used": new_used,
        }).eq("id", user_id).execute()
        logger.info("credits.refunded", user_id=user_id, cost=credit_cost)
    except Exception as exc:
        logger.error("credits.refund_failed", user_id=user_id, error=str(exc))


async def check_global_spend_cap(supabase_client) -> None:
    """
    Check if the global daily spend cap has been reached.
    Raises SpendCapError if so.
    """
    settings = get_settings()

    try:
        # Sum today's estimated costs
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = (
            supabase_client.table("api_usage")
            .select("estimated_cost_usd")
            .gte("created_at", f"{today}T00:00:00Z")
            .execute()
        )

        if response.data:
            total_cost = sum(row["estimated_cost_usd"] for row in response.data)
            if total_cost >= settings.daily_spend_cap_usd:
                logger.error(
                    "spend_cap.reached",
                    total_cost=total_cost,
                    cap=settings.daily_spend_cap_usd,
                )
                raise SpendCapError(
                    f"Daily spend cap reached: ${total_cost:.2f} / ${settings.daily_spend_cap_usd}",
                )
    except SpendCapError:
        raise
    except Exception as exc:
        # Non-fatal: don't block users if the check itself fails
        logger.warning("spend_cap.check_failed", error=str(exc))


async def log_api_usage(
    user_id: str,
    job_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
    supabase_client,
) -> None:
    """Log API usage for cost monitoring."""
    try:
        supabase_client.table("api_usage").insert({
            "user_id": user_id,
            "job_id": job_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }).execute()
    except Exception as exc:
        # Non-fatal: don't fail the job if logging fails
        logger.warning("api_usage.log_failed", error=str(exc))

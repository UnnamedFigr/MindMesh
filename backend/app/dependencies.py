"""
FastAPI dependencies: authentication, rate limiting, credit checking.

These are injected via `Depends()` in route handlers.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.services.dev_store import is_dev_mode
from app.utils.errors import AuthError, RateLimitError

import structlog

logger = structlog.get_logger()


# ── In-memory rate limit state (fine for single-instance MVP) ──────────
_last_submission: dict[str, float] = defaultdict(float)  # user_id → timestamp
_active_jobs: dict[str, int] = defaultdict(int)  # user_id → count

# ── Dev mode user ──────────────────────────────────────────────────────
_DEV_USER = {
    "sub": "dev-user-001",
    "email": "dev@mindmesh.local",
    "role": "authenticated",
}


def _get_token(authorization: str = Header("")) -> str:
    """Extract the Bearer token from the Authorization header."""
    if not authorization.startswith("Bearer "):
        if is_dev_mode():
            return "dev-mode"
        raise AuthError(
            "Missing or malformed Authorization header",
            code="AUTH_ERROR",
            user_message="Please sign in to continue.",
        )
    return authorization[7:]


async def get_current_user(
    token: Annotated[str, Depends(_get_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """
    Verify Supabase JWT and return the user payload.

    In dev mode (placeholder Supabase keys), returns a dev user without JWT verification.
    Returns dict with at least: {"sub": "<user-id>", "email": "..."}
    """
    # Dev mode bypass — accept any token when Supabase keys are placeholders
    if is_dev_mode():
        logger.debug("auth.dev_mode_bypass", token_preview=token[:10])
        return _DEV_USER

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise AuthError(
            f"JWT verification failed: {exc}",
            code="AUTH_ERROR",
            user_message="Your session has expired. Please sign in again.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError(
            "JWT missing 'sub' claim",
            code="AUTH_ERROR",
            user_message="Invalid authentication token.",
        )

    return {
        "sub": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "authenticated"),
    }


async def check_rate_limit(
    user: Annotated[dict, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """
    Enforce per-user rate limits:
    - Max 1 concurrent job
    - Min 30s cooldown between submissions
    """
    user_id = user["sub"]
    now = time.time()

    # Check cooldown
    last = _last_submission.get(user_id, 0)
    elapsed = now - last
    if elapsed < settings.job_cooldown_seconds:
        remaining = int(settings.job_cooldown_seconds - elapsed)
        raise RateLimitError(
            f"Cooldown: {remaining}s remaining",
            code="RATE_LIMITED",
            user_message=f"Please wait {remaining} seconds before submitting another request.",
        )

    # Check concurrent jobs
    if _active_jobs.get(user_id, 0) >= settings.max_concurrent_jobs_per_user:
        raise RateLimitError(
            "Max concurrent jobs reached",
            code="CONCURRENT_LIMIT",
            user_message="You already have a guide being generated. Please wait for it to finish.",
        )

    return user


def mark_job_started(user_id: str) -> None:
    """Record that a user started a job (for rate limiting)."""
    _last_submission[user_id] = time.time()
    _active_jobs[user_id] = _active_jobs.get(user_id, 0) + 1


def mark_job_finished(user_id: str) -> None:
    """Record that a user's job finished (for rate limiting)."""
    _active_jobs[user_id] = max(0, _active_jobs.get(user_id, 0) - 1)

"""
Supabase client singleton.

Single point of access for the Supabase client across the entire backend.
- Production: returns a real supabase-py Client (service role, shared singleton).
- Dev mode:   returns the in-memory _DevStore that mirrors the supabase-py API.

Usage:
    from app.db import get_supabase

    supabase = get_supabase()
    supabase.table("profiles").select("*").eq("id", user_id).execute()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from supabase import Client

logger = structlog.get_logger()

# Module-level singleton — created once on first call, reused forever.
_client = None


def get_supabase():
    """
    Return the shared Supabase client (or dev store in dev mode).

    Thread-safe at module import level; FastAPI's single-process model
    means there are no concurrent initialisation races.
    """
    global _client
    if _client is not None:
        return _client

    from app.services.dev_store import get_dev_client, is_dev_mode

    if is_dev_mode():
        _client = get_dev_client()
        logger.info("db.using_dev_store")
        return _client

    from supabase import create_client

    from app.config import get_settings

    settings = get_settings()
    _client = create_client(settings.supabase_url, settings.supabase_service_key)
    logger.info("db.supabase_client_created", url=settings.supabase_url)
    return _client


def reset_client() -> None:
    """
    Reset the singleton — used in tests to swap between real/dev clients.
    Not needed in normal operation.
    """
    global _client
    _client = None

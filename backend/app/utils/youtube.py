"""
YouTube URL parsing, validation, and metadata utilities.

Handles all YouTube URL formats and validates videos via oEmbed (free, no API key).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from app.utils.errors import ValidationError

# Regex to extract 11-character YouTube video IDs from ALL known URL formats
_YOUTUBE_ID_PATTERN = re.compile(
    r"""(?x)
    (?:
        (?:https?://)?
        (?:www\.|m\.|music\.)?
        (?:
            youtube\.com/(?:watch\?.*?v=|embed/|v/|shorts/|live/)
            | youtu\.be/
        )
    )
    (?P<id>[\w-]{11})
    """
)

# Simpler fallback: just find an 11-char YouTube ID-looking string
_BARE_ID_PATTERN = re.compile(r"^[\w-]{11}$")

OEMBED_URL = "https://www.youtube.com/oembed"


@dataclass
class VideoMetadata:
    """Minimal video metadata from oEmbed."""

    youtube_id: str
    title: str
    channel_name: str
    thumbnail_url: str
    duration_seconds: int | None = None
    chapters: list[dict] | None = None


def extract_video_id(url: str) -> str:
    """
    Extract an 11-character YouTube video ID from any URL format.

    Supported formats:
    - youtube.com/watch?v=ID
    - youtu.be/ID
    - youtube.com/shorts/ID
    - youtube.com/embed/ID
    - youtube.com/v/ID
    - youtube.com/live/ID
    - m.youtube.com/...
    - music.youtube.com/...
    - With tracking params (&si=, &list=, &t=, &feature=)
    - Bare 11-char ID string

    Raises ValidationError if no valid ID is found.
    """
    url = url.strip()

    if not url:
        raise ValidationError(
            "Empty URL provided",
            code="INVALID_URL",
            user_message="Please enter a YouTube URL.",
        )

    # Try the full URL regex first
    match = _YOUTUBE_ID_PATTERN.search(url)
    if match:
        return match.group("id")

    # Try bare ID (user pasted just the video ID)
    if _BARE_ID_PATTERN.match(url):
        return url

    raise ValidationError(
        f"Could not extract YouTube video ID from: {url}",
        code="INVALID_URL",
        user_message="Please enter a valid YouTube URL.",
    )


async def validate_video(video_id: str) -> VideoMetadata:
    """
    Validate that a YouTube video exists and is accessible via oEmbed.

    oEmbed is FREE and requires NO API key.
    Returns title, author, thumbnail on success.
    Raises ValidationError on failure (private, deleted, age-restricted, etc.).
    """
    watch_url = f"https://www.youtube.com/watch?v={video_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                OEMBED_URL,
                params={"url": watch_url, "format": "json"},
            )
        except httpx.TimeoutException:
            raise ValidationError(
                "YouTube validation timed out",
                code="YOUTUBE_TIMEOUT",
                user_message="YouTube is taking too long to respond. Please try again.",
            )
        except httpx.HTTPError as exc:
            raise ValidationError(
                f"YouTube validation failed: {exc}",
                code="YOUTUBE_ERROR",
                user_message="Could not reach YouTube. Please try again.",
            )

    if response.status_code == 200:
        data = response.json()
        return VideoMetadata(
            youtube_id=video_id,
            title=data.get("title", "Unknown Title"),
            channel_name=data.get("author_name", "Unknown Channel"),
            thumbnail_url=data.get("thumbnail_url", ""),
        )
    elif response.status_code == 401:
        raise ValidationError(
            f"Video {video_id} is age-restricted or requires authentication",
            code="VIDEO_AGE_RESTRICTED",
            user_message="This video is age-restricted and we can't access its content.",
        )
    elif response.status_code == 404:
        raise ValidationError(
            f"Video {video_id} not found",
            code="VIDEO_NOT_FOUND",
            user_message="This video doesn't exist or has been deleted.",
        )
    else:
        raise ValidationError(
            f"Unexpected oEmbed response: {response.status_code}",
            code="VIDEO_VALIDATION_FAILED",
            user_message="Could not validate this video. Please try again.",
        )


def is_playlist_url(url: str) -> bool:
    """Check if the URL is a playlist-only URL (no video ID)."""
    return "list=" in url and "v=" not in url and "youtu.be/" not in url


async def extract_chapters(video_id: str) -> list[dict] | None:
    """
    Extract YouTube chapters (timestamps and titles) using yt-dlp.
    Returns:
        [{"title": "Intro", "start_time": 0.0, "end_time": 60.0}, ...]
    """
    try:
        import os
        import yt_dlp

        proxy_url = os.environ.get("YOUTUBE_PROXY_URL", "").strip() or None
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "dumpsubtitles": False,
        }
        if proxy_url:
            ydl_opts["proxy"] = proxy_url
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and "chapters" in info and info["chapters"]:
                chapters = []
                for chapter in info["chapters"]:
                    chapters.append({
                        "title": chapter.get("title", "Untitled Chapter"),
                        "start_time": chapter.get("start_time", 0.0),
                        "end_time": chapter.get("end_time", 0.0)
                    })
                return chapters if len(chapters) > 0 else None
                
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.warning("youtube.chapter_extraction_failed", error=str(e), video_id=video_id)
        # Silently fail if yt-dlp cannot extract chapters, the fallback is LLM generation
        pass
        
    return None

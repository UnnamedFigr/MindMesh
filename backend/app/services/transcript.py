"""
Transcript fetching service.

Priority waterfall:
1. Cache (Supabase videos table)
2. YouTube manual captions (free)
3. YouTube auto captions (free)
4. Groq Whisper v3 Turbo fallback ($0.04/hr)
"""

from __future__ import annotations

import html
import os
import tempfile
import unicodedata
from pathlib import Path

import httpx
import structlog
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.config import get_settings
from app.utils.errors import TranscriptError
from app.utils.tokens import count_tokens

logger = structlog.get_logger()


async def fetch_transcript(
    youtube_id: str,
    supabase_client,
) -> dict:
    """
    Fetch transcript using the priority waterfall.

    Returns:
        {
            "transcript_raw": str,           # Plain text transcript
            "transcript_timestamped": list,   # [{start, duration, text}, ...]
            "token_count": int,
            "language_detected": str,
            "transcript_source": str,         # "manual_caption" | "auto_caption" | "whisper"
        }
    """
    settings = get_settings()

    # ── Step 1: Check cache ──────────────────────────────────────
    cached = await _check_cache(youtube_id, supabase_client)
    if cached:
        logger.info("transcript.cache_hit", youtube_id=youtube_id)
        return cached

    # ── Step 2 & 3: YouTube captions ─────────────────────────────
    try:
        result = _fetch_youtube_captions(youtube_id)
        if result:
            logger.info(
                "transcript.youtube_success",
                youtube_id=youtube_id,
                source=result["transcript_source"],
            )
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except TranscriptError:
        raise
    except Exception as exc:
        logger.warning("transcript.youtube_failed", youtube_id=youtube_id, error=str(exc))

    # ── Step 4: Groq Whisper fallback ────────────────────────────
    try:
        result = await _transcribe_with_whisper(youtube_id, settings)
        if result:
            logger.info("transcript.whisper_success", youtube_id=youtube_id)
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except Exception as exc:
        logger.error("transcript.whisper_failed", youtube_id=youtube_id, error=str(exc))

    # ── Step 5: All failed ───────────────────────────────────────
    raise TranscriptError(
        f"All transcript methods failed for {youtube_id}",
        code="TRANSCRIPT_UNAVAILABLE",
        user_message=(
            "We couldn't extract a transcript from this video. "
            "It may be private, age-restricted, or lack spoken content."
        ),
    )


async def _check_cache(youtube_id: str, supabase_client) -> dict | None:
    """Check the videos table for a cached transcript."""
    try:
        response = (
            supabase_client.table("videos")
            .select("transcript_raw, transcript_timestamped, token_count, language_detected, transcript_source")
            .eq("youtube_id", youtube_id)
            .maybe_single()
            .execute()
        )
        if response.data and response.data.get("transcript_raw"):
            return response.data
    except Exception as exc:
        logger.warning("transcript.cache_check_failed", error=str(exc))
    return None


def _fetch_youtube_captions(youtube_id: str) -> dict | None:
    """
    Try to fetch captions via youtube-transcript-api.

    Attempts manual captions first, then auto-generated.
    """
    try:
        ytt_api = YouTubeTranscriptApi()

        # Try fetching transcript — library handles manual vs auto priority
        transcript = ytt_api.fetch(youtube_id, languages=["en", "en-US", "en-GB"])
        is_manual = not getattr(transcript, "is_generated", True)
        source = "manual_caption" if is_manual else "auto_caption"

        # Convert to our format
        segments = []
        raw_parts = []
        for snippet in transcript:
            text = _sanitize_text(snippet.text)
            segments.append({
                "start": snippet.start,
                "duration": snippet.duration,
                "text": text,
            })
            raw_parts.append(text)

        raw_text = " ".join(raw_parts)
        token_count = count_tokens(raw_text)

        return {
            "transcript_raw": raw_text,
            "transcript_timestamped": segments,
            "token_count": token_count,
            "language_detected": "en",
            "transcript_source": source,
        }

    except (NoTranscriptFound, TranscriptsDisabled):
        logger.info("transcript.no_captions", youtube_id=youtube_id)
        return None
    except VideoUnavailable:
        raise TranscriptError(
            f"Video {youtube_id} is unavailable",
            code="VIDEO_UNAVAILABLE",
            user_message="This video is unavailable. It may be private or deleted.",
        )
    except Exception as exc:
        logger.warning("transcript.youtube_error", youtube_id=youtube_id, error=str(exc))
        return None


async def _transcribe_with_whisper(youtube_id: str, settings) -> dict | None:
    """
    Download audio via yt-dlp and transcribe with Groq Whisper v3 Turbo.

    Handles chunking for files > 25MB.
    """
    groq_client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.mp3"

        # Download audio with yt-dlp
        try:
            import yt_dlp

            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": str(Path(tmpdir) / "audio.%(ext)s"),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "64",
                    }
                ],
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 60,
            }

            url = f"https://www.youtube.com/watch?v={youtube_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as exc:
            logger.error("transcript.yt_dlp_failed", youtube_id=youtube_id, error=str(exc))
            return None

        # Find the downloaded audio file
        audio_files = list(Path(tmpdir).glob("audio.*"))
        if not audio_files:
            logger.error("transcript.no_audio_file", youtube_id=youtube_id)
            return None
        audio_path = audio_files[0]

        # Check file size — chunk if > 25MB
        file_size = audio_path.stat().st_size
        if file_size > 25 * 1024 * 1024:
            return await _transcribe_chunked(audio_path, tmpdir, groq_client, settings)

        # Single-file transcription
        return _transcribe_single(audio_path, groq_client, settings)


def _transcribe_single(audio_path: Path, groq_client: OpenAI, settings) -> dict | None:
    """Transcribe a single audio file with Groq Whisper."""
    try:
        with open(audio_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=f,
                model=settings.whisper_model,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        raw_text = transcription.text
        segments = []
        if hasattr(transcription, "segments") and transcription.segments:
            for seg in transcription.segments:
                segments.append({
                    "start": seg.get("start", seg.start if hasattr(seg, "start") else 0),
                    "duration": (
                        seg.get("end", seg.end if hasattr(seg, "end") else 0)
                        - seg.get("start", seg.start if hasattr(seg, "start") else 0)
                    ),
                    "text": _sanitize_text(
                        seg.get("text", seg.text if hasattr(seg, "text") else "")
                    ),
                })

        token_count = count_tokens(raw_text)

        return {
            "transcript_raw": raw_text,
            "transcript_timestamped": segments,
            "token_count": token_count,
            "language_detected": getattr(transcription, "language", "en") or "en",
            "transcript_source": "whisper",
        }
    except Exception as exc:
        logger.error("transcript.whisper_single_failed", error=str(exc))
        return None


async def _transcribe_chunked(
    audio_path: Path, tmpdir: str, groq_client: OpenAI, settings
) -> dict | None:
    """
    Split audio into 10-minute chunks with ffmpeg, transcribe each, merge.
    """
    import subprocess

    chunk_dir = Path(tmpdir) / "chunks"
    chunk_dir.mkdir(exist_ok=True)

    # Split with ffmpeg — 10 minute segments
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(audio_path),
                "-f", "segment",
                "-segment_time", "600",
                "-c", "copy",
                str(chunk_dir / "chunk_%03d.mp3"),
            ],
            capture_output=True,
            check=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.error("transcript.ffmpeg_split_failed", error=str(exc))
        return None

    # Transcribe each chunk and merge
    all_text_parts: list[str] = []
    all_segments: list[dict] = []
    chunk_files = sorted(chunk_dir.glob("chunk_*.mp3"))
    time_offset = 0.0

    for chunk_file in chunk_files:
        result = _transcribe_single(chunk_file, groq_client, settings)
        if result:
            all_text_parts.append(result["transcript_raw"])
            # Offset timestamps
            for seg in result.get("transcript_timestamped", []):
                seg["start"] += time_offset
                all_segments.append(seg)
        # Each chunk is ~600s
        time_offset += 600.0

    if not all_text_parts:
        return None

    raw_text = " ".join(all_text_parts)
    token_count = count_tokens(raw_text)

    return {
        "transcript_raw": raw_text,
        "transcript_timestamped": all_segments,
        "token_count": token_count,
        "language_detected": "en",
        "transcript_source": "whisper",
    }


async def _store_cache(youtube_id: str, result: dict, supabase_client) -> None:
    """Store transcript in the videos table cache."""
    try:
        supabase_client.table("videos").upsert(
            {
                "youtube_id": youtube_id,
                "transcript_raw": result["transcript_raw"],
                "transcript_timestamped": result["transcript_timestamped"],
                "token_count": result["token_count"],
                "language_detected": result["language_detected"],
                "transcript_source": result["transcript_source"],
            },
            on_conflict="youtube_id",
        ).execute()
    except Exception as exc:
        # Cache failure is non-fatal
        logger.warning("transcript.cache_store_failed", error=str(exc))


def _sanitize_text(text: str) -> str:
    """Clean transcript text: decode HTML entities, normalize unicode, strip control chars."""
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    # Remove control characters except newlines and tabs
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
    return text.strip()

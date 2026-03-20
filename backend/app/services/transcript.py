"""
Transcript fetching service.

Priority waterfall:
1. Cache (Supabase videos table)
2. youtube-transcript-api  (with optional browser cookies)
3. yt-dlp subtitle download (with optional browser cookies — skips audio)
4. yt-dlp audio + Groq Whisper v3 Turbo ($0.04/hr — ultimate fallback)

Cloud IP note: YouTube blocks all clients from datacenter IPs without a
pro_token. Set YOUTUBE_COOKIES_B64 (base64 Netscape cookies.txt) in Render
to authenticate and bypass this restriction.
"""

from __future__ import annotations

import html
import json
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
try:
    from youtube_transcript_api._errors import RequestBlocked  # v0.6.x+
except ImportError:
    RequestBlocked = None  # older versions: treated as generic Exception

from app.config import get_settings
from app.utils.errors import TranscriptError
from app.utils.tokens import count_tokens
from app.utils.youtube import extract_chapters

logger = structlog.get_logger()

_COOKIE_FILE_PATH = Path(tempfile.gettempdir()) / "yt_cookies.txt"


def _get_cookie_file() -> str | None:
    """
    Decode YOUTUBE_COOKIES_B64 env var and write to a temp file.
    Returns the path if available, None otherwise.

    The env var must contain a base64-encoded Netscape cookies.txt file
    exported from a browser that has visited youtube.com.
    """
    import base64

    cookie_b64 = os.environ.get("YOUTUBE_COOKIES_B64", "").strip()
    if not cookie_b64:
        return None
    try:
        cookie_data = base64.b64decode(cookie_b64).decode("utf-8")
        _COOKIE_FILE_PATH.write_text(cookie_data, encoding="utf-8")
        return str(_COOKIE_FILE_PATH)
    except Exception as exc:
        logger.warning("transcript.cookie_file_error", error=str(exc))
        return None


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

    # ── Step 1: Check cache & fetch chapters ─────────────────────
    
    # Always try to fetch chapters fresh, even if transcript is cached
    chapters = await extract_chapters(youtube_id)
    
    cached = await _check_cache(youtube_id, supabase_client)
    if cached:
        logger.info("transcript.cache_hit", youtube_id=youtube_id)
        cached["chapters"] = chapters
        return cached

    # ── Step 2: youtube-transcript-api (works on residential/some cloud IPs) ──
    try:
        result = _fetch_youtube_captions(youtube_id)
        if result:
            logger.info(
                "transcript.youtube_success",
                youtube_id=youtube_id,
                source=result["transcript_source"],
            )
            result["chapters"] = chapters
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except TranscriptError:
        raise
    except Exception as exc:
        logger.warning("transcript.youtube_failed", youtube_id=youtube_id, error=str(exc))

    # ── Step 3: yt-dlp subtitle download (android_vr/ios bypass cloud blocks) ──
    try:
        result = await _fetch_captions_via_ytdlp(youtube_id)
        if result:
            logger.info("transcript.ytdlp_subtitles_success", youtube_id=youtube_id)
            result["chapters"] = chapters
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except TranscriptError:
        raise
    except Exception as exc:
        logger.warning("transcript.ytdlp_subtitles_failed", youtube_id=youtube_id, error=str(exc))

    # ── Step 4: yt-dlp audio + Whisper (ultimate fallback) ──────────────────
    try:
        result = await _transcribe_with_whisper(youtube_id, settings)
        if result:
            logger.info("transcript.whisper_success", youtube_id=youtube_id)
            result["chapters"] = chapters
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except Exception as exc:
        logger.error("transcript.whisper_failed", youtube_id=youtube_id, error=str(exc))

    # ── All failed ───────────────────────────────────────────────
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
    Falls back to any available language if English isn't found.
    """
    try:
        cookie_file = _get_cookie_file()
        ytt_api = YouTubeTranscriptApi(cookies=cookie_file) if cookie_file else YouTubeTranscriptApi()

        # Try English first; fall back to any available language
        try:
            transcript = ytt_api.fetch(youtube_id, languages=["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            # List all transcripts and pick the first available one
            try:
                transcript_list = ytt_api.list(youtube_id)
                available = list(transcript_list)
                if not available:
                    return None
                # Prefer manually created over auto-generated
                manual = [t for t in available if not getattr(t, "is_generated", True)]
                chosen = manual[0] if manual else available[0]
                transcript = chosen.fetch()
                logger.info(
                    "transcript.language_fallback",
                    youtube_id=youtube_id,
                    language=getattr(chosen, "language_code", "unknown"),
                )
            except Exception as list_exc:
                logger.warning(
                    "transcript.list_failed",
                    youtube_id=youtube_id,
                    error=str(list_exc),
                )
                return None

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

    except TranscriptsDisabled:
        logger.info("transcript.no_captions", youtube_id=youtube_id)
        return None
    except VideoUnavailable:
        raise TranscriptError(
            f"Video {youtube_id} is unavailable",
            code="VIDEO_UNAVAILABLE",
            user_message="This video is unavailable. It may be private or deleted.",
        )
    except Exception as exc:
        exc_type = type(exc).__name__
        # Detect IP/bot blocking — fall through to Whisper rather than aborting
        if RequestBlocked and isinstance(exc, RequestBlocked):
            logger.warning("transcript.ip_blocked", youtube_id=youtube_id)
        else:
            logger.warning(
                "transcript.youtube_error",
                youtube_id=youtube_id,
                error_type=exc_type,
                error=str(exc),
            )
        return None


async def _fetch_captions_via_ytdlp(youtube_id: str) -> dict | None:
    """
    Fetch captions via yt-dlp subtitle download — no audio download needed.

    Uses android_vr/ios player clients which bypass YouTube's cloud IP
    botguard that blocks the InnerTube caption API and web-based clients.
    """
    import yt_dlp

    with tempfile.TemporaryDirectory() as tmpdir:
        cookie_file = _get_cookie_file()
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "subtitlesformat": "json3",
            "outtmpl": str(Path(tmpdir) / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android_vr", "ios", "web"],
                }
            },
        }
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        url = f"https://www.youtube.com/watch?v={youtube_id}"
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as exc:
            logger.warning(
                "transcript.ytdlp_sub_download_failed",
                youtube_id=youtube_id,
                error=str(exc),
            )
            return None

        # yt-dlp names subtitle files as <video_id>.<lang>.json3
        sub_files = list(Path(tmpdir).glob(f"{youtube_id}.*.json3"))
        if not sub_files:
            logger.info("transcript.ytdlp_no_subtitles", youtube_id=youtube_id)
            return None

        sub_file = sorted(sub_files)[0]
        try:
            with open(sub_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        # Parse json3 subtitle format
        segments: list[dict] = []
        raw_parts: list[str] = []
        for event in data.get("events", []):
            if "segs" not in event:
                continue
            start_ms = event.get("tStartMs", 0)
            dur_ms = event.get("dDurationMs", 0)
            text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            text = _sanitize_text(text)
            if not text or text == "\n":
                continue
            segments.append({
                "start": start_ms / 1000,
                "duration": dur_ms / 1000,
                "text": text,
            })
            raw_parts.append(text)

        if not raw_parts:
            return None

        raw_text = " ".join(raw_parts)
        return {
            "transcript_raw": raw_text,
            "transcript_timestamped": segments,
            "token_count": count_tokens(raw_text),
            "language_detected": "en",
            "transcript_source": "auto_caption",
        }


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

            cookie_file = _get_cookie_file()
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
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android_vr", "ios", "web"],
                    }
                },
            }
            if cookie_file:
                ydl_opts["cookiefile"] = cookie_file

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

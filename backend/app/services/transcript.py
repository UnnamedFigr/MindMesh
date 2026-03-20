"""
Transcript fetching service.

Priority waterfall:
1. Cache (Supabase videos table)
2. youtube-transcript-api  (with session cookies + optional proxy)
3. yt-dlp subtitle download (with cookies/proxy — skips audio)
4. yt-dlp audio + Groq Whisper v3 Turbo ($0.04/hr — ultimate fallback)

Cloud IP note: YouTube blocks all clients from datacenter IPs without a
pro_token. Set YOUTUBE_COOKIES_B64 (base64 Netscape cookies.txt) in Render
to authenticate and bypass this restriction.  Alternatively set
YOUTUBE_PROXY_URL (e.g. http://user:pass@host:port) to route all YouTube
requests through a residential/rotating proxy.
"""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

import httpx
import structlog
from openai import OpenAI
from requests import Session as RequestsSession
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
try:
    from youtube_transcript_api._errors import RequestBlocked
except ImportError:
    RequestBlocked = None
try:
    from youtube_transcript_api.proxies import GenericProxyConfig
except ImportError:
    GenericProxyConfig = None  # older versions

from app.config import get_settings
from app.utils.errors import TranscriptError
from app.utils.tokens import count_tokens
from app.utils.youtube import extract_chapters

logger = structlog.get_logger()

# Invidious instances that have historically worked for caption fetching.
# The public Invidious ecosystem has shrunk significantly; instances are tried
# in order and failures are handled gracefully — this step is best-effort.
_INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yewtu.be",
]

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
        logger.info(
            "transcript.cookie_file_written",
            path=str(_COOKIE_FILE_PATH),
            size_bytes=len(cookie_data),
        )
        return str(_COOKIE_FILE_PATH)
    except Exception as exc:
        logger.warning("transcript.cookie_file_error", error=str(exc))
        return None


def _get_proxy_url() -> str | None:
    """Return YOUTUBE_PROXY_URL if set, else None."""
    return os.environ.get("YOUTUBE_PROXY_URL", "").strip() or None


def _build_ytt_session(cookie_file: str | None, proxy_url: str | None) -> RequestsSession:
    """
    Build a requests.Session for youtube-transcript-api with cookies and proxy.

    youtube-transcript-api v1.x removed the dedicated `cookies` parameter but
    accepts an `http_client` (requests.Session).  Loading cookies directly into
    the session re-enables cookie-based auth.
    """
    import http.cookiejar

    session = RequestsSession()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    if cookie_file:
        jar = http.cookiejar.MozillaCookieJar(cookie_file)
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            session.cookies.update(jar)  # type: ignore[arg-type]
            logger.info("transcript.cookies_loaded", count=len(jar))
        except Exception as exc:
            logger.warning("transcript.cookie_load_error", error=str(exc))

    if proxy_url:
        session.proxies = {"http": proxy_url, "https": proxy_url}

    return session


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
        # Only fetch chapters if they aren't already stored with the cache
        if not cached.get("chapters"):
            cached["chapters"] = await extract_chapters(youtube_id)
        return cached

    # ── Step 1b: Fetch chapters (runs only when not cached) ──────
    chapters = await extract_chapters(youtube_id)

    # ── Step 2: InnerTube direct API (bypasses watch page bot-detection) ──
    try:
        result = await _fetch_captions_via_innertube(youtube_id)
        if result:
            logger.info(
                "transcript.innertube_success",
                youtube_id=youtube_id,
                source=result["transcript_source"],
            )
            result["chapters"] = chapters
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except TranscriptError:
        raise
    except Exception as exc:
        logger.warning("transcript.innertube_failed", youtube_id=youtube_id, error=str(exc))

    # ── Step 3: youtube-transcript-api (works on residential/some cloud IPs) ──
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

    # ── Step 4: Invidious proxy (residential IPs, no bot-detection issues) ───
    try:
        result = await _fetch_captions_via_invidious(youtube_id)
        if result:
            logger.info("transcript.invidious_success", youtube_id=youtube_id)
            result["chapters"] = chapters
            await _store_cache(youtube_id, result, supabase_client)
            return result
    except TranscriptError:
        raise
    except Exception as exc:
        logger.warning("transcript.invidious_error", youtube_id=youtube_id, error=str(exc))

    # ── Step 5: yt-dlp subtitle download (with cookies if YOUTUBE_COOKIES_B64 set) ──
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

    # ── Step 6: yt-dlp audio + Whisper (ultimate fallback) ───────────────────
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
    has_cookies = bool(_get_cookie_file())
    has_proxy = bool(_get_proxy_url())
    cookie_hint = "" if has_cookies else " To fix this, set YOUTUBE_COOKIES_B64 (base64-encoded Netscape cookies.txt) in your environment."
    logger.error(
        "transcript.all_methods_failed",
        youtube_id=youtube_id,
        cookies_configured=has_cookies,
        proxy_configured=has_proxy,
    )
    raise TranscriptError(
        f"All transcript methods failed for {youtube_id}.{cookie_hint}",
        code="TRANSCRIPT_UNAVAILABLE",
        user_message=(
            "We couldn't extract a transcript from this video. "
            "It may be private, age-restricted, or YouTube is blocking automated access. "
            "If this keeps happening, contact support."
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


# ── InnerTube direct API ─────────────────────────────────────────────────────
# YouTube's InnerTube API serves video metadata (including caption track URLs)
# without requiring a watch-page HTML fetch.  The watch page is where YouTube's
# bot-detection fires; calling InnerTube directly with mobile client contexts
# (ANDROID, IOS) often bypasses datacenter IP blocking entirely.
#
# API keys below are PUBLIC keys embedded in YouTube's own client code.

_INNERTUBE_CLIENTS = [
    {
        "name": "ANDROID",
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.09.37",
                "androidSdkVersion": 30,
                "hl": "en",
                "gl": "US",
            }
        },
        "key": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
        "ua": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
    },
    {
        "name": "IOS",
        "context": {
            "client": {
                "clientName": "IOS",
                "clientVersion": "19.09.3",
                "deviceModel": "iPhone14,3",
                "hl": "en",
                "gl": "US",
            }
        },
        "key": "AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUAc",
        "ua": "com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)",
    },
    {
        "name": "WEB",
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240313.01.00",
                "hl": "en",
                "gl": "US",
            }
        },
        "key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    },
]


async def _fetch_captions_via_innertube(youtube_id: str) -> dict | None:
    """
    Fetch captions by calling YouTube's InnerTube player API directly.

    This bypasses the watch-page HTML fetch that triggers bot-detection.
    Tries ANDROID → IOS → WEB client contexts which have different bot-
    detection thresholds.  Caption content is fetched in json3 format from
    the track URL returned by InnerTube.
    """
    for client in _INNERTUBE_CLIENTS:
        try:
            async with httpx.AsyncClient(timeout=15.0) as http:
                resp = await http.post(
                    "https://www.youtube.com/youtubei/v1/player",
                    params={"key": client["key"], "prettyPrint": "false"},
                    json={
                        "context": client["context"],
                        "videoId": youtube_id,
                    },
                    headers={
                        "User-Agent": client["ua"],
                        "Content-Type": "application/json",
                        "X-Goog-Api-Format-Version": "2",
                    },
                )

                if resp.status_code != 200:
                    logger.debug(
                        "transcript.innertube_http_error",
                        client=client["name"],
                        status=resp.status_code,
                    )
                    continue

                data = resp.json()

                # Check playability
                ps = data.get("playabilityStatus", {})
                status = ps.get("status")
                if status != "OK":
                    reason = ps.get("reason", "")
                    logger.debug(
                        "transcript.innertube_not_playable",
                        client=client["name"],
                        status=status,
                        reason=reason[:120],
                    )
                    if "Sign in" in reason or status == "LOGIN_REQUIRED":
                        continue  # try next client
                    if status in ("ERROR", "UNPLAYABLE"):
                        return None  # video genuinely unavailable
                    continue

                # Extract caption tracks
                captions_renderer = (
                    data.get("captions", {})
                    .get("playerCaptionsTracklistRenderer", {})
                )
                tracks = captions_renderer.get("captionTracks", [])

                if not tracks:
                    logger.info(
                        "transcript.innertube_no_captions",
                        youtube_id=youtube_id,
                        client=client["name"],
                    )
                    return None  # video has no captions at all

                # Pick best track: English manual > English auto > anything
                track = (
                    next(
                        (t for t in tracks
                         if t.get("languageCode", "").startswith("en")
                         and t.get("kind") != "asr"),
                        None,
                    )
                    or next(
                        (t for t in tracks
                         if t.get("languageCode", "").startswith("en")),
                        None,
                    )
                    or tracks[0]
                )

                base_url = track.get("baseUrl", "")
                if not base_url:
                    continue

                is_manual = track.get("kind") != "asr"
                lang = track.get("languageCode", "en")

                # Fetch caption content in json3 format
                sep = "&" if "?" in base_url else "?"
                caption_url = f"{base_url}{sep}fmt=json3"

                caption_resp = await http.get(
                    caption_url,
                    headers={"User-Agent": client["ua"]},
                )
                if caption_resp.status_code != 200:
                    logger.debug(
                        "transcript.innertube_caption_fetch_error",
                        client=client["name"],
                        status=caption_resp.status_code,
                    )
                    continue

                # Parse json3 format
                caption_data = caption_resp.json()
                segments: list[dict] = []
                raw_parts: list[str] = []

                for event in caption_data.get("events", []):
                    if "segs" not in event:
                        continue
                    start_ms = event.get("tStartMs", 0)
                    dur_ms = event.get("dDurationMs", 0)
                    text = "".join(
                        seg.get("utf8", "") for seg in event["segs"]
                    ).strip()
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
                    continue

                raw_text = " ".join(raw_parts)
                source = "manual_caption" if is_manual else "auto_caption"

                logger.info(
                    "transcript.innertube_caption_success",
                    youtube_id=youtube_id,
                    client=client["name"],
                    language=lang,
                    source=source,
                    segments=len(segments),
                )

                return {
                    "transcript_raw": raw_text,
                    "transcript_timestamped": segments,
                    "token_count": count_tokens(raw_text),
                    "language_detected": lang,
                    "transcript_source": source,
                }

        except Exception as exc:
            logger.warning(
                "transcript.innertube_client_error",
                client=client["name"],
                youtube_id=youtube_id,
                error=str(exc),
            )
            continue

    logger.warning("transcript.innertube_all_failed", youtube_id=youtube_id)
    return None


def _fetch_youtube_captions(youtube_id: str) -> dict | None:
    """
    Try to fetch captions via youtube-transcript-api.

    Attempts manual captions first, then auto-generated.
    Falls back to any available language if English isn't found.
    """
    try:
        cookie_file = _get_cookie_file()
        proxy_url = _get_proxy_url()
        session = _build_ytt_session(cookie_file, proxy_url)

        # Build proxy_config for v1.x (optional — also handled via session.proxies)
        proxy_config = None
        if proxy_url and GenericProxyConfig is not None:
            proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

        ytt_api = YouTubeTranscriptApi(http_client=session, proxy_config=proxy_config)

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


async def _fetch_captions_via_invidious(youtube_id: str) -> dict | None:
    """
    Fetch captions via public Invidious instances (best-effort).

    Invidious is an open-source YouTube front-end that proxies requests through
    its own servers, potentially bypassing YouTube's datacenter IP blocking.
    NOTE: the public Invidious ecosystem has shrunk significantly; most instances
    are either behind bot-guards or offline.  This step fails gracefully.
    """
    _browser_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    _headers = {
        "User-Agent": _browser_ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for instance in _INVIDIOUS_INSTANCES:
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                # Step 1: get caption track list for this video
                list_resp = await client.get(
                    f"{instance}/api/v1/captions/{youtube_id}",
                    headers=_headers,
                )
                # Reject non-200 or bot-gate HTML responses
                if list_resp.status_code != 200:
                    logger.debug(
                        "transcript.invidious_list_error",
                        instance=instance,
                        status=list_resp.status_code,
                    )
                    continue
                if "text/html" in list_resp.headers.get("content-type", ""):
                    logger.debug(
                        "transcript.invidious_bot_gate",
                        instance=instance,
                    )
                    continue

                data = list_resp.json()
                captions = data.get("captions", [])
                if not captions:
                    # Reached Invidious successfully — video just has no captions
                    logger.info(
                        "transcript.invidious_no_captions",
                        youtube_id=youtube_id,
                        instance=instance,
                    )
                    return None  # No point trying other instances

                # Prefer English; fall back to first available language
                caption = next(
                    (c for c in captions if c.get("languageCode", "").startswith("en")),
                    captions[0],
                )

                # Step 2: fetch the caption content (WebVTT) via the url field
                caption_url = caption.get("url", "")
                if not caption_url:
                    caption_url = f"/api/v1/captions/{youtube_id}?label={caption.get('label', '')}"
                if caption_url.startswith("/"):
                    caption_url = f"{instance}{caption_url}"

                vtt_resp = await client.get(caption_url, headers=_headers)
                if vtt_resp.status_code != 200:
                    continue

                segments, raw_parts = _parse_vtt(vtt_resp.text)
                if not raw_parts:
                    continue

                raw_text = " ".join(raw_parts)
                logger.info(
                    "transcript.invidious_fetched",
                    youtube_id=youtube_id,
                    instance=instance,
                    language=caption.get("languageCode", "en"),
                )
                return {
                    "transcript_raw": raw_text,
                    "transcript_timestamped": segments,
                    "token_count": count_tokens(raw_text),
                    "language_detected": caption.get("languageCode", "en"),
                    "transcript_source": "auto_caption",
                }

        except Exception as exc:
            logger.warning(
                "transcript.invidious_instance_error",
                instance=instance,
                youtube_id=youtube_id,
                error=str(exc),
            )
            continue

    logger.warning("transcript.invidious_all_failed", youtube_id=youtube_id)
    return None


def _parse_vtt(vtt_text: str) -> tuple[list[dict], list[str]]:
    """Parse WebVTT subtitle text into timestamped segments."""
    segments: list[dict] = []
    raw_parts: list[str] = []
    lines = vtt_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(
            r"(\d{1,2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[.,]\d{3})",
            line,
        )
        if m:
            start = _vtt_time_to_seconds(m.group(1))
            end = _vtt_time_to_seconds(m.group(2))
            i += 1
            text_lines: list[str] = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            raw = " ".join(text_lines)
            raw = re.sub(r"<[^>]+>", "", raw).strip()  # strip inline VTT tags
            text = _sanitize_text(raw)
            if text:
                segments.append({
                    "start": start,
                    "duration": max(0.0, end - start),
                    "text": text,
                })
                raw_parts.append(text)
        else:
            i += 1
    return segments, raw_parts


def _vtt_time_to_seconds(time_str: str) -> float:
    """Convert VTT timestamp (HH:MM:SS.mmm or HH:MM:SS,mmm) to seconds."""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


async def _fetch_captions_via_ytdlp(youtube_id: str) -> dict | None:
    """
    Fetch captions via yt-dlp subtitle download — no audio download needed.

    Uses android_vr/ios player clients which bypass YouTube's cloud IP
    botguard that blocks the InnerTube caption API and web-based clients.
    """
    import yt_dlp

    with tempfile.TemporaryDirectory() as tmpdir:
        cookie_file = _get_cookie_file()
        proxy_url = _get_proxy_url()
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
        if proxy_url:
            ydl_opts["proxy"] = proxy_url

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
            proxy_url = _get_proxy_url()
            ydl_opts = {
                "format": "bestaudio/best",
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
            if proxy_url:
                ydl_opts["proxy"] = proxy_url

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

"""
Content triage service.

Uses llama-3.1-8b-instant to classify whether a transcript is educational.
Fast (~1s) and cheap (~$0.001 per classification).
"""

from __future__ import annotations

import asyncio
import json

import structlog
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompts.schemas import TriageResult
from app.utils.errors import GenerationError, TriageError
from app.utils.tokens import truncate_to_tokens

logger = structlog.get_logger()

TRIAGE_SYSTEM_PROMPT = """You are a content classifier for MindMesh, an educational study guide platform.

Given the first portion of a video transcript, determine:
1. Is this content educational? (Educational = ANY content that teaches, explains, demonstrates, or informs. This includes: lectures, tutorials, how-to videos, documentaries, educational podcasts, interviews with experts, workshop recordings, coding tutorials, cooking lessons, DIY guides, science explainers, etc.)
2. What type of content is it?
3. What language is it in?
4. What's the primary topic?
5. What's the estimated complexity level?

Be GENEROUS with the educational classification — when in doubt, classify as educational. Only classify as non-educational if the content is clearly entertainment-only (music videos, comedy skits, vlogs without informational content, etc.).

You MUST respond with ONLY a valid JSON object matching this schema:
{
  "is_educational": true/false,
  "confidence": 0.0 to 1.0,
  "content_type": "lecture|tutorial|podcast|interview|documentary|workshop|entertainment|music|other",
  "language": "ISO 639-1 code like 'en' or 'es'",
  "primary_topic": "Brief 1-sentence topic summary",
  "estimated_complexity": "beginner|intermediate|advanced",
  "reason": "One-sentence explanation of the classification"
}"""


async def triage_content(
    transcript_raw: str,
    openai_client: OpenAI,
) -> TriageResult:
    """
    Classify transcript content using llama-3.1-8b-instant.

    Sends the first ~2000 tokens for classification.
    Returns TriageResult with classification details.
    Raises TriageError if content is not educational.
    """
    settings = get_settings()

    # Use first 2000 tokens for triage (cheap and fast)
    sample = truncate_to_tokens(transcript_raw, 2000)

    # Additional signal: unique word count
    unique_words = len(set(sample.lower().split()))
    if unique_words < 50:
        raise TriageError(
            "Transcript has very few unique words — likely music or silence",
            code="LOW_CONTENT",
            user_message=(
                "This video appears to have very little spoken content. "
                "MindMesh works best with videos that have substantive narration."
            ),
        )

    try:
        result = await _call_triage(sample, openai_client, settings)
    except GenerationError:
        raise
    except Exception as exc:
        logger.error("triage.unexpected_error", error=str(exc))
        # On triage failure, be lenient — let users through
        return TriageResult(
            is_educational=True,
            confidence=0.5,
            content_type="other",
            language="en",
            primary_topic="Could not determine",
            estimated_complexity="intermediate",
            reason="Triage service encountered an error; proceeding with generation.",
        )

    # Decision logic
    if not result.is_educational and result.confidence >= 0.7:
        raise TriageError(
            f"Content classified as non-educational ({result.content_type}): {result.reason}",
            code="NOT_EDUCATIONAL",
            user_message=(
                f"This content appears to be {result.content_type} rather than educational. "
                "MindMesh works best with lectures, tutorials, and informational videos."
            ),
        )

    if result.is_educational and result.confidence < 0.4:
        logger.warning(
            "triage.low_confidence",
            confidence=result.confidence,
            content_type=result.content_type,
        )

    logger.info(
        "triage.result",
        is_educational=result.is_educational,
        confidence=result.confidence,
        content_type=result.content_type,
        language=result.language,
        topic=result.primary_topic,
    )

    return result


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_triage(
    sample: str,
    openai_client: OpenAI,
    settings,
) -> TriageResult:
    """Call LLM for content triage with JSON mode and retry logic."""
    try:
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=settings.triage_model,
            messages=[
                {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this transcript:\n\n{sample}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
        )

        raw_text = response.choices[0].message.content
        if not raw_text:
            raise GenerationError(
                "Triage returned empty response",
                code="TRIAGE_PARSE_ERROR",
                user_message="Content classification failed. Please try again.",
            )

        data = json.loads(raw_text)
        return TriageResult(**data)

    except (GenerationError, TriageError):
        raise
    except json.JSONDecodeError as exc:
        logger.error("triage.json_parse_error", error=str(exc), raw=raw_text[:200])
        raise GenerationError(
            f"Triage JSON parse failed: {exc}",
            code="TRIAGE_PARSE_ERROR",
            user_message="Content classification failed. Please try again.",
        )
    except Exception as exc:
        logger.error("triage.api_error", error=str(exc))
        raise GenerationError(
            f"Triage API call failed: {exc}",
            code="TRIAGE_API_ERROR",
            user_message="Our AI is experiencing issues. Please try again in a few minutes.",
        )

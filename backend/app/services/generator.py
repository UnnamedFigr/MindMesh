"""
Study guide generator service.

Orchestrates prompt assembly, model routing, and output rendering.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import structlog
from pydantic import ValidationError as PydanticValidationError
from jinja2 import Environment, FileSystemLoader
from openai import APIConnectionError, APITimeoutError, BadRequestError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompts.schemas import StudyGuideCore, StudyGuidePro
from app.utils.errors import GenerationError, ValidationError
from app.utils.tokens import chunk_transcript, count_tokens, get_processing_strategy, truncate_to_tokens

logger = structlog.get_logger()

# Load Jinja2 templates
_TEMPLATES_DIR = Path(__file__).parent.parent / "prompts" / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=False,
)


def _get_persona_instructions(persona: str) -> str:
    """Load persona-specific prompt instructions."""
    template = _jinja_env.get_template(f"persona_{persona}.j2")
    return template.render()


def _get_system_prompt() -> str:
    """Load the core system prompt."""
    template = _jinja_env.get_template("system_core.j2")
    return template.render()


def _build_user_prompt(
    transcript: str,
    persona: str,
    tier: str,
    video_title: str = "",
    channel_name: str = "",
    duration_seconds: int | None = None,
) -> str:
    """Assemble the full user prompt from templates."""
    persona_instructions = _get_persona_instructions(persona)

    duration_display = None
    if duration_seconds:
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_display = f"{minutes}m {seconds}s"

    template = _jinja_env.get_template("guide_generation.j2")
    return template.render(
        transcript=transcript,
        persona_instructions=persona_instructions,
        tier=tier,
        video_title=video_title or "Unknown",
        channel_name=channel_name or "Unknown",
        duration_display=duration_display,
    )


async def generate_study_guide(
    transcript_raw: str,
    token_count: int,
    persona: str,
    tier: str,
    openai_client: OpenAI,
    video_title: str = "",
    channel_name: str = "",
    duration_seconds: int | None = None,
    model_name: str | None = None,
) -> dict:
    """
    Generate a study guide from a transcript.

    Routes to single-pass or chunk-and-merge based on token count.
    Uses model_name to decide which LLM model to call.

    Returns:
        {
            "content_json": dict,        # Parsed study guide as dict
            "content_markdown": str,     # Rendered Markdown
            "input_tokens": int,
            "output_tokens": int,
        }
    """
    settings = get_settings()
    if not model_name:
        model_name = settings.guide_model
    strategy = get_processing_strategy(token_count)

    if strategy == "reject":
        raise ValidationError(
            f"Transcript too long: {token_count} tokens",
            code="VIDEO_TOO_LONG",
            user_message="This video exceeds our processing limit (~4 hours). Try a shorter one.",
        )

    logger.info(
        "generator.start",
        strategy=strategy,
        token_count=token_count,
        persona=persona,
        tier=tier,
        model=model_name,
    )

    # Truncate transcript if it would overflow the model's context window.
    # Groq llama-3.3-70b-versatile has 128K context → keep ~90K for transcript.
    # OpenAI GPT-4.1 has 1M context → keep ~200K (plenty for any video).
    is_openai_model = model_name.startswith("gpt-")
    max_transcript_tokens = 200_000 if is_openai_model else 90_000
    if token_count > max_transcript_tokens:
        logger.info("generator.truncating", original=token_count, limit=max_transcript_tokens)
        transcript_raw = truncate_to_tokens(transcript_raw, max_transcript_tokens)
        token_count = max_transcript_tokens

    if strategy == "single_pass":
        return await _single_pass(
            transcript_raw, persona, tier, openai_client, settings,
            video_title, channel_name, duration_seconds, model_name,
        )
    else:
        return await _chunk_and_merge(
            transcript_raw, persona, tier, openai_client, settings,
            video_title, channel_name, duration_seconds, model_name,
        )


async def _single_pass(
    transcript: str,
    persona: str,
    tier: str,
    openai_client: OpenAI,
    settings,
    video_title: str,
    channel_name: str,
    duration_seconds: int | None,
    model_name: str | None = None,
) -> dict:
    """Single-pass generation for transcripts ≤100K tokens (95%+ of videos)."""
    system_prompt = _get_system_prompt()
    user_prompt = _build_user_prompt(
        transcript, persona, tier, video_title, channel_name, duration_seconds,
    )

    # Choose output schema based on tier
    output_model = StudyGuidePro if tier == "pro" else StudyGuideCore

    result = await _call_generation(
        system_prompt, user_prompt, output_model, openai_client, settings,
        model_name=model_name,
    )

    content_json = result["parsed"].model_dump()
    content_markdown = render_guide_markdown(content_json, tier)

    return {
        "content_json": content_json,
        "content_markdown": content_markdown,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }


async def _chunk_and_merge(
    transcript: str,
    persona: str,
    tier: str,
    openai_client: OpenAI,
    settings,
    video_title: str,
    channel_name: str,
    duration_seconds: int | None,
    model_name: str | None = None,
) -> dict:
    """
    Chunk-and-merge pipeline for transcripts >100K tokens.

    Phase 1: Extract key concepts from each chunk (MAP)
    Phase 2: Merge extractions into unified study guide (REDUCE)
    """
    chunks = chunk_transcript(transcript, max_tokens_per_chunk=12_000)
    total_input = 0
    total_output = 0

    # MAP phase: extract key information from each chunk
    extractions = []
    for i, chunk in enumerate(chunks):
        context = f"[Segment {i + 1}/{len(chunks)}]"
        map_prompt = (
            f"Extract the key concepts, mechanics, examples, and notable quotes "
            f"from this transcript segment. Include timestamps where available.\n\n"
            f"{context}\n\n{chunk}"
        )
        try:
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model=model_name or settings.guide_model,
                messages=[
                    {"role": "system", "content": _get_system_prompt()},
                    {"role": "user", "content": map_prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            extractions.append(response.choices[0].message.content)
            total_input += response.usage.prompt_tokens if response.usage else 0
            total_output += response.usage.completion_tokens if response.usage else 0
        except Exception as exc:
            logger.warning("generator.chunk_map_failed", chunk=i, error=str(exc))
            extractions.append(f"[Segment {i + 1}: extraction failed]")

    # REDUCE phase: merge into unified study guide
    merged_extractions = "\n\n---\n\n".join(extractions)
    persona_instructions = _get_persona_instructions(persona)
    reduce_prompt = (
        f"Below are extracted key concepts and information from a long video, "
        f"broken into segments. Merge them into a single, coherent study guide.\n\n"
        f"VIDEO TITLE: {video_title}\n"
        f"CHANNEL: {channel_name}\n\n"
        f"{persona_instructions}\n\n"
        f"EXTRACTED SEGMENTS:\n{merged_extractions}"
    )

    output_model = StudyGuidePro if tier == "pro" else StudyGuideCore
    result = await _call_generation(
        _get_system_prompt(), reduce_prompt, output_model, openai_client, settings,
        model_name=model_name,
    )
    total_input += result["input_tokens"]
    total_output += result["output_tokens"]

    content_json = result["parsed"].model_dump()
    content_markdown = render_guide_markdown(content_json, tier)

    return {
        "content_json": content_json,
        "content_markdown": content_markdown,
        "input_tokens": total_input,
        "output_tokens": total_output,
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_generation(
    system_prompt: str,
    user_prompt: str,
    output_model,
    openai_client: OpenAI,
    settings,
    *,
    model_name: str | None = None,
) -> dict:
    """Call LLM with JSON mode and retry logic."""
    resolved_model = model_name or settings.guide_model
    try:
        # Build JSON schema instruction from the Pydantic model
        schema_json = json.dumps(output_model.model_json_schema(), indent=2)
        schema_instruction = (
            f"\n\nYou MUST respond with ONLY a valid JSON object that conforms to this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do NOT include any text before or after the JSON. Only valid JSON."
        )

        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=resolved_model,
            messages=[
                {"role": "system", "content": system_prompt + schema_instruction},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=8192,
        )

        raw_text = response.choices[0].message.content
        if not raw_text:
            raise GenerationError(
                "Generation returned empty response",
                code="GENERATION_PARSE_ERROR",
            )

        data = json.loads(raw_text)
        parsed = output_model(**data)

        return {
            "parsed": parsed,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

    except GenerationError:
        raise
    except PydanticValidationError as exc:
        logger.warning("generator.schema_validation_error", error=str(exc), error_count=exc.error_count())
        raise GenerationError(
            f"AI output did not match expected format: {exc}",
            code="GENERATION_VALIDATION_ERROR",
            user_message="The AI produced an unexpected format. Please try again.",
        )
    except json.JSONDecodeError as exc:
        logger.error("generator.json_parse_error", error=str(exc))
        raise GenerationError(
            f"Study guide JSON parse failed: {exc}",
            code="GENERATION_PARSE_ERROR",
            user_message="Failed to parse the generated study guide. Please try again.",
        )
    except RateLimitError as exc:
        logger.warning("generator.rate_limit", error=str(exc), status=exc.status_code)
        raise GenerationError(
            f"Rate limit hit: {exc}",
            code="GENERATION_RATE_LIMIT",
            user_message="AI rate limit reached. Please wait a minute and try again.",
        )
    except BadRequestError as exc:
        logger.error("generator.bad_request", error=str(exc), status=exc.status_code)
        msg = str(exc).lower()
        if "context" in msg or "token" in msg or "too large" in msg or "maximum" in msg:
            user_msg = "This video's transcript is too large for our AI model. Try a shorter video."
        else:
            user_msg = f"AI rejected the request: {exc.message if hasattr(exc, 'message') else exc}"
        raise GenerationError(
            f"Bad request: {exc}",
            code="GENERATION_BAD_REQUEST",
            user_message=user_msg,
        )
    except APITimeoutError as exc:
        logger.warning("generator.timeout", error=str(exc))
        raise GenerationError(
            f"API timeout: {exc}",
            code="GENERATION_TIMEOUT",
            user_message="AI request timed out. The video may be too long — please try again or use a shorter video.",
        )
    except APIConnectionError as exc:
        logger.error("generator.connection_error", error=str(exc))
        raise GenerationError(
            f"Connection error: {exc}",
            code="GENERATION_CONNECTION_ERROR",
            user_message="Could not connect to AI service. Please check your connection and try again.",
        )
    except Exception as exc:
        logger.error("generator.api_error", error=str(exc), error_type=type(exc).__name__)
        raise GenerationError(
            f"Study guide generation failed: {exc}",
            code="GENERATION_API_ERROR",
            user_message="Our AI is experiencing issues. Please try again in a few minutes.",
        )


def render_guide_markdown(content_json: dict, tier: str) -> str:
    """
    Render study guide JSON into beautiful Markdown.

    We control the formatting ourselves rather than trusting GPT to format.
    """
    md_parts: list[str] = []
    brief = content_json.get("quick_brief", {})

    # ── Quick Brief ──────────────────────────────────────────
    md_parts.append("# 📋 Quick Brief\n")

    # Clickbait score
    cb = brief.get("clickbait_score", {})
    if cb:
        score = cb.get("score", "?")
        verdict = cb.get("verdict", "")
        md_parts.append(f"**🎯 Clickbait Score:** {score}/10 — {verdict}\n")

    # Time saved
    time_saved = brief.get("time_saved_minutes", 0)
    if time_saved:
        md_parts.append(f"**⏱️ Time Saved:** ~{time_saved} minutes\n")

    # Hook
    hook = brief.get("hook", "")
    if hook:
        md_parts.append(f"**💡 In a Nutshell:** {hook}\n")

    # Key takeaways
    takeaways = brief.get("key_takeaways", [])
    if takeaways:
        md_parts.append("\n### Key Takeaways\n")
        for t in takeaways:
            md_parts.append(f"- {t}")
        md_parts.append("")

    # Highlight quote
    quote = brief.get("highlight_quote", "")
    quote_ts = brief.get("highlight_quote_timestamp", "")
    if quote:
        md_parts.append(f'\n> "{quote}"')
        if quote_ts:
            md_parts.append(f"> — *at {quote_ts}*\n")

    # ── Themes ───────────────────────────────────────────────
    themes = content_json.get("themes", [])
    if themes:
        md_parts.append("\n---\n\n# 📚 Themes\n")
        for theme in themes:
            num = theme.get("theme_number", "")
            title = theme.get("title", "Untitled")
            time_range = theme.get("time_range", "")
            md_parts.append(f"\n## Theme {num}: {title}")
            if time_range:
                md_parts.append(f"*⏰ {time_range}*\n")

            core = theme.get("core_concept", "")
            if core:
                md_parts.append(f"{core}\n")

            mechanics = theme.get("mechanics", [])
            if mechanics:
                md_parts.append("**How it works:**")
                for m in mechanics:
                    md_parts.append(f"- {m}")
                md_parts.append("")

            analogy = theme.get("analogy_or_example", "")
            if analogy:
                md_parts.append(f"💡 **Example:** {analogy}\n")

    # ── Pro: Quiz ────────────────────────────────────────────
    quiz = content_json.get("quiz", [])
    if quiz and tier == "pro":
        md_parts.append("\n---\n\n# 🧠 Active Recall Quiz\n")
        for i, q in enumerate(quiz, 1):
            md_parts.append(f"\n**Question {i}:** {q.get('question', '')}\n")
            options = q.get("options", [])
            for j, opt in enumerate(options):
                letter = chr(65 + j)  # A, B, C, D
                md_parts.append(f"- **{letter}.** {opt}")
            correct = q.get("correct_index", 0)
            md_parts.append(
                f"\n<details><summary>Show Answer</summary>\n\n"
                f"**{chr(65 + correct)}.** {options[correct] if correct < len(options) else '?'}\n\n"
                f"*{q.get('explanation', '')}*\n"
                f"📍 *See: {q.get('timestamp', '')}*\n\n"
                f"</details>\n"
            )

    # ── Pro: Reflection ──────────────────────────────────────
    reflection = content_json.get("reflection_question", "")
    if reflection and tier == "pro":
        md_parts.append("\n---\n\n# 🪞 Reflection\n")
        md_parts.append(f"*{reflection}*\n")

    return "\n".join(md_parts)

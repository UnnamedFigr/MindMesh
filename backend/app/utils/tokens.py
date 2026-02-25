"""
Token counting and chunking utilities.

Uses tiktoken for accurate GPT token counts.
Provides chunking strategy for very long transcripts (>100K tokens).
"""

from __future__ import annotations

import tiktoken

# cl100k_base is used by GPT-4, GPT-4o, GPT-4.1 family
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count the number of tokens in a string using cl100k_base encoding."""
    return len(_ENCODING.encode(text))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to fit within max_tokens."""
    tokens = _ENCODING.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _ENCODING.decode(tokens[:max_tokens])


def chunk_transcript(
    text: str,
    max_tokens_per_chunk: int = 12_000,
    overlap_tokens: int = 200,
) -> list[str]:
    """
    Split a transcript into overlapping chunks for the map-reduce pipeline.

    Args:
        text: The full transcript text.
        max_tokens_per_chunk: Maximum tokens per chunk (default 12K).
        overlap_tokens: Overlap between chunks for context continuity.

    Returns:
        List of text chunks, each within max_tokens_per_chunk.
    """
    tokens = _ENCODING.encode(text)
    total = len(tokens)

    if total <= max_tokens_per_chunk:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max_tokens_per_chunk - overlap_tokens

    while start < total:
        end = min(start + max_tokens_per_chunk, total)
        chunk_tokens = tokens[start:end]
        chunks.append(_ENCODING.decode(chunk_tokens))
        start += step

    return chunks


def get_processing_strategy(token_count: int) -> str:
    """
    Determine the processing strategy based on token count.

    Returns:
        "single_pass" for ≤120K tokens (95%+ of videos)
        "chunk_and_merge" for 120K–500K tokens
        "reject" for >500K tokens
    """
    if token_count <= 120_000:
        return "single_pass"
    elif token_count <= 500_000:
        return "chunk_and_merge"
    else:
        return "reject"

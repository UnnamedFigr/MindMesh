"""
Tests for token counting and chunking utilities.
"""

import pytest
from app.utils.tokens import count_tokens, truncate_to_tokens, chunk_transcript, get_processing_strategy


class TestCountTokens:
    """Test token counting."""

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello world")
        assert tokens > 0
        assert tokens <= 5  # "Hello" and "world" are typically 2-3 tokens

    def test_longer_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 10
        tokens = count_tokens(text)
        assert tokens > 50

    def test_unicode_text(self):
        tokens = count_tokens("こんにちは世界")
        assert tokens > 0


class TestTruncateToTokens:
    """Test token truncation."""

    def test_short_text_unchanged(self):
        text = "Hello world"
        result = truncate_to_tokens(text, max_tokens=100)
        assert result == text

    def test_long_text_truncated(self):
        text = "word " * 1000
        result = truncate_to_tokens(text, max_tokens=10)
        assert count_tokens(result) <= 10

    def test_empty_text(self):
        result = truncate_to_tokens("", max_tokens=100)
        assert result == ""


class TestChunkTranscript:
    """Test transcript chunking."""

    def test_short_transcript_single_chunk(self):
        text = "Short transcript " * 10
        chunks = chunk_transcript(text, max_tokens_per_chunk=12000)
        assert len(chunks) == 1

    def test_long_transcript_multiple_chunks(self):
        # Create text that's definitely more than one chunk
        text = "word " * 50000  # ~50K tokens
        chunks = chunk_transcript(text, max_tokens_per_chunk=12000)
        assert len(chunks) > 1

    def test_empty_text(self):
        chunks = chunk_transcript("")
        assert len(chunks) == 0 or chunks == [""]


class TestGetProcessingStrategy:
    """Test strategy selection."""

    def test_small_transcript(self):
        assert get_processing_strategy(5000) == "single_pass"

    def test_medium_transcript(self):
        assert get_processing_strategy(50000) == "single_pass"

    def test_large_transcript(self):
        assert get_processing_strategy(100001) == "single_pass_fallback"

    def test_very_large_transcript(self):
        assert get_processing_strategy(200000) == "single_pass_fallback"

    def test_too_large_transcript(self):
        assert get_processing_strategy(200001) == "reject"

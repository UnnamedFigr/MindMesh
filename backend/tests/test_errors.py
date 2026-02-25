"""
Tests for error hierarchy.
"""

import pytest
from app.utils.errors import (
    MindMeshError,
    TranscriptError,
    TriageError,
    GenerationError,
    CreditError,
    RateLimitError,
    SpendCapError,
    AuthError,
    ValidationError,
)


class TestErrorHierarchy:
    """Test exception inheritance and attributes."""

    def test_base_error(self):
        err = MindMeshError("test", code="TEST", user_message="Test error")
        assert str(err) == "test"
        assert err.code == "TEST"
        assert err.user_message == "Test error"
        assert err.status_code == 500

    def test_transcript_error(self):
        err = TranscriptError("no captions", code="NO_CAPTIONS")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 502

    def test_triage_error(self):
        err = TriageError("not educational", code="NOT_EDUCATIONAL")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 422

    def test_generation_error(self):
        err = GenerationError("openai fail", code="OPENAI_ERROR")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 502

    def test_credit_error(self):
        err = CreditError("no credits", code="CREDIT_EXHAUSTED")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 429

    def test_rate_limit_error(self):
        err = RateLimitError("too many", code="RATE_LIMITED")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 429

    def test_spend_cap_error(self):
        err = SpendCapError("cap reached")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 503

    def test_auth_error(self):
        err = AuthError("unauthorized", code="UNAUTHORIZED")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 401

    def test_validation_error(self):
        err = ValidationError("bad input", code="INVALID_URL")
        assert isinstance(err, MindMeshError)
        assert err.status_code == 400

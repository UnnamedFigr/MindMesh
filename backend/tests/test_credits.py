"""
Tests for credit management service.
"""

import pytest
from app.services.credits import get_credit_cost, CREDIT_COSTS


class TestGetCreditCost:
    """Test credit cost calculation."""

    def test_default_cost(self):
        assert get_credit_cost() == 1

    def test_short_video(self):
        assert get_credit_cost(duration_seconds=3600) == 1  # 60 min

    def test_long_video(self):
        assert get_credit_cost(duration_seconds=5400) == 2  # 90 min

    def test_very_long_video(self):
        assert get_credit_cost(duration_seconds=10800) == 2  # 180 min

    def test_none_duration(self):
        assert get_credit_cost(duration_seconds=None) == 1

    def test_zero_duration(self):
        assert get_credit_cost(duration_seconds=0) == 1


class TestCreditCosts:
    """Test credit cost constants."""

    def test_standard_guide_cost(self):
        assert CREDIT_COSTS["standard_guide"] == 1

    def test_long_guide_cost(self):
        assert CREDIT_COSTS["long_guide"] == 2

    def test_regenerate_cost(self):
        assert CREDIT_COSTS["regenerate"] == 1

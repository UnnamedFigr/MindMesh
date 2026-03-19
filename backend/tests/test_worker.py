"""Tests for worker helper functions."""

import asyncio

from app.services.worker import check_existing_guide, get_user_tier


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._filters: dict[str, object] = {}
        self._limit: int | None = None
        self._single = False

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value: object):
        self._filters[column] = value
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        matches = [
            row for row in self._rows
            if all(row.get(column) == value for column, value in self._filters.items())
        ]
        if self._limit is not None:
            matches = matches[: self._limit]
        if self._single:
            return FakeResponse(matches[0] if matches else None)
        return FakeResponse(matches)


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict[str, object]]]):
        self._tables = tables

    def table(self, table_name: str):
        return FakeQuery(self._tables.get(table_name, []))


class TestGetUserTier:
    def test_returns_profile_tier(self):
        supabase = FakeSupabase({
            "profiles": [{"id": "user-1", "tier": "pro"}],
        })

        tier = asyncio.run(get_user_tier("user-1", supabase))

        assert tier == "pro"

    def test_defaults_to_free_without_profile(self):
        supabase = FakeSupabase({"profiles": []})

        tier = asyncio.run(get_user_tier("missing-user", supabase))

        assert tier == "free"


class TestCheckExistingGuide:
    def test_matches_same_variant_only(self):
        supabase = FakeSupabase({
            "study_guides": [
                {
                    "id": "core-guide",
                    "video_id": "video-1",
                    "persona": "academic",
                    "tier": "core",
                    "user_id": "user-1",
                },
                {
                    "id": "pro-guide",
                    "video_id": "video-1",
                    "persona": "academic",
                    "tier": "pro",
                    "user_id": "user-1",
                },
            ]
        })

        core_match = asyncio.run(
            check_existing_guide("video-1", "academic", "core", "user-1", supabase)
        )
        pro_match = asyncio.run(
            check_existing_guide("video-1", "academic", "pro", "user-1", supabase)
        )
        other_tier = asyncio.run(
            check_existing_guide("video-1", "academic", "free", "user-1", supabase)
        )

        assert core_match == "core-guide"
        assert pro_match == "pro-guide"
        assert other_tier is None
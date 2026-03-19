"""
Tests for YouTube URL parsing utility.
"""

import pytest
from app.utils.youtube import extract_video_id, is_playlist_url
from app.utils.errors import ValidationError


class TestExtractVideoId:
    """Test extract_video_id with various YouTube URL formats."""

    def test_standard_watch_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_v_slash_url(self):
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_live_url(self):
        assert extract_video_id("https://www.youtube.com/live/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        assert extract_video_id("https://m.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_music_url(self):
        assert extract_video_id("https://music.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLxyz") == "dQw4w9WgXcQ"

    def test_url_with_timestamp(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=42") == "dQw4w9WgXcQ"

    def test_no_scheme(self):
        assert extract_video_id("youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            extract_video_id("https://www.google.com")

    def test_empty_string(self):
        with pytest.raises(ValidationError):
            extract_video_id("")

    def test_none_input(self):
        with pytest.raises((ValidationError, AttributeError)):
            extract_video_id(None)

    def test_random_text(self):
        with pytest.raises(ValidationError):
            extract_video_id("not a url at all")

    def test_youtube_homepage(self):
        with pytest.raises(ValidationError):
            extract_video_id("https://www.youtube.com")

    def test_youtube_channel(self):
        with pytest.raises(ValidationError):
            extract_video_id("https://www.youtube.com/@channel")


class TestIsPlaylistUrl:
    """Test playlist URL detection."""

    def test_playlist_url(self):
        assert is_playlist_url("https://www.youtube.com/playlist?list=PLxyz123") is True

    def test_watch_with_list(self):
        # Has a video ID, so it's not a pure playlist URL
        assert is_playlist_url("https://www.youtube.com/watch?v=abc&list=PLxyz") is False

    def test_regular_video(self):
        assert is_playlist_url("https://www.youtube.com/watch?v=abc") is False

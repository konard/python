"""Tests for YouTube URL parser"""
import pytest
from app.utils.youtube_url_parser import YouTubeURLParser, parse_youtube_url


class TestYouTubeURLParser:
    """Test cases for YouTube URL parsing"""

    def test_parse_handle_url(self):
        """Test parsing @handle URL"""
        channel_id, username, video_id = parse_youtube_url("https://www.youtube.com/@mkbhd")
        assert channel_id is None
        assert username == "mkbhd"
        assert video_id is None

    def test_parse_channel_id_url(self):
        """Test parsing channel ID URL"""
        channel_id, username, video_id = parse_youtube_url(
            "https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ"
        )
        assert channel_id == "UCBJycsmduvYEL83R_U4JriQ"
        assert username is None
        assert video_id is None

    def test_parse_custom_url(self):
        """Test parsing custom URL"""
        channel_id, username, video_id = parse_youtube_url(
            "https://www.youtube.com/c/MarquesBrownlee"
        )
        assert channel_id is None
        assert username == "MarquesBrownlee"
        assert video_id is None

    def test_parse_user_url(self):
        """Test parsing user URL"""
        channel_id, username, video_id = parse_youtube_url(
            "https://www.youtube.com/user/MarquesBrownlee"
        )
        assert channel_id is None
        assert username == "MarquesBrownlee"
        assert video_id is None

    def test_parse_video_url(self):
        """Test parsing video URL"""
        channel_id, username, video_id = parse_youtube_url(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        assert channel_id is None
        assert username is None
        assert video_id == "dQw4w9WgXcQ"

    def test_parse_short_video_url(self):
        """Test parsing youtu.be short URL"""
        channel_id, username, video_id = parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert channel_id is None
        assert username is None
        assert video_id == "dQw4w9WgXcQ"

    def test_parse_direct_handle(self):
        """Test parsing direct @handle input"""
        channel_id, username, video_id = parse_youtube_url("@mkbhd")
        assert channel_id is None
        assert username == "mkbhd"
        assert video_id is None

    def test_is_channel_id(self):
        """Test channel ID validation"""
        assert YouTubeURLParser.is_channel_id("UCBJycsmduvYEL83R_U4JriQ") is True
        assert YouTubeURLParser.is_channel_id("mkbhd") is False
        assert YouTubeURLParser.is_channel_id("UC123") is False  # too short

    def test_extract_handle(self):
        """Test handle extraction"""
        assert YouTubeURLParser.extract_handle("@mkbhd") == "mkbhd"
        assert YouTubeURLParser.extract_handle("mkbhd") is None

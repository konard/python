"""
Parse YouTube channel URLs and extract channel IDs.
Supports various URL formats.
"""
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class ChannelURLParser:
    """
    Parser for YouTube channel URLs.
    Supports multiple URL formats and extracts channel identifiers.
    """

    # Regular expression patterns for different URL formats
    PATTERNS = {
        "channel_id": r"youtube\.com/channel/([a-zA-Z0-9_-]+)",
        "handle": r"youtube\.com/@([a-zA-Z0-9_-]+)",
        "user": r"youtube\.com/user/([a-zA-Z0-9_-]+)",
        "c_url": r"youtube\.com/c/([a-zA-Z0-9_-]+)",
        "custom": r"youtube\.com/([a-zA-Z0-9_-]+)$",
    }

    @classmethod
    def parse(cls, url: str) -> dict:
        """
        Parse a YouTube URL and extract channel identifier.

        Args:
            url: YouTube URL (channel, video, or custom URL)

        Returns:
            Dict with 'type' and 'id' keys:
            - type: 'channel_id', 'handle', 'user', or 'video'
            - id: The extracted identifier
            - original_url: The input URL

        Raises:
            ValueError: If URL format is not recognized
        """
        url = url.strip()

        # Add https if not present
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)

        # Check if it's a YouTube domain
        if "youtube.com" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            raise ValueError(f"Not a YouTube URL: {url}")

        # Check for video URL (we'll extract channel from video later)
        if "youtu.be" in parsed.netloc or "/watch" in parsed.path:
            video_id = cls._extract_video_id(url)
            if video_id:
                return {
                    "type": "video",
                    "id": video_id,
                    "original_url": url,
                }

        # Try to match channel patterns
        full_url = parsed.geturl()

        # Channel ID format: /channel/UC...
        match = re.search(cls.PATTERNS["channel_id"], full_url)
        if match:
            return {
                "type": "channel_id",
                "id": match.group(1),
                "original_url": url,
            }

        # Handle format: /@username
        match = re.search(cls.PATTERNS["handle"], full_url)
        if match:
            return {
                "type": "handle",
                "id": match.group(1),
                "original_url": url,
            }

        # User format: /user/username
        match = re.search(cls.PATTERNS["user"], full_url)
        if match:
            return {
                "type": "user",
                "id": match.group(1),
                "original_url": url,
            }

        # /c/ format
        match = re.search(cls.PATTERNS["c_url"], full_url)
        if match:
            return {
                "type": "handle",  # Treat as handle
                "id": match.group(1),
                "original_url": url,
            }

        # Custom URL (just username)
        match = re.search(cls.PATTERNS["custom"], full_url)
        if match:
            return {
                "type": "handle",
                "id": match.group(1),
                "original_url": url,
            }

        raise ValueError(f"Could not parse YouTube URL: {url}")

    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube video URL formats.

        Args:
            url: YouTube video URL

        Returns:
            Video ID or None if not found
        """
        # youtu.be/VIDEO_ID
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        # youtube.com/watch?v=VIDEO_ID
        parsed = urlparse(url)
        if "/watch" in parsed.path:
            params = parse_qs(parsed.query)
            if "v" in params:
                return params["v"][0]

        # youtube.com/embed/VIDEO_ID
        match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        # youtube.com/v/VIDEO_ID
        match = re.search(r"youtube\.com/v/([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def is_valid_channel_id(channel_id: str) -> bool:
        """
        Check if a string is a valid YouTube channel ID.
        Channel IDs typically start with 'UC' and are 24 characters long.

        Args:
            channel_id: String to validate

        Returns:
            True if valid channel ID format
        """
        return bool(re.match(r"^UC[a-zA-Z0-9_-]{22}$", channel_id))

    @staticmethod
    def is_valid_video_id(video_id: str) -> bool:
        """
        Check if a string is a valid YouTube video ID.
        Video IDs are 11 characters long.

        Args:
            video_id: String to validate

        Returns:
            True if valid video ID format
        """
        return bool(re.match(r"^[a-zA-Z0-9_-]{11}$", video_id))

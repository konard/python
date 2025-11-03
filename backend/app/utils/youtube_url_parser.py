"""YouTube URL parser to extract channel IDs"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


class YouTubeURLParser:
    """
    Parser for YouTube URLs to extract channel identifiers.

    Supported formats:
    - https://www.youtube.com/@handle
    - https://www.youtube.com/channel/UCxxxxx
    - https://www.youtube.com/c/customname
    - https://www.youtube.com/user/username
    - https://www.youtube.com/watch?v=videoid (extracts video, need to fetch channel)
    """

    # Regex patterns
    CHANNEL_ID_PATTERN = re.compile(r"^UC[\w-]{22}$")
    HANDLE_PATTERN = re.compile(r"@([\w-]+)")

    @classmethod
    def parse_url(cls, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse YouTube URL to extract identifiers.

        Args:
            url: YouTube URL or handle

        Returns:
            Tuple of (channel_id, username, video_id)
            - channel_id: Direct channel ID (UCxxxxx) if found
            - username: Username/handle if found (needs API lookup)
            - video_id: Video ID if URL is a video link

        Examples:
            >>> parse_url("https://youtube.com/@mkbhd")
            (None, "mkbhd", None)

            >>> parse_url("https://youtube.com/channel/UC123456789")
            ("UC123456789", None, None)

            >>> parse_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
            (None, None, "dQw4w9WgXcQ")
        """
        url = url.strip()

        # Handle direct @handle input
        if url.startswith("@"):
            handle = url[1:]
            return None, handle, None

        # Parse as URL
        try:
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            path_parts = path.split("/")

            # Channel ID: /channel/UCxxxxx
            if len(path_parts) >= 2 and path_parts[0] == "channel":
                channel_id = path_parts[1]
                if cls.CHANNEL_ID_PATTERN.match(channel_id):
                    return channel_id, None, None

            # Handle: /@handle
            if path.startswith("@"):
                handle = path[1:]
                return None, handle, None

            # Custom URL: /c/customname
            if len(path_parts) >= 2 and path_parts[0] == "c":
                username = path_parts[1]
                return None, username, None

            # User URL: /user/username
            if len(path_parts) >= 2 and path_parts[0] == "user":
                username = path_parts[1]
                return None, username, None

            # Video URL: /watch?v=videoid
            if path == "watch" or path.startswith("watch"):
                query_params = parse_qs(parsed.query)
                video_id = query_params.get("v", [None])[0]
                if video_id:
                    return None, None, video_id

            # Short video URL: youtu.be/videoid
            if parsed.netloc in ["youtu.be", "www.youtu.be"]:
                video_id = path_parts[0] if path_parts else None
                if video_id:
                    return None, None, video_id

            # Direct channel path: /UCxxxxx
            if len(path_parts) == 1 and cls.CHANNEL_ID_PATTERN.match(path_parts[0]):
                return path_parts[0], None, None

            # Handle pattern in path
            handle_match = cls.HANDLE_PATTERN.search(path)
            if handle_match:
                return None, handle_match.group(1), None

        except Exception as e:
            print(f"Error parsing URL {url}: {e}")

        return None, None, None

    @classmethod
    def is_channel_id(cls, text: str) -> bool:
        """Check if text is a valid YouTube channel ID (UCxxxxx)"""
        return bool(cls.CHANNEL_ID_PATTERN.match(text))

    @classmethod
    def extract_handle(cls, text: str) -> Optional[str]:
        """Extract handle from @handle format"""
        if text.startswith("@"):
            return text[1:]
        match = cls.HANDLE_PATTERN.search(text)
        return match.group(1) if match else None


def parse_youtube_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Convenience function to parse YouTube URL.

    Returns:
        Tuple of (channel_id, username, video_id)
    """
    return YouTubeURLParser.parse_url(url)

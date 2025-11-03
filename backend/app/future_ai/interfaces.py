"""
Abstract interfaces for future AI integrations.
These are stubs that can be implemented later with real LLM services.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


# Data models for AI features
class Comment(BaseModel):
    """Comment data model."""
    id: str
    video_id: str
    text: str
    like_count: int
    published_at: datetime


class SentimentResult(BaseModel):
    """Sentiment analysis result."""
    overall_sentiment: str  # 'positive', 'negative', 'neutral'
    sentiment_score: float  # -1.0 to 1.0
    positive_count: int
    negative_count: int
    neutral_count: int
    top_positive_comments: List[str]
    top_negative_comments: List[str]


class Topic(BaseModel):
    """Extracted topic from comments."""
    name: str
    frequency: int
    keywords: List[str]
    sentiment: str


class ChannelStats(BaseModel):
    """Channel statistics for analysis."""
    channel_id: str
    total_views: int
    total_videos: int
    avg_views_per_video: float
    avg_engagement_rate: float
    top_performing_topics: List[str]
    recent_growth_rate: float


class ContentIdea(BaseModel):
    """Generated content idea."""
    title: str
    description: str
    target_keywords: List[str]
    estimated_appeal_score: float
    reasoning: str


class VideoScript(BaseModel):
    """Generated video script."""
    title: str
    introduction: str
    main_sections: List[Dict[str, str]]  # [{"heading": "", "content": "", "timing": ""}]
    conclusion: str
    call_to_action: str
    total_duration_minutes: int
    keywords: List[str]


# Abstract interfaces
class CommentAnalyzer(ABC):
    """Interface for comment sentiment and topic analysis."""

    @abstractmethod
    async def analyze_sentiment(
        self,
        comments: List[Comment],
    ) -> SentimentResult:
        """
        Analyze sentiment of a list of comments.

        Args:
            comments: List of comment objects

        Returns:
            Aggregated sentiment analysis result
        """
        pass

    @abstractmethod
    async def extract_topics(
        self,
        comments: List[Comment],
        max_topics: int = 10,
    ) -> List[Topic]:
        """
        Extract main topics from comments.

        Args:
            comments: List of comment objects
            max_topics: Maximum number of topics to extract

        Returns:
            List of extracted topics with metadata
        """
        pass

    @abstractmethod
    async def identify_issues(
        self,
        comments: List[Comment],
    ) -> List[str]:
        """
        Identify common problems or complaints in comments.

        Args:
            comments: List of comment objects

        Returns:
            List of identified issues/problems
        """
        pass


class ContentIdeaGenerator(ABC):
    """Interface for generating content ideas."""

    @abstractmethod
    async def generate_ideas(
        self,
        channel_stats: ChannelStats,
        competitor_topics: Optional[List[str]] = None,
        count: int = 10,
    ) -> List[ContentIdea]:
        """
        Generate content ideas based on channel performance.

        Args:
            channel_stats: Statistics and performance data
            competitor_topics: Topics from competitor channels
            count: Number of ideas to generate

        Returns:
            List of content ideas with reasoning
        """
        pass

    @abstractmethod
    async def analyze_title_performance(
        self,
        titles: List[str],
        view_counts: List[int],
    ) -> Dict[str, Any]:
        """
        Analyze what makes titles perform well.

        Args:
            titles: List of video titles
            view_counts: Corresponding view counts

        Returns:
            Analysis of title patterns and recommendations
        """
        pass


class ScriptGenerator(ABC):
    """Interface for generating video scripts."""

    @abstractmethod
    async def generate_script(
        self,
        topic: str,
        target_duration_minutes: int,
        style: str = "educational",
        keywords: Optional[List[str]] = None,
    ) -> VideoScript:
        """
        Generate a video script for a given topic.

        Args:
            topic: The main topic/title for the video
            target_duration_minutes: Desired video length
            style: Video style (educational, entertaining, etc.)
            keywords: Keywords to include in the script

        Returns:
            Complete video script with structure
        """
        pass

    @abstractmethod
    async def refine_script(
        self,
        script: VideoScript,
        feedback: str,
    ) -> VideoScript:
        """
        Refine an existing script based on feedback.

        Args:
            script: Original script
            feedback: User feedback for improvements

        Returns:
            Refined video script
        """
        pass


# Stub implementations (return mock data)
class StubCommentAnalyzer(CommentAnalyzer):
    """Stub implementation for testing."""

    async def analyze_sentiment(self, comments: List[Comment]) -> SentimentResult:
        return SentimentResult(
            overall_sentiment="positive",
            sentiment_score=0.65,
            positive_count=int(len(comments) * 0.7),
            negative_count=int(len(comments) * 0.1),
            neutral_count=int(len(comments) * 0.2),
            top_positive_comments=["Great video!", "Thanks for sharing!"],
            top_negative_comments=["Could be better"],
        )

    async def extract_topics(
        self,
        comments: List[Comment],
        max_topics: int = 10,
    ) -> List[Topic]:
        return [
            Topic(
                name="Health Tips",
                frequency=15,
                keywords=["health", "wellness", "tips"],
                sentiment="positive",
            )
        ]

    async def identify_issues(self, comments: List[Comment]) -> List[str]:
        return ["Audio quality could be improved", "More examples needed"]


class StubContentIdeaGenerator(ContentIdeaGenerator):
    """Stub implementation for testing."""

    async def generate_ideas(
        self,
        channel_stats: ChannelStats,
        competitor_topics: Optional[List[str]] = None,
        count: int = 10,
    ) -> List[ContentIdea]:
        return [
            ContentIdea(
                title="10 Simple Health Habits for Better Sleep",
                description="Explore evidence-based sleep hygiene practices",
                target_keywords=["sleep", "health", "wellness"],
                estimated_appeal_score=0.85,
                reasoning="Sleep content performs well based on channel history",
            )
        ]

    async def analyze_title_performance(
        self,
        titles: List[str],
        view_counts: List[int],
    ) -> Dict[str, Any]:
        return {
            "top_patterns": ["Numbered lists", "How-to format"],
            "avg_length": 45,
            "recommendations": ["Use specific numbers", "Include actionable words"],
        }


class StubScriptGenerator(ScriptGenerator):
    """Stub implementation for testing."""

    async def generate_script(
        self,
        topic: str,
        target_duration_minutes: int,
        style: str = "educational",
        keywords: Optional[List[str]] = None,
    ) -> VideoScript:
        return VideoScript(
            title=topic,
            introduction=f"Welcome! Today we're discussing {topic}.",
            main_sections=[
                {
                    "heading": "Overview",
                    "content": "Main content here...",
                    "timing": "0:30-2:00",
                }
            ],
            conclusion="Thanks for watching!",
            call_to_action="Subscribe for more content!",
            total_duration_minutes=target_duration_minutes,
            keywords=keywords or [],
        )

    async def refine_script(
        self,
        script: VideoScript,
        feedback: str,
    ) -> VideoScript:
        # Return the same script with minor modifications
        return script

export interface Channel {
  id: number;
  youtube_channel_id: string;
  title: string;
  description: string | null;
  custom_url: string | null;
  published_at: string;
  country: string | null;
  thumbnails: Record<string, any>;
  is_own_channel: boolean;
  subscriber_count: number | null;
  view_count: number;
  video_count: number;
  hidden_subscriber_count: boolean;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: number;
  youtube_video_id: string;
  channel_id: number;
  title: string;
  description: string | null;
  published_at: string;
  thumbnails: Record<string, any>;
  duration_seconds: number | null;
  view_count: number;
  like_count: number;
  comment_count: number;
  tags: string[];
  category_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface VideoMetrics {
  video_id: number;
  youtube_video_id: string;
  title: string;
  published_at: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  like_ratio: number;
  comment_rate: number;
  engagement_rate: number;
  views_per_day: number;
  view_growth_24h: number | null;
  view_growth_7d: number | null;
}

export interface ChannelMetrics {
  channel_id: number;
  youtube_channel_id: string;
  title: string;
  view_count: number;
  subscriber_count: number | null;
  video_count: number;
  avg_views_per_video: number;
  view_growth_7d: number | null;
  view_growth_30d: number | null;
  subscriber_growth_7d: number | null;
  subscriber_growth_30d: number | null;
}

export interface TrendingVideo {
  video_id: number;
  youtube_video_id: string;
  title: string;
  channel_title: string;
  published_at: string;
  view_count: number;
  view_growth: number;
  growth_percentage: number;
}

export interface AddChannelRequest {
  url: string;
  is_own_channel?: boolean;
}

export interface AddChannelResponse {
  channel: Channel;
  message: string;
}

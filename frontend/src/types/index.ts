export interface Channel {
  id: number;
  youtube_channel_id: string;
  title: string;
  description?: string;
  custom_url?: string;
  published_at: string;
  thumbnail_url?: string;
  country?: string;
  view_count: number;
  subscriber_count?: number;
  hidden_subscriber_count: boolean;
  video_count: number;
  is_own_channel: boolean;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: number;
  youtube_video_id: string;
  channel_id: number;
  title: string;
  description?: string;
  published_at: string;
  thumbnail_url?: string;
  duration_seconds: number;
  view_count: number;
  like_count: number;
  comment_count: number;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface VideoMetrics {
  video_id: number;
  view_count: number;
  like_count: number;
  comment_count: number;
  like_ratio: number;
  comment_rate: number;
  engagement_rate: number;
  views_per_day: number;
  growth_24h?: number;
  growth_7d?: number;
}

export interface ChannelMetrics {
  channel_id: number;
  total_views: number;
  subscriber_count?: number;
  video_count: number;
  avg_views_per_video: number;
  growth_7d?: number;
  growth_30d?: number;
}

export interface TrendingVideo extends Video {
  metrics: VideoMetrics;
  channel_title: string;
}

export interface AddChannelRequest {
  url: string;
  is_own_channel?: boolean;
}

export interface QuotaStatus {
  [key: string]: {
    key: string;
    quota_used: number;
    quota_limit: number;
    quota_remaining: number;
    usage_percent: number;
    is_disabled: boolean;
    disabled_until?: string;
    error_count: number;
    last_error?: string;
    last_reset: string;
  };
}

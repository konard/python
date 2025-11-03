import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { channelsApi, videosApi, analyticsApi } from '../lib/api';
import type { Channel, Video, ChannelMetrics } from '../types';
import { formatNumber, formatDuration, formatDate, formatPercentage } from '../lib/utils';

export default function ChannelDetail() {
  const { id } = useParams<{ id: string }>();
  const channelId = parseInt(id || '0');

  const [channel, setChannel] = useState<Channel | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [metrics, setMetrics] = useState<ChannelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'views'>('date');

  useEffect(() => {
    loadChannelData();
  }, [channelId]);

  const loadChannelData = async () => {
    try {
      setLoading(true);
      const [channelData, videosData, metricsData] = await Promise.all([
        channelsApi.get(channelId),
        videosApi.listByChannel(channelId),
        analyticsApi.getChannelMetrics(channelId),
      ]);

      setChannel(channelData);
      setVideos(videosData);
      setMetrics(metricsData);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load channel data');
    } finally {
      setLoading(false);
    }
  };

  const sortedVideos = [...videos].sort((a, b) => {
    if (sortBy === 'views') {
      return b.view_count - a.view_count;
    }
    return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
  });

  const calculateEngagement = (video: Video) => {
    if (video.view_count === 0) return 0;
    return ((video.like_count + video.comment_count) / video.view_count) * 100;
  };

  if (loading) {
    return <div className="spinner" style={{ margin: '4rem auto' }} />;
  }

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <div className="card" style={{ backgroundColor: '#f443364d', border: '1px solid #f44336' }}>
          <p style={{ color: '#f44336' }}>{error}</p>
        </div>
        <Link to="/channels">
          <button>Back to Channels</button>
        </Link>
      </div>
    );
  }

  if (!channel) {
    return <div style={{ padding: '2rem' }}>Channel not found</div>;
  }

  return (
    <div style={{ padding: '2rem' }}>
      <Link to="/channels" style={{ marginBottom: '1rem', display: 'inline-block' }}>
        ← Back to Channels
      </Link>

      {/* Channel Header */}
      <div className="card">
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
          {channel.thumbnail_url && (
            <img
              src={channel.thumbnail_url}
              alt={channel.title}
              style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                objectFit: 'cover',
              }}
            />
          )}

          <div style={{ flex: 1 }}>
            <h1 style={{ marginBottom: '0.5rem' }}>{channel.title}</h1>
            {channel.is_own_channel && <span className="badge success">My Channel</span>}

            {channel.description && (
              <p style={{ color: 'var(--text-secondary)', marginTop: '1rem', fontSize: '0.9rem' }}>
                {channel.description.substring(0, 300)}
                {channel.description.length > 300 && '...'}
              </p>
            )}

            <div
              style={{
                marginTop: '1.5rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
              }}
            >
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Total Views</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{formatNumber(channel.view_count)}</div>
              </div>

              {!channel.hidden_subscriber_count && channel.subscriber_count !== null && (
                <div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Subscribers</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>
                    {formatNumber(channel.subscriber_count)}
                  </div>
                </div>
              )}

              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Videos</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{channel.video_count}</div>
              </div>

              {metrics && (
                <div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Avg Views/Video</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>
                    {formatNumber(metrics.avg_views_per_video)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Videos Section */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>Videos ({videos.length})</h2>
          <div>
            <label style={{ marginRight: '0.5rem', fontSize: '0.9rem' }}>Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'date' | 'views')}
              style={{
                padding: '0.5rem',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="date">Date (newest first)</option>
              <option value="views">Views (highest first)</option>
            </select>
          </div>
        </div>

        {sortedVideos.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
            No videos found. Click "Import Videos" to fetch videos from this channel.
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>Title</th>
                  <th>Published</th>
                  <th>Duration</th>
                  <th>Views</th>
                  <th>Likes</th>
                  <th>Comments</th>
                  <th>Engagement</th>
                </tr>
              </thead>
              <tbody>
                {sortedVideos.map((video) => (
                  <tr key={video.id}>
                    <td>
                      {video.thumbnail_url && (
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          style={{
                            width: '120px',
                            height: '68px',
                            borderRadius: '6px',
                            objectFit: 'cover',
                          }}
                        />
                      )}
                    </td>
                    <td>
                      <a
                        href={`https://www.youtube.com/watch?v=${video.youtube_video_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontWeight: '500' }}
                      >
                        {video.title}
                      </a>
                    </td>
                    <td>{formatDate(video.published_at)}</td>
                    <td>{formatDuration(video.duration_seconds)}</td>
                    <td>{formatNumber(video.view_count)}</td>
                    <td>{formatNumber(video.like_count)}</td>
                    <td>{formatNumber(video.comment_count)}</td>
                    <td>{formatPercentage(calculateEngagement(video))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

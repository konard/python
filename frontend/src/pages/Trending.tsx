import { useState, useEffect } from 'react';
import { analyticsApi } from '../lib/api';
import type { TrendingVideo } from '../types';
import { formatNumber, formatDate, formatPercentage } from '../lib/utils';

export default function Trending() {
  const [videos, setVideos] = useState<TrendingVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number>(24);

  useEffect(() => {
    loadTrendingVideos();
  }, [timeRange]);

  const loadTrendingVideos = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getTrendingVideos(timeRange);
      setVideos(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load trending videos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Trending Videos</h1>

        <div>
          <label style={{ marginRight: '0.5rem' }}>Time Range:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              backgroundColor: 'var(--surface)',
              color: 'var(--text-primary)',
            }}
          >
            <option value={24}>Last 24 hours</option>
            <option value={48}>Last 48 hours</option>
            <option value={168}>Last 7 days</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="card" style={{ backgroundColor: '#f443364d', border: '1px solid #f44336' }}>
          <p style={{ color: '#f44336', margin: 0 }}>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="spinner" />
      ) : videos.length === 0 ? (
        <div className="card">
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
            No trending videos found for the selected time range.
            <br />
            <small>Make sure you have channels added and video statistics are being collected.</small>
          </p>
        </div>
      ) : (
        <div className="card">
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>#</th>
                  <th></th>
                  <th>Video</th>
                  <th>Channel</th>
                  <th>Published</th>
                  <th>Views</th>
                  <th>Growth</th>
                  <th>Engagement</th>
                </tr>
              </thead>
              <tbody>
                {videos.map((video, index) => (
                  <tr key={video.id}>
                    <td>
                      <div
                        style={{
                          fontSize: '1.5rem',
                          fontWeight: '700',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {index + 1}
                      </div>
                    </td>
                    <td>
                      {video.thumbnail_url && (
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          style={{
                            width: '160px',
                            height: '90px',
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
                        style={{ fontWeight: '500', fontSize: '0.95rem' }}
                      >
                        {video.title}
                      </a>
                    </td>
                    <td>{video.channel_title}</td>
                    <td>{formatDate(video.published_at)}</td>
                    <td>
                      <strong>{formatNumber(video.view_count)}</strong>
                    </td>
                    <td>
                      {video.metrics.growth_24h !== undefined && (
                        <span className="badge success">
                          +{formatNumber(video.metrics.growth_24h)} views
                        </span>
                      )}
                    </td>
                    <td>{formatPercentage(video.metrics.engagement_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

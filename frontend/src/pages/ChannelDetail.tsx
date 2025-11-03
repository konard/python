import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { channelsApi, analyticsApi } from '../lib/api';
import type { Channel, Video, ChannelMetrics } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ChannelDetail() {
  const { id } = useParams<{ id: string }>();
  const channelId = parseInt(id || '0');

  const [channel, setChannel] = useState<Channel | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [metrics, setMetrics] = useState<ChannelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'views' | 'likes' | 'date'>('views');

  useEffect(() => {
    if (channelId) {
      loadData();
    }
  }, [channelId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [channelData, videosData, metricsData] = await Promise.all([
        channelsApi.get(channelId),
        channelsApi.getVideos(channelId),
        analyticsApi.getChannelMetrics(channelId),
      ]);
      setChannel(channelData);
      setVideos(videosData);
      setMetrics(metricsData);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load channel data');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number | null) => {
    if (num === null) return 'N/A';
    return num.toLocaleString();
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getSortedVideos = () => {
    const sorted = [...videos];
    switch (sortBy) {
      case 'views':
        return sorted.sort((a, b) => b.view_count - a.view_count);
      case 'likes':
        return sorted.sort((a, b) => b.like_count - a.like_count);
      case 'date':
        return sorted.sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());
      default:
        return sorted;
    }
  };

  const getTopVideosChartData = () => {
    return getSortedVideos()
      .slice(0, 10)
      .map((video) => ({
        title: video.title.length > 30 ? video.title.substring(0, 30) + '...' : video.title,
        views: video.view_count,
        likes: video.like_count,
      }));
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading channel...</p>
      </div>
    );
  }

  if (error || !channel) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || 'Channel not found'}</p>
        <Link to="/" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
          Back to Channels
        </Link>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-0">
      <Link to="/" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
        &larr; Back to Channels
      </Link>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex items-start">
          {channel.thumbnails?.default?.url && (
            <img
              src={channel.thumbnails.default.url}
              alt={channel.title}
              className="h-20 w-20 rounded-full mr-6"
            />
          )}
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">{channel.title}</h1>
            {channel.description && (
              <p className="mt-2 text-gray-600">{channel.description}</p>
            )}
            {channel.custom_url && (
              <a
                href={`https://youtube.com/${channel.custom_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-blue-600 hover:text-blue-800"
              >
                {channel.custom_url}
              </a>
            )}
          </div>
        </div>
      </div>

      {metrics && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Channel Metrics</h2>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="bg-gray-50 px-4 py-3 rounded">
              <dt className="text-sm font-medium text-gray-500">Total Views</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{formatNumber(metrics.view_count)}</dd>
            </div>
            <div className="bg-gray-50 px-4 py-3 rounded">
              <dt className="text-sm font-medium text-gray-500">Subscribers</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{formatNumber(metrics.subscriber_count)}</dd>
            </div>
            <div className="bg-gray-50 px-4 py-3 rounded">
              <dt className="text-sm font-medium text-gray-500">Total Videos</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{formatNumber(metrics.video_count)}</dd>
            </div>
            <div className="bg-gray-50 px-4 py-3 rounded">
              <dt className="text-sm font-medium text-gray-500">Avg Views/Video</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">{formatNumber(Math.round(metrics.avg_views_per_video))}</dd>
            </div>
          </dl>
        </div>
      )}

      {videos.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top 10 Videos by Views</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getTopVideosChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="title" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="views" fill="#3b82f6" name="Views" />
              <Bar dataKey="likes" fill="#10b981" name="Likes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">Videos ({videos.length})</h2>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            <option value="views">Sort by Views</option>
            <option value="likes">Sort by Likes</option>
            <option value="date">Sort by Date</option>
          </select>
        </div>

        {videos.length === 0 ? (
          <p className="text-center text-gray-600 py-8">
            No videos imported yet. Click "Import Videos" on the channels page.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Video
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Published
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Views
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Likes
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Comments
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {getSortedVideos().map((video) => (
                  <tr key={video.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        {video.thumbnails?.default?.url && (
                          <img
                            src={video.thumbnails.default.url}
                            alt={video.title}
                            className="h-12 w-20 object-cover rounded mr-3"
                          />
                        )}
                        <div className="max-w-xs">
                          <a
                            href={`https://youtube.com/watch?v=${video.youtube_video_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
                          >
                            {video.title}
                          </a>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(video.published_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDuration(video.duration_seconds)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(video.view_count)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(video.like_count)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(video.comment_count)}
                    </td>
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

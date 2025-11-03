import { useState, useEffect } from 'react';
import { analyticsApi } from '../lib/api';
import type { TrendingVideo } from '../types/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Trending() {
  const [videos, setVideos] = useState<TrendingVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<24 | 168>(24); // 24h or 7d (168h)

  useEffect(() => {
    loadTrendingVideos();
  }, [timeRange]);

  const loadTrendingVideos = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getTrendingVideos(timeRange, undefined, 20);
      setVideos(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load trending videos');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatGrowth = (growth: number) => {
    if (growth >= 1000000) {
      return `+${(growth / 1000000).toFixed(1)}M`;
    } else if (growth >= 1000) {
      return `+${(growth / 1000).toFixed(1)}K`;
    }
    return `+${growth}`;
  };

  const getChartData = () => {
    return videos.slice(0, 10).map((video, index) => ({
      rank: index + 1,
      title: video.title.length > 20 ? video.title.substring(0, 20) + '...' : video.title,
      viewGrowth: video.view_growth,
      growthPercentage: video.growth_percentage,
    }));
  };

  if (loading && videos.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading trending videos...</p>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Trending Videos</h2>
        <p className="mt-1 text-sm text-gray-600">
          Videos with the highest view growth
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Time Range</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => setTimeRange(24)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                timeRange === 24
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Last 24 Hours
            </button>
            <button
              onClick={() => setTimeRange(168)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                timeRange === 168
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Last 7 Days
            </button>
          </div>
        </div>
      </div>

      {videos.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top 10 View Growth</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="rank" label={{ value: 'Rank', position: 'insideBottom', offset: -5 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="viewGrowth" stroke="#3b82f6" name="View Growth" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {videos.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">
              No trending videos found. Make sure you have channels added and videos imported.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Video
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Views
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    View Growth
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Growth %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Published
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {videos.map((video, index) => (
                  <tr key={video.video_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-semibold">
                        {index + 1}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <a
                        href={`https://youtube.com/watch?v=${video.youtube_video_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-gray-900 hover:text-blue-600 max-w-md line-clamp-2"
                      >
                        {video.title}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {video.channel_title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(video.view_count)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {formatGrowth(video.view_growth)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        +{video.growth_percentage.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(video.published_at).toLocaleDateString()}
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

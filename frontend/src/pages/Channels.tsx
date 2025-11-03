import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { channelsApi } from '../lib/api';
import type { Channel } from '../types/api';

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addingChannel, setAddingChannel] = useState(false);
  const [newChannelUrl, setNewChannelUrl] = useState('');
  const [isOwnChannel, setIsOwnChannel] = useState(false);

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    try {
      setLoading(true);
      const data = await channelsApi.list();
      setChannels(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load channels');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChannelUrl.trim()) return;

    try {
      setAddingChannel(true);
      await channelsApi.add({
        url: newChannelUrl,
        is_own_channel: isOwnChannel,
      });
      setNewChannelUrl('');
      setIsOwnChannel(false);
      await loadChannels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add channel');
    } finally {
      setAddingChannel(false);
    }
  };

  const handleImportVideos = async (channelId: number) => {
    try {
      await channelsApi.importVideos(channelId, 50);
      alert('Video import started! This may take a few minutes.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start video import');
    }
  };

  const formatNumber = (num: number | null) => {
    if (num === null) return 'N/A';
    return num.toLocaleString();
  };

  if (loading && channels.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading channels...</p>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Channels</h2>
        <p className="mt-1 text-sm text-gray-600">
          Add and monitor YouTube channels
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Channel</h3>
        <form onSubmit={handleAddChannel} className="space-y-4">
          <div>
            <label htmlFor="channel-url" className="block text-sm font-medium text-gray-700">
              Channel URL
            </label>
            <input
              type="text"
              id="channel-url"
              value={newChannelUrl}
              onChange={(e) => setNewChannelUrl(e.target.value)}
              placeholder="https://www.youtube.com/@channelname or https://www.youtube.com/channel/..."
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
              disabled={addingChannel}
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is-own"
              checked={isOwnChannel}
              onChange={(e) => setIsOwnChannel(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={addingChannel}
            />
            <label htmlFor="is-own" className="ml-2 block text-sm text-gray-700">
              This is my channel
            </label>
          </div>
          <button
            type="submit"
            disabled={addingChannel || !newChannelUrl.trim()}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {addingChannel ? 'Adding...' : 'Add Channel'}
          </button>
        </form>
      </div>

      {channels.length === 0 ? (
        <div className="text-center py-12 bg-white shadow rounded-lg">
          <p className="text-gray-600">No channels added yet. Add your first channel above!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {channels.map((channel) => (
            <div key={channel.id} className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-start">
                  {channel.thumbnails?.default?.url && (
                    <img
                      src={channel.thumbnails.default.url}
                      alt={channel.title}
                      className="h-16 w-16 rounded-full mr-4"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {channel.title}
                    </h3>
                    {channel.is_own_channel && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        Own Channel
                      </span>
                    )}
                  </div>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Subscribers</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatNumber(channel.subscriber_count)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Views</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatNumber(channel.view_count)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Videos</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatNumber(channel.video_count)}</dd>
                  </div>
                </dl>
                <div className="mt-6 flex space-x-3">
                  <Link
                    to={`/channels/${channel.id}`}
                    className="flex-1 text-center bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
                  >
                    View Details
                  </Link>
                  <button
                    onClick={() => handleImportVideos(channel.id)}
                    className="flex-1 text-center bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 text-sm font-medium"
                  >
                    Import Videos
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { channelsApi } from '../lib/api';
import type { Channel } from '../types';
import { formatNumber, timeAgo } from '../lib/utils';

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingChannel, setAddingChannel] = useState(false);
  const [channelUrl, setChannelUrl] = useState('');
  const [isOwnChannel, setIsOwnChannel] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setError(err.message || 'Failed to load channels');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChannel = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!channelUrl.trim()) {
      setError('Please enter a channel URL');
      return;
    }

    try {
      setAddingChannel(true);
      setError(null);

      await channelsApi.add({
        url: channelUrl,
        is_own_channel: isOwnChannel,
      });

      // Reset form
      setChannelUrl('');
      setIsOwnChannel(false);

      // Reload channels
      await loadChannels();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to add channel');
    } finally {
      setAddingChannel(false);
    }
  };

  const handleImportVideos = async (channelId: number) => {
    try {
      setError(null);
      await channelsApi.importVideos(channelId, 100); // Import up to 100 videos
      alert('Video import started! This may take a few moments.');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to import videos');
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>YouTube Channels</h1>

      {/* Add Channel Form */}
      <div className="card">
        <h3>Add New Channel</h3>
        <form onSubmit={handleAddChannel} style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
          <div>
            <input
              type="text"
              placeholder="Enter YouTube channel URL (e.g., https://www.youtube.com/@mkbhd)"
              value={channelUrl}
              onChange={(e) => setChannelUrl(e.target.value)}
              disabled={addingChannel}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              id="isOwnChannel"
              checked={isOwnChannel}
              onChange={(e) => setIsOwnChannel(e.target.checked)}
              disabled={addingChannel}
            />
            <label htmlFor="isOwnChannel">This is my channel</label>
          </div>
          <div>
            <button type="submit" disabled={addingChannel}>
              {addingChannel ? 'Adding...' : 'Add Channel'}
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card" style={{ backgroundColor: '#f443364d', border: '1px solid #f44336' }}>
          <p style={{ color: '#f44336', margin: 0 }}>{error}</p>
        </div>
      )}

      {/* Channels List */}
      {loading ? (
        <div className="spinner" />
      ) : channels.length === 0 ? (
        <div className="card">
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
            No channels yet. Add your first channel above!
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
          {channels.map((channel) => (
            <div key={channel.id} className="card">
              {channel.thumbnail_url && (
                <img
                  src={channel.thumbnail_url}
                  alt={channel.title}
                  style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    marginBottom: '1rem',
                  }}
                />
              )}

              <h3 style={{ marginBottom: '0.5rem' }}>
                <Link to={`/channels/${channel.id}`}>{channel.title}</Link>
              </h3>

              {channel.is_own_channel && <span className="badge success">My Channel</span>}

              <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <p>
                  <strong>{formatNumber(channel.view_count)}</strong> views
                </p>
                {!channel.hidden_subscriber_count && channel.subscriber_count !== null && (
                  <p>
                    <strong>{formatNumber(channel.subscriber_count)}</strong> subscribers
                  </p>
                )}
                <p>
                  <strong>{channel.video_count}</strong> videos
                </p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
                  Added {timeAgo(channel.created_at)}
                </p>
              </div>

              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                <Link to={`/channels/${channel.id}`}>
                  <button className="secondary">View Details</button>
                </Link>
                <button className="secondary" onClick={() => handleImportVideos(channel.id)}>
                  Import Videos
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

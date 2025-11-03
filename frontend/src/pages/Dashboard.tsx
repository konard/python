import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { channelsApi, systemApi } from '../lib/api';
import type { Channel, QuotaStatus } from '../types';
import { formatNumber } from '../lib/utils';

export default function Dashboard() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [quotaStatus, setQuotaStatus] = useState<QuotaStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [channelsData, quotaData] = await Promise.all([
        channelsApi.list(),
        systemApi.getQuotaStatus(),
      ]);

      setChannels(channelsData);
      setQuotaStatus(quotaData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const totalViews = channels.reduce((sum, ch) => sum + ch.view_count, 0);
  const totalVideos = channels.reduce((sum, ch) => sum + ch.video_count, 0);
  const ownChannels = channels.filter((ch) => ch.is_own_channel);
  const competitorChannels = channels.filter((ch) => !ch.is_own_channel);

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ marginBottom: '2rem' }}>Dashboard</h1>

      {loading ? (
        <div className="spinner" />
      ) : (
        <>
          {/* Stats Overview */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            <div className="card">
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Total Channels</div>
              <div style={{ fontSize: '2rem', fontWeight: '700' }}>{channels.length}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                {ownChannels.length} own, {competitorChannels.length} competitors
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Total Videos</div>
              <div style={{ fontSize: '2rem', fontWeight: '700' }}>{totalVideos}</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Total Views</div>
              <div style={{ fontSize: '2rem', fontWeight: '700' }}>{formatNumber(totalViews)}</div>
            </div>
          </div>

          {/* API Quota Status */}
          {quotaStatus && (
            <div className="card" style={{ marginBottom: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>API Quota Status</h3>
              <div style={{ display: 'grid', gap: '1rem' }}>
                {Object.entries(quotaStatus).map(([keyName, status]) => (
                  <div
                    key={keyName}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '1rem',
                      backgroundColor: 'var(--background)',
                      borderRadius: '8px',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '500' }}>API Key: {status.key}</div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                        {status.quota_used.toLocaleString()} / {status.quota_limit.toLocaleString()} used
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div
                        className={`badge ${
                          status.usage_percent > 80
                            ? 'error'
                            : status.usage_percent > 50
                            ? 'warning'
                            : 'success'
                        }`}
                      >
                        {status.usage_percent.toFixed(1)}%
                      </div>
                      {status.is_disabled && (
                        <div style={{ fontSize: '0.8rem', color: '#f44336', marginTop: '0.25rem' }}>
                          Disabled
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Quick Actions</h3>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <Link to="/channels">
                <button>View All Channels</button>
              </Link>
              <Link to="/trending">
                <button className="secondary">View Trending Videos</button>
              </Link>
            </div>
          </div>

          {/* Getting Started */}
          {channels.length === 0 && (
            <div
              className="card"
              style={{
                marginTop: '2rem',
                backgroundColor: 'var(--primary)',
                color: 'white',
                border: 'none',
              }}
            >
              <h3>Welcome to YouTube Analytics!</h3>
              <p style={{ marginTop: '0.5rem', opacity: 0.9 }}>
                Get started by adding your first YouTube channel. You can track your own channels and analyze
                competitors.
              </p>
              <Link to="/channels">
                <button
                  style={{
                    marginTop: '1rem',
                    backgroundColor: 'white',
                    color: 'var(--primary)',
                  }}
                >
                  Add Your First Channel
                </button>
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  );
}

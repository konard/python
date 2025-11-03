import { Link, Outlet, useLocation } from 'react-router-dom';
import { Home, Youtube, TrendingUp } from 'lucide-react';

export default function Layout() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/channels', label: 'Channels', icon: Youtube },
    { path: '/trending', label: 'Trending', icon: TrendingUp },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: '250px',
          backgroundColor: 'var(--surface)',
          borderRight: '1px solid var(--border)',
          padding: '1.5rem',
        }}
      >
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.5rem', margin: 0 }}>YouTube Analytics</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Health Analytics System
          </p>
        </div>

        <nav>
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                marginBottom: '0.5rem',
                borderRadius: '8px',
                textDecoration: 'none',
                color: isActive(path) ? 'var(--primary)' : 'var(--text-primary)',
                backgroundColor: isActive(path) ? 'var(--background)' : 'transparent',
                fontWeight: isActive(path) ? '600' : '400',
              }}
            >
              <Icon size={20} />
              {label}
            </Link>
          ))}
        </nav>

        <div
          style={{
            marginTop: 'auto',
            paddingTop: '2rem',
            borderTop: '1px solid var(--border)',
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
          }}
        >
          <p>MVP Version 0.1.0</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
            Built with FastAPI + React
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
}

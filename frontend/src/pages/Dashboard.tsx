import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'

const DEMO_MODE = (import.meta.env.VITE_DEMO_MODE || '').toString().toLowerCase() === 'true'

const Dashboard = () => {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    apiCalls: 0,
    revenue: 0,
    activeUsers: 0,
    uptime: 0,
  })

  useEffect(() => {
    const load = async () => {
      if (DEMO_MODE) {
        setStats({
          apiCalls: 45230,
          revenue: 847293,
          activeUsers: 12847,
          uptime: 99.98,
        })
        return
      }
      try {
        const res = await api.get('/api/v1/omni/summary')
        const s = res.data
        setStats({
          apiCalls: Number(s.api_calls_hour ?? 0),
          revenue: Number(String(s.revenue_24h).replace(/[^0-9.]/g, '')) || 0,
          activeUsers: Number(s.active_users ?? 0),
          uptime: Number(String(s.uptime).replace(/[^0-9.]/g, '')) || 0,
        })
      } catch (e) {
        // Fallback to mock data if API unavailable
        setStats({
          apiCalls: 45230,
          revenue: 847293,
          activeUsers: 12847,
          uptime: 99.98,
        })
      }
    }
    load()
  }, [])

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 className="gradient-text" style={styles.title}>
          Welcome back, {user?.full_name}!
        </h1>
        <p style={styles.subtitle}>Here's what's happening with your platform</p>
      </div>

      <div style={styles.statsGrid}>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>📊</div>
          <div style={styles.statValue}>{stats.apiCalls.toLocaleString()}</div>
          <div style={styles.statLabel}>API Calls/Hour</div>
          <div style={styles.statChange}>+12.5% from last hour</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>💰</div>
          <div style={styles.statValue}>€{stats.revenue.toLocaleString()}</div>
          <div style={styles.statLabel}>24h Revenue</div>
          <div style={styles.statChange}>+23.5% from yesterday</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>👥</div>
          <div style={styles.statValue}>{stats.activeUsers.toLocaleString()}</div>
          <div style={styles.statLabel}>Active Users</div>
          <div style={styles.statChange}>+8.2% from last week</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>⚡</div>
          <div style={styles.statValue}>{stats.uptime}%</div>
          <div style={styles.statLabel}>System Uptime</div>
          <div style={styles.statChange}>Last 30 days</div>
        </div>
      </div>

      <div style={styles.grid}>
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>🚀 Quick Actions</h2>
          <div style={styles.actions}>
            <button style={styles.actionBtn}>Create API Key</button>
            <button style={styles.actionBtn}>View Documentation</button>
            <button style={styles.actionBtn}>Invite Team Member</button>
            <button style={styles.actionBtn}>Upgrade Plan</button>
          </div>
        </div>

        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>📈 Recent Activity</h2>
          <div style={styles.activityList}>
            <div style={styles.activityItem}>
              <span style={styles.activityIcon}>✅</span>
              <div>
                <div style={styles.activityText}>API deployment successful</div>
                <div style={styles.activityTime}>2 minutes ago</div>
              </div>
            </div>
            <div style={styles.activityItem}>
              <span style={styles.activityIcon}>💳</span>
              <div>
                <div style={styles.activityText}>Payment processed</div>
                <div style={styles.activityTime}>15 minutes ago</div>
              </div>
            </div>
            <div style={styles.activityItem}>
              <span style={styles.activityIcon}>🔐</span>
              <div>
                <div style={styles.activityText}>Security scan completed</div>
                <div style={styles.activityTime}>1 hour ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    marginBottom: '32px',
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '8px',
  },
  subtitle: {
    color: 'var(--text-secondary)',
    fontSize: '16px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
    marginBottom: '32px',
  },
  statCard: {
    textAlign: 'center',
  },
  statIcon: {
    fontSize: '32px',
    marginBottom: '16px',
  },
  statValue: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: 'var(--primary)',
    marginBottom: '8px',
  },
  statLabel: {
    color: 'var(--text-secondary)',
    fontSize: '14px',
    marginBottom: '8px',
  },
  statChange: {
    color: 'var(--success)',
    fontSize: '12px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
  },
  card: {
    minHeight: '300px',
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '24px',
  },
  actions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  actionBtn: {
    background: 'rgba(0, 221, 255, 0.1)',
    border: '1px solid rgba(0, 221, 255, 0.3)',
    color: 'var(--secondary)',
    padding: '12px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    textAlign: 'left',
    transition: 'all 0.2s',
  },
  activityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  activityItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
  },
  activityIcon: {
    fontSize: '24px',
  },
  activityText: {
    color: 'var(--text)',
    marginBottom: '4px',
  },
  activityTime: {
    color: 'var(--text-secondary)',
    fontSize: '12px',
  },
}

export default Dashboard

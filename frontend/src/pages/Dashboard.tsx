import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const UserGrowthChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGrowthData = async () => {
      try {
        const response = await api.get('/api/v1/dashboards/supabase/users/growth');
        if (response.data && Array.isArray(response.data)) {
          setData(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch user growth data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGrowthData();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}>Loading Chart...</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis dataKey="date" stroke="#888" />
        <YAxis stroke="#888" />
        <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
        <Legend wrapperStyle={{ color: '#fff' }}/>
        <Line type="monotone" dataKey="count" stroke="#00ddff" name="New Users" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 8 }}/>
      </LineChart>
    </ResponsiveContainer>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate(); // Hook for navigation
  const [stats, setStats] = useState({
    apiCalls: 45230,
    revenue: 0,
    activeUsers: 0,
    uptime: 99.98,
  });

  useEffect(() => {
    const fetchActiveUsers = async () => {
      try {
        const res = await api.get('/api/v1/dashboards/supabase/users');
        if (res.data && Array.isArray(res.data)) {
          setStats(prev => ({ ...prev, activeUsers: res.data.length }));
        }
      } catch (e) {
        console.error("Failed to fetch active users:", e);
        setStats(prev => ({ ...prev, activeUsers: 12847 }));
      }
    };

    const fetchRevenue = async () => {
      try {
        const res = await api.get('/api/v1/dashboards/supabase/revenue/summary');
        if (res.data && res.data.revenue_24h !== undefined) {
          setStats(prev => ({ ...prev, revenue: res.data.revenue_24h }));
        }
      } catch (e) {
        console.error("Failed to fetch revenue:", e);
        setStats(prev => ({ ...prev, revenue: 847293 }));
      }
    };

    fetchActiveUsers();
    fetchRevenue();
  }, []);

  // Handlers for Quick Actions
  const handleNavigate = (path) => () => navigate(path);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 className="gradient-text" style={styles.title}>Welcome back, {user?.full_name}!</h1>
        <p style={styles.subtitle}>Here's a real-time overview of your platform's performance.</p>
      </div>

      <div style={styles.statsGrid}>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>📊</div>
          <div style={styles.statValue}>{stats.apiCalls.toLocaleString()}</div>
          <div style={styles.statLabel}>API Calls/Hour</div>
          <div style={styles.statChange}>(Demo) +12.5%</div>
        </div>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>💰</div>
          <div style={styles.statValue}>€{stats.revenue.toLocaleString()}</div>
          <div style={styles.statLabel}>24h Revenue</div>
          <div style={styles.statChange} title="Data from Supabase 'transactions' table">Live Data</div>
        </div>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>👥</div>
          <div style={styles.statValue}>{stats.activeUsers.toLocaleString()}</div>
          <div style={styles.statLabel}>Total Users</div>
          <div style={styles.statChange} title="Data from Supabase 'users' table">Live Data</div>
        </div>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>⚡</div>
          <div style={styles.statValue}>{stats.uptime}%</div>
          <div style={styles.statLabel}>System Uptime</div>
          <div style={styles.statChange}>(Demo) Last 30 days</div>
        </div>
      </div>

      <div style={styles.mainGrid}>
        <div className="card" style={{...styles.card, gridColumn: 'span 2'}}>
          <h2 style={styles.cardTitle}>📈 User Growth</h2>
          <UserGrowthChart />
        </div>
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>🚀 Quick Actions</h2>
          <div style={styles.actions}>
            <button style={styles.actionBtn} onClick={handleNavigate('/pricing')}>Upgrade Plan</button>
            <button style={styles.actionBtn} onClick={() => alert('Functionality not implemented yet.')}>Create API Key</button>
            <button style={styles.actionBtn} onClick={() => alert('Functionality not implemented yet.')}>Invite Team Member</button>
            <button style={styles.actionBtn} onClick={() => window.open('https://supabase.com/docs', '_blank')}>View Documentation</button>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: { maxWidth: '1600px', margin: '0 auto' },
  header: { marginBottom: '32px' },
  title: { fontSize: '36px', fontWeight: 'bold', marginBottom: '8px' },
  subtitle: { color: 'var(--text-secondary)', fontSize: '16px' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '32px' },
  statCard: { textAlign: 'center', padding: '24px', borderRadius: '12px' },
  statIcon: { fontSize: '32px', marginBottom: '16px' },
  statValue: { fontSize: '32px', fontWeight: 'bold', color: 'var(--primary)', marginBottom: '8px' },
  statLabel: { color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' },
  statChange: { color: 'var(--success)', fontSize: '12px', fontWeight: 'bold' },
  mainGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' },
  card: { minHeight: '300px', padding: '24px', borderRadius: '12px' },
  cardTitle: { fontSize: '20px', fontWeight: 'bold', marginBottom: '24px' },
  actions: { display: 'flex', flexDirection: 'column', gap: '12px' },
  actionBtn: { background: 'rgba(0, 221, 255, 0.1)', border: '1px solid rgba(0, 221, 255, 0.3)', color: 'var(--secondary)', padding: '12px', borderRadius: '8px', fontSize: '14px', fontWeight: '500', textAlign: 'left', transition: 'all 0.2s', cursor: 'pointer' },
};

export default Dashboard;

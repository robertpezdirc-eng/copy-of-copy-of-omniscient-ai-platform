import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

const AffiliateDashboard = () => {
  const [stats, setStats] = useState({
    totalClicks: 0,
    totalConversions: 0,
    totalCommission: 0,
    conversionRate: 0,
  })

  useEffect(() => {
    // Mock data - replace with real API calls
    setStats({
      totalClicks: 1247,
      totalConversions: 89,
      totalCommission: 2450.75,
      conversionRate: 7.13,
    })
  }, [])

  return (
    <div style={styles.container}>
      <h1 className="gradient-text" style={styles.title}>
        Affiliate Dashboard
      </h1>

      <div style={styles.statsGrid}>
        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>👆</div>
          <div style={styles.statValue}>{stats.totalClicks.toLocaleString()}</div>
          <div style={styles.statLabel}>Total Clicks</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>✅</div>
          <div style={styles.statValue}>{stats.totalConversions}</div>
          <div style={styles.statLabel}>Conversions</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>💰</div>
          <div style={styles.statValue}>€{stats.totalCommission.toFixed(2)}</div>
          <div style={styles.statLabel}>Total Commission</div>
        </div>

        <div className="card" style={styles.statCard}>
          <div style={styles.statIcon}>📈</div>
          <div style={styles.statValue}>{stats.conversionRate}%</div>
          <div style={styles.statLabel}>Conversion Rate</div>
        </div>
      </div>

      <div style={styles.grid}>
        <div className="card">
          <h2 style={styles.cardTitle}>Your Affiliate Link</h2>
          <input
            type="text"
            value="https://track.omni-ultra.com/ref/AFF12AB34CD"
            readOnly
            style={styles.linkInput}
          />
          <button style={styles.copyBtn}>Copy Link</button>
        </div>

        <div className="card">
          <h2 style={styles.cardTitle}>Current Tier</h2>
          <div style={styles.tierInfo}>
            <div style={styles.tierBadge}>🥇 Gold</div>
            <div style={styles.tierRate}>20% Commission Rate</div>
            <div style={styles.tierProgress}>
              <div style={styles.progressBar}>
                <div style={{ ...styles.progressFill, width: '65%' }} />
              </div>
              <div style={styles.progressText}>€6,500 / €10,000 to Platinum</div>
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
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '32px',
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
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '16px',
  },
  linkInput: {
    width: '100%',
    marginBottom: '12px',
  },
  copyBtn: {
    width: '100%',
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
    color: '#000',
    padding: '12px',
    borderRadius: '8px',
    fontWeight: 'bold',
  },
  tierInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  tierBadge: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: 'var(--primary)',
  },
  tierRate: {
    fontSize: '18px',
    color: 'var(--secondary)',
  },
  tierProgress: {
    marginTop: '8px',
  },
  progressBar: {
    height: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '4px',
    overflow: 'hidden',
    marginBottom: '8px',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
  },
  progressText: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
  },
}

export default AffiliateDashboard

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import AdminAlertsPanel from '@/components/AdminAlertsPanel'

const AdminPanel = () => {
  return (
    <div style={styles.container}>
      <h1 className="gradient-text" style={styles.title}>
        Admin Panel
      </h1>

      <AdminAlertsPanel />

      <div style={styles.grid}>
        <div className="card">
          <h2 style={styles.cardTitle}>System Overview</h2>
          <div style={styles.stats}>
            <div style={styles.stat}>
              <span style={styles.statLabel}>Total Users</span>
              <span style={styles.statValue}>12,847</span>
            </div>
            <div style={styles.stat}>
              <span style={styles.statLabel}>Active Sessions</span>
              <span style={styles.statValue}>3,241</span>
            </div>
            <div style={styles.stat}>
              <span style={styles.statLabel}>Total Revenue</span>
              <span style={styles.statValue}>€847,293</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 style={styles.cardTitle}>Quick Actions</h2>
          <div style={styles.actions}>
            <button style={styles.actionBtn}>Manage Users</button>
            <button style={styles.actionBtn}>View Logs</button>
            <button style={styles.actionBtn}>System Settings</button>
            <button style={styles.actionBtn}>Generate Report</button>
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
    marginTop: '24px',
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '20px',
  },
  stats: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  stat: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
  },
  statLabel: {
    color: 'var(--text-secondary)',
  },
  statValue: {
    color: 'var(--primary)',
    fontWeight: 'bold',
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
  },
}

export default AdminPanel

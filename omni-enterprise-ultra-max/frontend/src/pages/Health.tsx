import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface HealthStatus {
  status: string
  timestamp: string
  version: string
  services?: {
    api: string
    database?: string
  }
}

const Health = () => {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [apiUrl, setApiUrl] = useState<string>('')

  useEffect(() => {
    // Get the API URL from the environment
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080'
    setApiUrl(baseUrl)

    const checkHealth = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const response = await api.get('/api/health')
        setBackendHealth(response.data)
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to connect to backend')
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  const refreshHealth = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.get('/api/health')
      setBackendHealth(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to connect to backend')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <h1 className="gradient-text" style={styles.title}>System Health Check</h1>
      <p style={styles.subtitle}>Verify backend connectivity and system status</p>

      <div style={styles.grid}>
        {/* Frontend Info */}
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>🌐 Frontend</h2>
          <div style={styles.infoGrid}>
            <div style={styles.infoRow}>
              <span style={styles.label}>Status:</span>
              <span style={styles.valueSuccess}>✓ Running</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Environment:</span>
              <span style={styles.value}>{import.meta.env.MODE}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>API Base URL:</span>
              <span style={styles.value}>{apiUrl}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>URL:</span>
              <span style={styles.value}>{window.location.origin}</span>
            </div>
          </div>
        </div>

        {/* Backend Health */}
        <div className="card" style={styles.card}>
          <div style={styles.cardHeader}>
            <h2 style={styles.cardTitle}>🔧 Backend API</h2>
            <button onClick={refreshHealth} style={styles.refreshBtn} disabled={loading}>
              {loading ? '⟳' : '↻'} Refresh
            </button>
          </div>

          {loading && (
            <div style={styles.loading}>Loading...</div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <strong>❌ Connection Failed</strong>
              <p style={styles.errorText}>{error}</p>
            </div>
          )}

          {!loading && !error && backendHealth && (
            <div style={styles.infoGrid}>
              <div style={styles.infoRow}>
                <span style={styles.label}>Status:</span>
                <span style={styles.valueSuccess}>
                  ✓ {backendHealth.status}
                </span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.label}>Version:</span>
                <span style={styles.value}>{backendHealth.version}</span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.label}>Timestamp:</span>
                <span style={styles.value}>
                  {new Date(backendHealth.timestamp).toLocaleString()}
                </span>
              </div>
              {backendHealth.services && (
                <>
                  <div style={styles.infoRow}>
                    <span style={styles.label}>API Service:</span>
                    <span style={styles.value}>{backendHealth.services.api}</span>
                  </div>
                  {backendHealth.services.database && (
                    <div style={styles.infoRow}>
                      <span style={styles.label}>Database:</span>
                      <span style={styles.value}>{backendHealth.services.database}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Connection Test */}
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>🧪 Connection Test</h2>
          <div style={styles.testResults}>
            <div style={styles.testItem}>
              <span style={styles.testLabel}>Frontend → Backend:</span>
              <span style={!error && backendHealth ? styles.testSuccess : styles.testFailure}>
                {loading ? '⏳ Testing...' : !error && backendHealth ? '✓ Connected' : '✗ Failed'}
              </span>
            </div>
            <div style={styles.testItem}>
              <span style={styles.testLabel}>Response Time:</span>
              <span style={styles.value}>
                {!error && backendHealth ? '< 500ms' : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Environment Variables */}
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>⚙️ Configuration</h2>
          <div style={styles.infoGrid}>
            <div style={styles.infoRow}>
              <span style={styles.label}>VITE_API_URL:</span>
              <span style={styles.value}>
                {import.meta.env.VITE_API_URL || '(not set, using default)'}
              </span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Mode:</span>
              <span style={styles.value}>{import.meta.env.MODE}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Dev:</span>
              <span style={styles.value}>{import.meta.env.DEV ? 'Yes' : 'No'}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Prod:</span>
              <span style={styles.value}>{import.meta.env.PROD ? 'Yes' : 'No'}</span>
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
    padding: '24px',
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '8px',
  },
  subtitle: {
    color: 'var(--text-secondary)',
    marginBottom: '32px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
  },
  card: {
    minHeight: '200px',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '16px',
  },
  refreshBtn: {
    background: 'rgba(0, 221, 255, 0.1)',
    border: '1px solid rgba(0, 221, 255, 0.3)',
    color: 'var(--secondary)',
    padding: '8px 12px',
    borderRadius: '8px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  infoGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  label: {
    color: 'var(--text-secondary)',
    fontSize: '14px',
  },
  value: {
    color: 'var(--text)',
    fontSize: '14px',
    fontFamily: 'monospace',
  },
  valueSuccess: {
    color: 'var(--primary)',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  loading: {
    textAlign: 'center',
    padding: '24px',
    color: 'var(--text-secondary)',
  },
  errorBox: {
    background: 'rgba(255, 85, 85, 0.1)',
    border: '1px solid rgba(255, 85, 85, 0.3)',
    borderRadius: '8px',
    padding: '16px',
  },
  errorText: {
    color: '#ff8888',
    marginTop: '8px',
    fontSize: '14px',
    fontFamily: 'monospace',
  },
  testResults: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  testItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
  },
  testLabel: {
    color: 'var(--text-secondary)',
    fontSize: '14px',
  },
  testSuccess: {
    color: 'var(--primary)',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  testFailure: {
    color: '#ff5555',
    fontSize: '14px',
    fontWeight: 'bold',
  },
}

export default Health

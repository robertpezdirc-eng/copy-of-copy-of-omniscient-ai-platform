import { useAuth } from '@/contexts/AuthContext'

const Profile = () => {
  const { user } = useAuth()

  return (
    <div style={styles.container}>
      <h1 className="gradient-text" style={styles.title}>
        Profile Settings
      </h1>

      <div className="card" style={styles.card}>
        <h2 style={styles.cardTitle}>Personal Information</h2>
        
        <div style={styles.grid}>
          <div style={styles.field}>
            <label style={styles.label}>Full Name</label>
            <input type="text" value={user?.full_name || ''} readOnly style={styles.input} />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input type="email" value={user?.email || ''} readOnly style={styles.input} />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Role</label>
            <input type="text" value={user?.role || ''} readOnly style={styles.input} />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Tenant ID</label>
            <input type="text" value={user?.tenant_id || 'N/A'} readOnly style={styles.input} />
          </div>
        </div>
      </div>

      <div className="card" style={styles.card}>
        <h2 style={styles.cardTitle}>Account Status</h2>
        <div style={styles.statusGrid}>
          <div style={styles.statusItem}>
            <span style={styles.statusLabel}>Verification Status</span>
            <span style={user?.is_verified ? styles.statusActive : styles.statusInactive}>
              {user?.is_verified ? '✓ Verified' : '✗ Not Verified'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '32px',
  },
  card: {
    marginBottom: '24px',
  },
  cardTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '24px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: 'var(--text)',
  },
  input: {
    width: '100%',
  },
  statusGrid: {
    display: 'flex',
    gap: '24px',
  },
  statusItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  statusLabel: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
  },
  statusActive: {
    color: 'var(--success)',
    fontWeight: 'bold',
  },
  statusInactive: {
    color: 'var(--error)',
    fontWeight: 'bold',
  },
}

export default Profile

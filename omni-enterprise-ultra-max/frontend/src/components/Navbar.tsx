import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

const Navbar = () => {
  const { user, logout } = useAuth()

  return (
    <nav style={styles.navbar}>
      <div style={styles.container}>
        <Link to="/dashboard" style={styles.logo}>
          <span className="gradient-text" style={styles.logoText}>
            ⚡ Omni Enterprise
          </span>
        </Link>

        <div style={styles.actions}>
          <span style={styles.userInfo}>{user?.email}</span>
          <button onClick={logout} style={styles.logoutBtn}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  navbar: {
    background: 'rgba(26, 26, 46, 0.95)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '16px 24px',
  },
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    textDecoration: 'none',
  },
  logoText: {
    fontSize: '24px',
    fontWeight: 'bold',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  userInfo: {
    color: 'var(--text-secondary)',
    fontSize: '14px',
  },
  logoutBtn: {
    background: 'rgba(255, 85, 85, 0.2)',
    border: '1px solid rgba(255, 85, 85, 0.3)',
    color: '#ff8888',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
}

export default Navbar

import { Link, useLocation } from 'react-router-dom'

const Sidebar = () => {
  const location = useLocation()

  const menuItems = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard' },
    { path: '/profile', icon: '👤', label: 'Profile' },
    { path: '/affiliate', icon: '🤝', label: 'Affiliate' },
    { path: '/pricing', icon: '💎', label: 'Pricing' },
    { path: '/admin', icon: '⚙️', label: 'Admin' },
  ]

  return (
    <aside style={styles.sidebar}>
      <div style={styles.menu}>
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            style={{
              ...styles.menuItem,
              ...(location.pathname === item.path ? styles.menuItemActive : {}),
            }}
          >
            <span style={styles.icon}>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </aside>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  sidebar: {
    width: '240px',
    background: 'rgba(26, 26, 46, 0.5)',
    borderRight: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '24px 0',
  },
  menu: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '0 16px',
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderRadius: '12px',
    color: 'var(--text)',
    textDecoration: 'none',
    transition: 'all 0.2s',
    fontSize: '15px',
  },
  menuItemActive: {
    background: 'rgba(0, 255, 136, 0.1)',
    borderLeft: '3px solid var(--primary)',
    color: 'var(--primary)',
  },
  icon: {
    fontSize: '20px',
  },
}

export default Sidebar

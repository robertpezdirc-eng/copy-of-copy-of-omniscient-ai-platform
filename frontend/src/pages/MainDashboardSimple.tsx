import React from 'react'
import { Link } from 'react-router-dom'

// Enostaven, produkcijsko pripravljen pregled dashboardov.
// Agent lahko prosto doda/uredi URL-je modulov tukaj.
const dashboards = [
  { name: 'Finance', url: '/finance' },
  { name: 'Analytics', url: '/analytics' },
  { name: 'Projects', url: '/projects' },
  { name: 'Sales', url: '/sales' },
  { name: 'Marketing', url: '/marketing' },
  { name: 'Operations', url: '/operations' },
  { name: 'CRM', url: '/module/crm' },
  { name: 'Reports', url: '/module/reports' },
  { name: 'Notifications', url: '/module/notifications' },
  { name: 'Settings', url: '/module/settings' },
  { name: 'Assistant', url: '/module/assistant' },
]

const MainDashboardSimple: React.FC = () => {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Main Dashboard</h1>
      <p>Vse funkcije so klikabilne in delujoče, tako da uporabnik vidi takojšno korist.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
        {dashboards.map((dash, idx) => (
          <Link
            key={idx}
            to={dash.url}
            style={{
              display: 'block',
              padding: '1.5rem',
              backgroundColor: '#f4f4f4',
              borderRadius: '8px',
              textDecoration: 'none',
              color: '#333',
              fontWeight: 'bold',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            {dash.name}
          </Link>
        ))}
      </div>
    </div>
  )
}

export default MainDashboardSimple
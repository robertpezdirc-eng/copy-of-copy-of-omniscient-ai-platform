import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Pricing from './pages/Pricing'
import Profile from './pages/Profile'
import AffiliateDashboard from './pages/AffiliateDashboard'
import AdminPanel from './pages/AdminPanel'
import Health from './pages/Health'
import { BIDashboard } from './pages/BIDashboard'
import PrivateRoute from './components/PrivateRoute'
import MainDashboardSimple from './pages/MainDashboardSimple'
import Finance from './pages/Finance'
import Analytics from './pages/Analytics'
import Projects from './pages/Projects'
import Module from './pages/Module'
import Sales from './pages/Sales'
import Marketing from './pages/Marketing'
import Operations from './pages/Operations'
import CRM from './pages/CRM'
import Reports from './pages/Reports'
import Notifications from './pages/Notifications'
import Settings from './pages/Settings'
import Assistant from './pages/Assistant'
import LiveNow from './pages/LiveNow'

function App() {
  const [healthStatus, setHealthStatus] = useState<'ok' | 'fail' | 'loading'>('loading')
  const [apiUrl] = useState<string>(import.meta.env.VITE_API_URL || 'http://localhost:9000')

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.get('/health')
        if (res.data?.status) {
          setHealthStatus('ok')
        } else {
          setHealthStatus('fail')
        }
      } catch {
        setHealthStatus('fail')
      }
    }
    check()
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <AuthProvider>
      <Router>
        {/* Health badge */}
        <div style={{ position: 'fixed', top: 8, right: 8, zIndex: 1000 }}>
          <div
            title={`Backend: ${apiUrl}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 10px',
              borderRadius: 12,
              fontSize: 12,
              background:
                healthStatus === 'ok'
                  ? 'rgba(0,255,136,0.12)'
                  : healthStatus === 'loading'
                  ? 'rgba(255, 221, 0, 0.12)'
                  : 'rgba(255,85,85,0.12)',
              border:
                healthStatus === 'ok'
                  ? '1px solid rgba(0,255,136,0.35)'
                  : healthStatus === 'loading'
                  ? '1px solid rgba(255,221,0,0.35)'
                  : '1px solid rgba(255,85,85,0.35)',
              color: 'var(--text)'
            }}
          >
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background:
                healthStatus === 'ok'
                  ? '#00ff88'
                  : healthStatus === 'loading'
                  ? '#ffdd00'
                  : '#ff5555'
            }} />
            <span>
              {healthStatus === 'ok' ? 'DEMO OFF · PROD OK' : healthStatus === 'loading' ? 'Checking…' : 'Backend Unreachable'}
            </span>
          </div>
        </div>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1a1a2e',
              color: '#fff',
              border: '1px solid rgba(0, 255, 136, 0.3)',
            },
            success: {
              iconTheme: {
                primary: '#00ff88',
                secondary: '#1a1a2e',
              },
            },
            error: {
              iconTheme: {
                primary: '#ff5555',
                secondary: '#1a1a2e',
              },
            },
          }}
        />
        
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/health" element={<Health />} />
          {/* Public landing and interactive previews */}
          <Route path="/" element={<MainDashboardSimple />} />
          <Route path="/finance" element={<Finance />} />
          <Route path="/finance2" element={<Finance />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/analytics2" element={<Analytics />} />
          <Route path="/sales" element={<Sales />} />
          <Route path="/marketing" element={<Marketing />} />
          <Route path="/operations" element={<Operations />} />
          <Route path="/crm" element={<CRM />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/live" element={<LiveNow />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects2" element={<Projects />} />
          {/* Dynamic module preview */}
          <Route path="/module/:slug" element={<Module />} />
          
          {/* Protected routes */}
          <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/bi-dashboard" element={<BIDashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/affiliate" element={<AffiliateDashboard />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Route>
          
          {/* 404 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

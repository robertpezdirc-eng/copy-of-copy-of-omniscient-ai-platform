import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { ErrorBoundary } from './components/common'
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
import { COLORS } from './constants'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: COLORS.surface,
                color: COLORS.text.primary,
                border: '1px solid rgba(0, 255, 136, 0.3)',
              },
              success: {
                iconTheme: {
                  primary: COLORS.primary,
                  secondary: COLORS.surface,
                },
              },
              error: {
                iconTheme: {
                  primary: COLORS.status.error,
                  secondary: COLORS.surface,
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
            
            {/* Protected routes */}
            <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
    </ErrorBoundary>
  )
}

export default App

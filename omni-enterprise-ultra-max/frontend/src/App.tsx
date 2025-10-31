import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
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
import PrivateRoute from './components/PrivateRoute'

function App() {
  return (
    <AuthProvider>
      <Router>
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
          
          {/* Protected routes */}
          <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
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

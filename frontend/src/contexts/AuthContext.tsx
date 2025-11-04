import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

const DEMO_MODE = (import.meta.env.VITE_DEMO_MODE || '').toString().toLowerCase() === 'true'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id?: string
  is_verified: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token')
      if (DEMO_MODE) {
        // Auto-login in demo mode or restore existing demo session
        if (!token) {
          localStorage.setItem('auth_token', 'demo-token')
        }
        setUser({
          id: 'demo-user-id',
          email: 'demo@example.com',
          full_name: 'Demo User',
          role: 'admin',
          is_verified: true,
          tenant_id: 'demo-tenant',
        })
      } else {
        if (token) {
          try {
            const response = await api.get('/api/v1/auth/me')
            setUser(response.data)
          } catch (error) {
            localStorage.removeItem('auth_token')
          }
        }
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    if (DEMO_MODE) {
      const ok = (email === 'demo' || email === 'demo@example.com') && password === 'demo123'
      if (ok) {
        localStorage.setItem('auth_token', 'demo-token')
        setUser({
          id: 'demo-user-id',
          email: 'demo@example.com',
          full_name: 'Demo User',
          role: 'admin',
          is_verified: true,
          tenant_id: 'demo-tenant',
        })
        toast.success('Logged in as demo user')
        return
      } else {
        toast.error('Invalid demo credentials')
        throw new Error('Invalid demo credentials')
      }
    }

    try {
      const response = await api.post('/api/v1/auth/login', { email, password })
      // Support both token response shapes
      const token: string = response.data?.token || response.data?.access_token

      if (!token) {
        throw new Error('Missing access token in response')
      }

      localStorage.setItem('auth_token', token)

      // Fetch current user profile from backend
      try {
        const me = await api.get('/api/v1/auth/me')
        const meData = me.data
        setUser({
          id: meData.user_id || meData.id || 'unknown',
          email: meData.email || 'unknown@example.com',
          full_name: meData.full_name || meData.name || 'Unknown',
          role: meData.role || 'user',
          is_verified: meData.is_verified ?? true,
          tenant_id: meData.tenant_id,
        })
      } catch (e) {
        // If /me fails, fallback to minimal user
        setUser({
          id: 'unknown',
          email,
          full_name: email,
          role: 'user',
          is_verified: true,
        })
      }

      toast.success('Successfully logged in!')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      throw error
    }
  }

  const register = async (email: string, password: string, fullName: string) => {
    if (DEMO_MODE) {
      toast('Registration is disabled in demo mode', { icon: 'ℹ️' })
      return
    }
    try {
      await api.post('/api/v1/auth/register', {
        email,
        password,
        full_name: fullName,
      })
      
      toast.success('Registration successful! Please login.')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed'
      toast.error(message)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    toast.success('Logged out successfully')
  }

  const refreshUser = async () => {
    if (DEMO_MODE) {
      // No-op in demo mode
      return
    }
    try {
      const response = await api.get('/api/v1/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

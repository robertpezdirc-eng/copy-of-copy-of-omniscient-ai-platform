import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

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
      if (token) {
        try {
          const response = await api.get('/api/v1/auth/me')
          setUser(response.data)
        } catch (error) {
          localStorage.removeItem('auth_token')
        }
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/api/v1/auth/login', { email, password })
      const { token, user: userData } = response.data
      
      localStorage.setItem('auth_token', token)
      setUser(userData)
      toast.success('Successfully logged in!')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      throw error
    }
  }

  const register = async (email: string, password: string, fullName: string) => {
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

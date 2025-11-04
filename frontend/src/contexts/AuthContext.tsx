import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import type { User } from '@/types'
import { API_ENDPOINTS, STORAGE_KEYS, SUCCESS_MESSAGES } from '@/constants'
import { getErrorMessage } from '@/utils'

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
      const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
      if (token) {
        try {
          const response = await api.get(API_ENDPOINTS.AUTH.ME)
          setUser(response.data)
        } catch (error) {
          localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
        }
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, { email, password })
      const { token, user: userData } = response.data
      
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token)
      setUser(userData)
      toast.success('Successfully logged in!')
    } catch (error: any) {
      const message = getErrorMessage(error)
      toast.error(message)
      throw error
    }
  }

  const register = async (email: string, password: string, fullName: string) => {
    try {
      await api.post(API_ENDPOINTS.AUTH.REGISTER, {
        email,
        password,
        full_name: fullName,
      })
      
      toast.success(SUCCESS_MESSAGES.CREATE)
    } catch (error: any) {
      const message = getErrorMessage(error)
      toast.error(message)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
    setUser(null)
    toast.success('Logged out successfully')
  }

  const refreshUser = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.AUTH.ME)
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

/**
 * Omni Enterprise Ultra Max - Application Constants
 * Shared constants and configuration values
 */

import type { AppConfig } from '@/types'

// ============================================================================
// Application Configuration
// ============================================================================

export const APP_CONFIG: AppConfig = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  appName: import.meta.env.VITE_APP_NAME || 'Omni Enterprise Ultra Max',
  appVersion: import.meta.env.VITE_APP_VERSION || '2.0.0',
  environment: (import.meta.env.MODE as 'development' | 'staging' | 'production') || 'development',
  features: {
    enableBIDashboard: true,
    enableAffiliateProgram: true,
    enableRealTimeMetrics: true,
    enableAdvancedAnalytics: true,
  },
}

// ============================================================================
// API Endpoints
// ============================================================================

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    ME: '/api/v1/auth/me',
    REFRESH: '/api/v1/auth/refresh',
    VERIFY_EMAIL: '/api/v1/auth/verify-email',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
  },
  
  // User Management
  USERS: {
    LIST: '/api/v1/users',
    DETAIL: (id: string) => `/api/v1/users/${id}`,
    UPDATE: (id: string) => `/api/v1/users/${id}`,
    DELETE: (id: string) => `/api/v1/users/${id}`,
  },
  
  // Dashboard & Analytics
  ANALYTICS: {
    DASHBOARD: '/api/v1/analytics/dashboard',
    USAGE: '/api/v1/analytics/usage',
    REPORTS: '/api/v1/analytics/reports',
    EXPORT: '/api/v1/analytics/export',
  },
  
  // Billing
  BILLING: {
    INVOICES: '/api/v1/billing/invoices',
    INVOICE_DETAIL: (id: string) => `/api/v1/billing/invoices/${id}`,
    PAYMENT_METHODS: '/api/v1/billing/payment-methods',
    SUBSCRIPTIONS: '/api/v1/billing/subscriptions',
  },
  
  // Affiliate
  AFFILIATE: {
    STATS: '/api/v1/affiliate/stats',
    REFERRALS: '/api/v1/affiliate/referrals',
    COMMISSIONS: '/api/v1/affiliate/commissions',
    LINKS: '/api/v1/affiliate/links',
  },
  
  // Admin
  ADMIN: {
    ALERTS: '/api/v1/admin/alerts',
    METRICS: '/api/v1/admin/metrics',
    USERS: '/api/v1/admin/users',
    SETTINGS: '/api/v1/admin/settings',
  },
  
  // Health & Status
  HEALTH: '/api/health',
  METRICS: '/metrics',
}

// ============================================================================
// UI Constants
// ============================================================================

export const COLORS = {
  primary: '#00ff88',
  secondary: '#8b5cf6',
  accent: '#3b82f6',
  background: '#0a0a0f',
  surface: '#1a1a2e',
  text: {
    primary: '#ffffff',
    secondary: 'rgba(255, 255, 255, 0.7)',
    muted: 'rgba(255, 255, 255, 0.5)',
  },
  status: {
    success: '#00ff88',
    error: '#ff5555',
    warning: '#fbbf24',
    info: '#3b82f6',
  },
}

export const BREAKPOINTS = {
  mobile: 640,
  tablet: 768,
  desktop: 1024,
  wide: 1280,
  ultrawide: 1536,
}

export const ANIMATIONS = {
  duration: {
    fast: 150,
    normal: 300,
    slow: 500,
  },
  easing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
}

// ============================================================================
// Validation Rules
// ============================================================================

export const VALIDATION = {
  email: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Please enter a valid email address',
  },
  password: {
    minLength: 8,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    message: 'Password must be at least 8 characters with uppercase, lowercase, and number',
  },
  username: {
    minLength: 3,
    maxLength: 30,
    pattern: /^[a-zA-Z0-9_-]+$/,
    message: 'Username must be 3-30 characters, alphanumeric with - or _',
  },
}

// ============================================================================
// Pagination & Limits
// ============================================================================

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PER_PAGE: 20,
  PER_PAGE_OPTIONS: [10, 20, 50, 100],
  MAX_PER_PAGE: 100,
}

export const LIMITS = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
  MAX_UPLOAD_SIZE: 50 * 1024 * 1024, // 50MB
  MAX_TEXT_LENGTH: 10000,
  MAX_DESCRIPTION_LENGTH: 500,
  MAX_TITLE_LENGTH: 100,
}

// ============================================================================
// Time & Date Constants
// ============================================================================

export const TIME = {
  SECOND: 1000,
  MINUTE: 60 * 1000,
  HOUR: 60 * 60 * 1000,
  DAY: 24 * 60 * 60 * 1000,
  WEEK: 7 * 24 * 60 * 60 * 1000,
  MONTH: 30 * 24 * 60 * 60 * 1000,
}

export const DATE_FORMATS = {
  SHORT: 'MMM d, yyyy',
  LONG: 'MMMM d, yyyy',
  FULL: 'EEEE, MMMM d, yyyy',
  TIME: 'h:mm a',
  DATETIME: 'MMM d, yyyy h:mm a',
  ISO: "yyyy-MM-dd'T'HH:mm:ss",
}

// ============================================================================
// Storage Keys
// ============================================================================

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  RECENT_SEARCHES: 'recent_searches',
  DASHBOARD_LAYOUT: 'dashboard_layout',
}

// ============================================================================
// Route Paths
// ============================================================================

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  BI_DASHBOARD: '/bi-dashboard',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  
  // Auth
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',
  
  // Features
  AFFILIATE: '/affiliate',
  ADMIN: '/admin',
  PRICING: '/pricing',
  
  // Health
  HEALTH: '/health',
}

// ============================================================================
// WebSocket Events
// ============================================================================

export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  
  // Metrics
  METRICS_UPDATE: 'metrics:update',
  SYSTEM_ALERT: 'system:alert',
  
  // User
  USER_ONLINE: 'user:online',
  USER_OFFLINE: 'user:offline',
  
  // Notifications
  NOTIFICATION: 'notification',
  NOTIFICATION_READ: 'notification:read',
}

// ============================================================================
// Error Messages
// ============================================================================

export const ERROR_MESSAGES = {
  GENERIC: 'An unexpected error occurred. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION: 'Please check your input and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
  TIMEOUT: 'Request timeout. Please try again.',
}

// ============================================================================
// Success Messages
// ============================================================================

export const SUCCESS_MESSAGES = {
  SAVE: 'Changes saved successfully',
  DELETE: 'Item deleted successfully',
  CREATE: 'Item created successfully',
  UPDATE: 'Item updated successfully',
  COPY: 'Copied to clipboard',
  EMAIL_SENT: 'Email sent successfully',
}

// ============================================================================
// Feature Flags
// ============================================================================

export const FEATURES = {
  ENABLE_DARK_MODE: true,
  ENABLE_ANALYTICS: true,
  ENABLE_NOTIFICATIONS: true,
  ENABLE_WEBSOCKET: true,
  ENABLE_FILE_UPLOAD: true,
  ENABLE_EXPORT: true,
  ENABLE_ADVANCED_SEARCH: true,
  ENABLE_TWO_FACTOR_AUTH: false, // Coming soon
  ENABLE_API_PLAYGROUND: false, // Coming soon
}

// ============================================================================
// Subscription Tiers
// ============================================================================

export const SUBSCRIPTION_TIERS = {
  FREE: {
    name: 'Free',
    tier: 'free' as const,
    apiCallsPerMonth: 1000,
    maxTeamMembers: 1,
    maxProjects: 1,
    storageGB: 1,
  },
  STARTER: {
    name: 'Starter',
    tier: 'starter' as const,
    apiCallsPerMonth: 10000,
    maxTeamMembers: 5,
    maxProjects: 10,
    storageGB: 10,
  },
  PROFESSIONAL: {
    name: 'Professional',
    tier: 'professional' as const,
    apiCallsPerMonth: 100000,
    maxTeamMembers: 20,
    maxProjects: 50,
    storageGB: 100,
  },
  ENTERPRISE: {
    name: 'Enterprise',
    tier: 'enterprise' as const,
    apiCallsPerMonth: -1, // Unlimited
    maxTeamMembers: -1, // Unlimited
    maxProjects: -1, // Unlimited
    storageGB: 1000,
  },
}

// ============================================================================
// Icon Mappings
// ============================================================================

export const ICONS = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
  loading: '⏳',
  stats: '📊',
  money: '💰',
  users: '👥',
  bolt: '⚡',
  rocket: '🚀',
  chart: '📈',
  bell: '🔔',
  settings: '⚙️',
  key: '🔑',
  lock: '🔒',
  shield: '🛡️',
}

// ============================================================================
// HTTP Status Codes
// ============================================================================

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
}

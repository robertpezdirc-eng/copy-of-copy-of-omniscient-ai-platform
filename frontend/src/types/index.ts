/**
 * Omni Enterprise Ultra Max - TypeScript Type Definitions
 * Central type definitions for the entire frontend application
 */

// ============================================================================
// User & Authentication Types
// ============================================================================

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  tenant_id?: string
  is_verified: boolean
  created_at?: string
  updated_at?: string
  subscription_tier?: SubscriptionTier
}

export type UserRole = 'admin' | 'user' | 'affiliate' | 'developer'

export interface AuthResponse {
  token: string
  user: User
  expires_at?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  detail: string
  status_code: number
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// ============================================================================
// Dashboard & Analytics Types
// ============================================================================

export interface DashboardStats {
  apiCalls: number
  revenue: number
  activeUsers: number
  uptime: number
}

export interface ActivityItem {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  icon: string
  text: string
  time: string
  timestamp?: string
}

export interface MetricData {
  timestamp: string
  value: number
  label?: string
}

export interface ChartDataPoint {
  name: string
  value: number
  fill?: string
}

// ============================================================================
// Subscription & Billing Types
// ============================================================================

export type SubscriptionTier = 'free' | 'starter' | 'professional' | 'enterprise'

export interface SubscriptionPlan {
  id: string
  name: string
  tier: SubscriptionTier
  price: number
  currency: string
  billing_period: 'monthly' | 'yearly'
  features: string[]
  limits: PlanLimits
  is_popular?: boolean
}

export interface PlanLimits {
  api_calls_per_month: number
  max_team_members: number
  max_projects: number
  storage_gb: number
  support_level: 'community' | 'email' | 'priority' | '24/7'
}

export interface Invoice {
  id: string
  user_id: string
  amount: number
  currency: string
  status: InvoiceStatus
  created_at: string
  due_date: string
  paid_at?: string
  items: InvoiceItem[]
}

export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'overdue' | 'cancelled'

export interface InvoiceItem {
  description: string
  quantity: number
  unit_price: number
  amount: number
}

// ============================================================================
// Affiliate Types
// ============================================================================

export interface AffiliateStats {
  total_clicks: number
  total_referrals: number
  total_earnings: number
  conversion_rate: number
  pending_commission: number
  tier: AffiliateTier
}

export type AffiliateTier = 'bronze' | 'silver' | 'gold' | 'platinum'

export interface AffiliateReferral {
  id: string
  referred_email: string
  status: ReferralStatus
  signup_date: string
  commission_earned: number
  subscription_tier?: SubscriptionTier
}

export type ReferralStatus = 'pending' | 'converted' | 'cancelled'

export interface AffiliateCommission {
  id: string
  amount: number
  status: CommissionStatus
  earned_at: string
  paid_at?: string
  referral_id: string
}

export type CommissionStatus = 'pending' | 'approved' | 'paid' | 'declined'

// ============================================================================
// Admin Types
// ============================================================================

export interface SystemAlert {
  id: string
  type: AlertType
  severity: AlertSeverity
  title: string
  message: string
  timestamp: string
  acknowledged: boolean
  metadata?: Record<string, any>
}

export type AlertType = 
  | 'system' 
  | 'security' 
  | 'performance' 
  | 'billing' 
  | 'user_activity'

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical'

export interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  requests_per_second: number
  error_rate: number
}

export interface UserManagementItem {
  user: User
  last_login?: string
  api_usage: number
  status: 'active' | 'inactive' | 'suspended'
}

// ============================================================================
// BI Dashboard Types
// ============================================================================

export interface BIDashboardData {
  revenue_chart: ChartDataPoint[]
  user_growth: ChartDataPoint[]
  api_usage: ChartDataPoint[]
  geographic_distribution: GeographicData[]
  top_features: FeatureUsageData[]
}

export interface GeographicData {
  country: string
  country_code: string
  users: number
  revenue: number
}

export interface FeatureUsageData {
  feature_name: string
  usage_count: number
  unique_users: number
  revenue_generated: number
}

// ============================================================================
// API & Integration Types
// ============================================================================

export interface APIKey {
  id: string
  name: string
  key: string
  prefix: string
  created_at: string
  last_used_at?: string
  expires_at?: string
  is_active: boolean
  scopes: string[]
}

export interface WebhookConfig {
  id: string
  url: string
  events: WebhookEvent[]
  secret: string
  is_active: boolean
  created_at: string
  last_triggered_at?: string
}

export type WebhookEvent = 
  | 'user.created'
  | 'user.updated'
  | 'payment.success'
  | 'payment.failed'
  | 'subscription.created'
  | 'subscription.cancelled'

// ============================================================================
// Notification Types
// ============================================================================

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  read: boolean
  created_at: string
  link?: string
  metadata?: Record<string, any>
}

export type NotificationType = 
  | 'info' 
  | 'success' 
  | 'warning' 
  | 'error'
  | 'update'
  | 'promotion'

// ============================================================================
// Form & UI Types
// ============================================================================

export interface FormField<T = any> {
  name: string
  label: string
  type: FormFieldType
  value: T
  error?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  options?: SelectOption[]
}

export type FormFieldType = 
  | 'text' 
  | 'email' 
  | 'password' 
  | 'number' 
  | 'select' 
  | 'textarea' 
  | 'checkbox' 
  | 'radio'
  | 'date'

export interface SelectOption {
  label: string
  value: string | number
}

export interface ToastOptions {
  duration?: number
  position?: ToastPosition
  style?: React.CSSProperties
}

export type ToastPosition = 
  | 'top-left' 
  | 'top-center' 
  | 'top-right' 
  | 'bottom-left' 
  | 'bottom-center' 
  | 'bottom-right'

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WebSocketMessage<T = any> {
  type: string
  payload: T
  timestamp: string
}

export interface RealtimeUpdate {
  metric: string
  value: number
  change: number
  trend: 'up' | 'down' | 'stable'
}

// ============================================================================
// Utility Types
// ============================================================================

export type Nullable<T> = T | null

export type Optional<T> = T | undefined

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export interface DateRange {
  start: Date | string
  end: Date | string
}

export interface Pagination {
  page: number
  per_page: number
  total?: number
}

// ============================================================================
// Environment & Config Types
// ============================================================================

export interface AppConfig {
  apiUrl: string
  appName: string
  appVersion: string
  environment: 'development' | 'staging' | 'production'
  features: FeatureFlags
}

export interface FeatureFlags {
  enableBIDashboard: boolean
  enableAffiliateProgram: boolean
  enableRealTimeMetrics: boolean
  enableAdvancedAnalytics: boolean
}

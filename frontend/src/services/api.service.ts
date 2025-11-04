/**
 * Omni Enterprise Ultra Max - API Service Layer
 * Typed API service functions for backend communication
 */

import { api } from '@/lib/api'
import { API_ENDPOINTS } from '@/constants'
import type {
  User,
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  DashboardStats,
  AffiliateStats,
  AffiliateReferral,
  AffiliateCommission,
  AffiliateLink,
  Invoice,
  SystemAlert,
  SystemMetrics,
  SystemSettings,
  PaginatedResponse,
  Pagination,
  UsageAnalytics,
  AnalyticsReport,
  PaymentMethod,
  Subscription,
  HealthCheckResponse,
} from '@/types'

// ============================================================================
// Authentication Service
// ============================================================================

export const authService = {
  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    )
    return response.data
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.REGISTER, data)
  },

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    const response = await api.get<User>(API_ENDPOINTS.AUTH.ME)
    return response.data
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.LOGOUT)
  },

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(API_ENDPOINTS.AUTH.REFRESH)
    return response.data
  },

  /**
   * Verify email address
   */
  async verifyEmail(token: string): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL, { token })
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, { email })
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
      token,
      new_password: newPassword,
    })
  },
}

// ============================================================================
// User Service
// ============================================================================

export const userService = {
  /**
   * List users (admin only)
   */
  async list(pagination?: Pagination): Promise<PaginatedResponse<User>> {
    const response = await api.get<PaginatedResponse<User>>(
      API_ENDPOINTS.USERS.LIST,
      { params: pagination }
    )
    return response.data
  },

  /**
   * Get user by ID
   */
  async getById(id: string): Promise<User> {
    const response = await api.get<User>(API_ENDPOINTS.USERS.DETAIL(id))
    return response.data
  },

  /**
   * Update user
   */
  async update(id: string, data: Partial<User>): Promise<User> {
    const response = await api.put<User>(API_ENDPOINTS.USERS.UPDATE(id), data)
    return response.data
  },

  /**
   * Delete user
   */
  async delete(id: string): Promise<void> {
    await api.delete(API_ENDPOINTS.USERS.DELETE(id))
  },
}

// ============================================================================
// Analytics Service
// ============================================================================

export const analyticsService = {
  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>(
      API_ENDPOINTS.ANALYTICS.DASHBOARD
    )
    return response.data
  },

  /**
   * Get usage analytics
   */
  async getUsage(params?: {
    days?: number
    start_date?: string
    end_date?: string
  }): Promise<UsageAnalytics> {
    const response = await api.get<UsageAnalytics>(API_ENDPOINTS.ANALYTICS.USAGE, { params })
    return response.data
  },

  /**
   * Get analytics reports
   */
  async getReports(type?: string): Promise<AnalyticsReport[]> {
    const response = await api.get<AnalyticsReport[]>(API_ENDPOINTS.ANALYTICS.REPORTS, {
      params: { type },
    })
    return response.data
  },

  /**
   * Export analytics data
   */
  async exportData(format: 'csv' | 'json' | 'excel'): Promise<Blob> {
    const response = await api.post(
      API_ENDPOINTS.ANALYTICS.EXPORT,
      { format },
      { responseType: 'blob' }
    )
    return response.data
  },
}

// ============================================================================
// Billing Service
// ============================================================================

export const billingService = {
  /**
   * List invoices
   */
  async listInvoices(params?: {
    page?: number
    per_page?: number
    status?: string
  }): Promise<PaginatedResponse<Invoice>> {
    const response = await api.get<PaginatedResponse<Invoice>>(
      API_ENDPOINTS.BILLING.INVOICES,
      { params }
    )
    return response.data
  },

  /**
   * Get invoice by ID
   */
  async getInvoice(id: string): Promise<Invoice> {
    const response = await api.get<Invoice>(
      API_ENDPOINTS.BILLING.INVOICE_DETAIL(id)
    )
    return response.data
  },

  /**
   * Pay invoice
   */
  async payInvoice(id: string, paymentMethodId: string): Promise<Invoice> {
    const response = await api.post<Invoice>(
      `${API_ENDPOINTS.BILLING.INVOICE_DETAIL(id)}/pay`,
      { payment_method_id: paymentMethodId }
    )
    return response.data
  },

  /**
   * Get payment methods
   */
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await api.get<PaymentMethod[]>(API_ENDPOINTS.BILLING.PAYMENT_METHODS)
    return response.data
  },

  /**
   * Add payment method
   */
  async addPaymentMethod(data: Partial<PaymentMethod>): Promise<PaymentMethod> {
    const response = await api.post<PaymentMethod>(API_ENDPOINTS.BILLING.PAYMENT_METHODS, data)
    return response.data
  },

  /**
   * Get current subscription
   */
  async getSubscription(): Promise<Subscription> {
    const response = await api.get<Subscription>(API_ENDPOINTS.BILLING.SUBSCRIPTIONS)
    return response.data
  },

  /**
   * Update subscription
   */
  async updateSubscription(tierId: string): Promise<Subscription> {
    const response = await api.put<Subscription>(API_ENDPOINTS.BILLING.SUBSCRIPTIONS, {
      tier_id: tierId,
    })
    return response.data
  },

  /**
   * Cancel subscription
   */
  async cancelSubscription(): Promise<void> {
    await api.delete(API_ENDPOINTS.BILLING.SUBSCRIPTIONS)
  },
}

// ============================================================================
// Affiliate Service
// ============================================================================

export const affiliateService = {
  /**
   * Get affiliate statistics
   */
  async getStats(): Promise<AffiliateStats> {
    const response = await api.get<AffiliateStats>(API_ENDPOINTS.AFFILIATE.STATS)
    return response.data
  },

  /**
   * List referrals
   */
  async listReferrals(params?: Pagination): Promise<PaginatedResponse<AffiliateReferral>> {
    const response = await api.get<PaginatedResponse<AffiliateReferral>>(
      API_ENDPOINTS.AFFILIATE.REFERRALS,
      { params }
    )
    return response.data
  },

  /**
   * List commissions
   */
  async listCommissions(params?: Pagination): Promise<PaginatedResponse<AffiliateCommission>> {
    const response = await api.get<PaginatedResponse<AffiliateCommission>>(
      API_ENDPOINTS.AFFILIATE.COMMISSIONS,
      { params }
    )
    return response.data
  },

  /**
   * Get affiliate links
   */
  async getLinks(): Promise<AffiliateLink[]> {
    const response = await api.get<AffiliateLink[]>(API_ENDPOINTS.AFFILIATE.LINKS)
    return response.data
  },

  /**
   * Generate new affiliate link
   */
  async generateLink(campaign?: string): Promise<AffiliateLink> {
    const response = await api.post<AffiliateLink>(API_ENDPOINTS.AFFILIATE.LINKS, { campaign })
    return response.data
  },
}

// ============================================================================
// Admin Service
// ============================================================================

export const adminService = {
  /**
   * List system alerts
   */
  async listAlerts(params?: {
    severity?: string
    type?: string
    acknowledged?: boolean
  }): Promise<SystemAlert[]> {
    const response = await api.get<SystemAlert[]>(
      API_ENDPOINTS.ADMIN.ALERTS,
      { params }
    )
    return response.data
  },

  /**
   * Acknowledge alert
   */
  async acknowledgeAlert(id: string): Promise<void> {
    await api.post(`${API_ENDPOINTS.ADMIN.ALERTS}/${id}/acknowledge`)
  },

  /**
   * Get system metrics
   */
  async getMetrics(): Promise<SystemMetrics> {
    const response = await api.get<SystemMetrics>(API_ENDPOINTS.ADMIN.METRICS)
    return response.data
  },

  /**
   * List all users (admin view)
   */
  async listUsers(params?: Pagination): Promise<PaginatedResponse<User>> {
    const response = await api.get<PaginatedResponse<User>>(
      API_ENDPOINTS.ADMIN.USERS,
      { params }
    )
    return response.data
  },

  /**
   * Update user status
   */
  async updateUserStatus(
    userId: string,
    status: 'active' | 'inactive' | 'suspended'
  ): Promise<void> {
    await api.put(`${API_ENDPOINTS.ADMIN.USERS}/${userId}/status`, { status })
  },

  /**
   * Get system settings
   */
  async getSettings(): Promise<SystemSettings> {
    const response = await api.get<SystemSettings>(API_ENDPOINTS.ADMIN.SETTINGS)
    return response.data
  },

  /**
   * Update system settings
   */
  async updateSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    const response = await api.put<SystemSettings>(API_ENDPOINTS.ADMIN.SETTINGS, settings)
    return response.data
  },
}

// ============================================================================
// Health Service
// ============================================================================

export const healthService = {
  /**
   * Check API health
   */
  async check(): Promise<HealthCheckResponse> {
    const response = await api.get<HealthCheckResponse>(API_ENDPOINTS.HEALTH)
    return response.data
  },

  /**
   * Get metrics
   */
  async getMetrics(): Promise<Record<string, number>> {
    const response = await api.get<Record<string, number>>(API_ENDPOINTS.METRICS)
    return response.data
  },
}

// ============================================================================
// Export all services
// ============================================================================

export default {
  auth: authService,
  user: userService,
  analytics: analyticsService,
  billing: billingService,
  affiliate: affiliateService,
  admin: adminService,
  health: healthService,
}

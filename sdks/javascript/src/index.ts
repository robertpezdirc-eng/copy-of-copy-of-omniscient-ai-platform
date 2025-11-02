/**
 * Omni Enterprise Ultra Max - JavaScript/TypeScript SDK
 * Official client library for the Omni AI Platform
 * @version 1.0.0
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

export interface OmniClientConfig {
  apiKey: string;
  baseURL?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
}

export class OmniAPIError extends Error {
  statusCode?: number;
  
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'OmniAPIError';
    this.statusCode = statusCode;
  }
}

export class OmniAuthError extends OmniAPIError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'OmniAuthError';
  }
}

export class OmniRateLimitError extends OmniAPIError {
  retryAfter: number;
  
  constructor(message: string, retryAfter: number = 60) {
    super(message, 429);
    this.name = 'OmniRateLimitError';
    this.retryAfter = retryAfter;
  }
}

/**
 * Main Omni client class
 * 
 * @example
 * ```typescript
 * import { OmniClient } from '@omni/client';
 * 
 * const client = new OmniClient({ apiKey: 'your-api-key' });
 * const predictions = await client.intelligence.predictRevenue({ userId: '123' });
 * console.log(predictions);
 * ```
 */
export class OmniClient {
  private client: AxiosInstance;
  private config: Required<OmniClientConfig>;
  
  public intelligence: IntelligenceService;
  public ai: AIService;
  public analytics: AnalyticsService;
  
  constructor(config: OmniClientConfig) {
    this.config = {
      apiKey: config.apiKey,
      baseURL: config.baseURL || 'https://api.omni-platform.com',
      timeout: config.timeout || 30000,
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 1000,
    };
    
    this.client = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'omni-js-sdk/1.0.0',
      },
    });
    
    // Initialize services
    this.intelligence = new IntelligenceService(this);
    this.ai = new AIService(this);
    this.analytics = new AnalyticsService(this);
  }
  
  /**
   * Make HTTP request with retry logic
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        const response = await this.client.request<T>(config);
        return response.data;
      } catch (error) {
        const axiosError = error as AxiosError;
        
        // Handle rate limiting
        if (axiosError.response?.status === 429) {
          const retryAfter = parseInt(
            axiosError.response.headers['x-ratelimit-reset'] || '60'
          );
          throw new OmniRateLimitError(
            `Rate limit exceeded. Retry after ${retryAfter}s`,
            retryAfter
          );
        }
        
        // Handle authentication errors
        if (axiosError.response?.status === 401) {
          throw new OmniAuthError('Invalid or expired API key');
        }
        
        // Handle other errors
        if (axiosError.response && axiosError.response.status >= 400) {
          const errorMsg = (axiosError.response.data as any)?.detail || 'Unknown error';
          throw new OmniAPIError(
            `API error: ${errorMsg}`,
            axiosError.response.status
          );
        }
        
        lastError = axiosError;
        
        // Don't retry on last attempt
        if (attempt < this.config.maxRetries - 1) {
          // Exponential backoff
          await this.sleep(this.config.retryDelay * Math.pow(2, attempt));
        }
      }
    }
    
    throw new OmniAPIError(`Request failed after ${this.config.maxRetries} attempts: ${lastError!.message}`);
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Intelligence Service - AI Intelligence endpoints
 */
export class IntelligenceService {
  constructor(private client: OmniClient) {}
  
  /**
   * Get revenue predictions
   */
  async predictRevenue(params?: { userId?: string; [key: string]: any }): Promise<any> {
    return this.client.request({
      method: 'GET',
      url: '/api/intelligence/predictions/revenue',
      data: params,
    });
  }
  
  /**
   * Get business insights
   */
  async getBusinessInsights(timeframe: string = '30d'): Promise<any> {
    return this.client.request({
      method: 'GET',
      url: `/api/intelligence/insights/business?timeframe=${timeframe}`,
    });
  }
  
  /**
   * Detect anomalies in data
   */
  async detectAnomalies(data: Array<Record<string, any>>): Promise<any> {
    return this.client.request({
      method: 'POST',
      url: '/api/intelligence/anomaly-detection',
      data: { data },
    });
  }
  
  /**
   * Predict customer churn probability
   */
  async predictChurn(userId: string, features: Record<string, any>): Promise<any> {
    return this.client.request({
      method: 'POST',
      url: '/api/intelligence/predict/churn',
      data: { user_id: userId, features },
    });
  }
}

/**
 * AI Service - AI processing endpoints
 */
export class AIService {
  constructor(private client: OmniClient) {}
  
  /**
   * Analyze text with AI
   */
  async analyzeText(text: string, analysisType: string = 'sentiment'): Promise<any> {
    return this.client.request({
      method: 'POST',
      url: '/api/ai/analyze/text',
      data: { text, analysis_type: analysisType },
    });
  }
  
  /**
   * Get available AI models
   */
  async getModels(): Promise<Array<any>> {
    return this.client.request({
      method: 'GET',
      url: '/api/advanced-ai/models',
    });
  }
  
  /**
   * Get details for a specific model
   */
  async getModelDetails(modelName: string): Promise<any> {
    return this.client.request({
      method: 'GET',
      url: `/api/advanced-ai/models/${modelName}`,
    });
  }
}

/**
 * Analytics Service - Analytics endpoints
 */
export class AnalyticsService {
  constructor(private client: OmniClient) {}
  
  /**
   * Get analytics dashboard data
   */
  async getDashboard(dashboardId?: string): Promise<any> {
    const params = dashboardId ? { id: dashboardId } : {};
    return this.client.request({
      method: 'GET',
      url: '/api/analytics/dashboard',
      params,
    });
  }
  
  /**
   * Get real-time metrics
   */
  async getMetrics(metricNames?: string[]): Promise<any> {
    const params = metricNames ? { metrics: metricNames.join(',') } : {};
    return this.client.request({
      method: 'GET',
      url: '/api/analytics/metrics',
      params,
    });
  }
  
  /**
   * Get available dashboard types
   */
  async getDashboardTypes(): Promise<Array<any>> {
    return this.client.request({
      method: 'GET',
      url: '/api/v1/dashboards/types',
    });
  }
}

export default OmniClient;

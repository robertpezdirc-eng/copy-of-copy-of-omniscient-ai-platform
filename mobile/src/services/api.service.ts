import axios, {AxiosInstance, AxiosRequestConfig} from 'axios';
import {API_CONFIG} from '../config/app.config';
import {ApiResponse} from '../types';
import {OfflineQueueService} from './offlineQueue.service';
import NetInfo from '@react-native-community/netinfo';

class ApiService {
  private client: AxiosInstance;
  private offlineQueue: OfflineQueueService;
  private isOnline: boolean = true;

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.GATEWAY_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_CONFIG.API_KEY,
      },
    });

    this.offlineQueue = new OfflineQueueService();
    this.setupInterceptors();
    this.monitorNetworkStatus();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      config => {
        // Add authentication token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      error => Promise.reject(error),
    );

    // Response interceptor
    this.client.interceptors.response.use(
      response => response,
      async error => {
        if (!this.isOnline && error.message === 'Network Error') {
          // Queue request for later
          await this.offlineQueue.addToQueue({
            url: error.config.url,
            method: error.config.method.toUpperCase(),
            data: error.config.data,
            headers: error.config.headers,
          });
          return Promise.reject({
            message: 'Request queued for when connection is restored',
            offline: true,
          });
        }
        return Promise.reject(error);
      },
    );
  }

  private monitorNetworkStatus() {
    NetInfo.addEventListener(state => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected ?? false;

      // If coming back online, process queue
      if (wasOffline && this.isOnline) {
        this.offlineQueue.processQueue(this.client);
      }
    });
  }

  private getAuthToken(): string | null {
    // This would be retrieved from secure storage
    return null;
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get(url, config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'An error occurred',
      };
    }
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post(url, data, config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'An error occurred',
      };
    }
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put(url, data, config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'An error occurred',
      };
    }
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.delete(url, config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'An error occurred',
      };
    }
  }

  // Specific API endpoints
  async healthCheck() {
    return this.get('/health');
  }

  async getSystemMetrics() {
    return this.get('/api/v1/omni/summary');
  }

  async login(email: string, password: string) {
    return this.post('/api/auth/login', {email, password});
  }

  async logout() {
    return this.post('/api/auth/logout');
  }
}

export default new ApiService();

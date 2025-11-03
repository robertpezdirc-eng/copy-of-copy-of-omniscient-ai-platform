export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface OfflineQueueItem {
  id: string;
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  headers?: Record<string, string>;
  timestamp: number;
  retries: number;
}

export interface NotificationPayload {
  title: string;
  body: string;
  data?: Record<string, any>;
}

export interface BiometricAuthResult {
  success: boolean;
  error?: string;
}

export interface NetworkState {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string | null;
}

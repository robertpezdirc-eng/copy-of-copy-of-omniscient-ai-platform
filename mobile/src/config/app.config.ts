// API Configuration
export const API_CONFIG = {
  GATEWAY_URL: 'https://ai-gateway-661612368188.europe-west1.run.app',
  BACKEND_URL: 'https://omni-ultra-backend-prod-661612368188.europe-west1.run.app',
  API_KEY: 'prod-key-omni-2025',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
};

// Push Notification Configuration
export const PUSH_CONFIG = {
  FCM_SENDER_ID: 'YOUR_FCM_SENDER_ID',
  TOPIC: 'omni-updates',
};

// Offline Mode Configuration
export const OFFLINE_CONFIG = {
  SYNC_INTERVAL: 60000, // 1 minute
  MAX_QUEUE_SIZE: 100,
  STORAGE_KEY: '@omni_offline_queue',
};

// Biometric Authentication Configuration
export const BIOMETRIC_CONFIG = {
  PROMPT_TITLE: 'Authenticate',
  PROMPT_MESSAGE: 'Use your biometric credentials to access Omni Enterprise',
  CANCEL_BUTTON: 'Cancel',
  FALLBACK_ENABLED: true,
};

// App Configuration
export const APP_CONFIG = {
  VERSION: '1.0.0',
  BUILD_NUMBER: 1,
  ENVIRONMENT: 'production',
};

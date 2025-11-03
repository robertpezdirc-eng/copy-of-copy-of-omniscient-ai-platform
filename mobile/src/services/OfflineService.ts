/**
 * Offline Mode Service
 * Handles offline data synchronization with Realm
 */

import Realm from 'realm';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import BackgroundFetch from 'react-native-background-fetch';

const UserSchema = {
  name: 'User',
  primaryKey: 'id',
  properties: {
    id: 'string',
    email: 'string',
    name: 'string',
    tenantId: 'string',
    subscriptionTier: 'string',
    lastSync: 'date',
  },
};

const CachedDataSchema = {
  name: 'CachedData',
  primaryKey: 'id',
  properties: {
    id: 'string',
    endpoint: 'string',
    data: 'string',
    timestamp: 'date',
    expiresAt: 'date',
  },
};

const PendingActionSchema = {
  name: 'PendingAction',
  primaryKey: 'id',
  properties: {
    id: 'string',
    type: 'string',
    endpoint: 'string',
    method: 'string',
    data: 'string',
    timestamp: 'date',
    retryCount: 'int',
    synced: 'bool',
  },
};

class OfflineService {
  constructor() {
    this.realm = null;
    this.isOnline = true;
    this.syncInProgress = false;
  }

  async initialize() {
    try {
      this.realm = await Realm.open({
        schema: [UserSchema, CachedDataSchema, PendingActionSchema],
        schemaVersion: 1,
      });

      this.monitorNetworkStatus();
      await this.setupBackgroundSync();

      return { success: true };
    } catch (error) {
      console.error('Error initializing offline service:', error);
      return { success: false, error: error.message };
    }
  }

  monitorNetworkStatus() {
    NetInfo.addEventListener((state) => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected;

      if (!wasOnline && this.isOnline) {
        this.syncPendingActions();
      }
    });
  }

  async setupBackgroundSync() {
    try {
      await BackgroundFetch.configure(
        {
          minimumFetchInterval: 15,
          stopOnTerminate: false,
          startOnBoot: true,
          enableHeadless: true,
        },
        async (taskId) => {
          await this.syncPendingActions();
          await this.cleanupExpiredCache();
          BackgroundFetch.finish(taskId);
        },
        (taskId) => {
          BackgroundFetch.finish(taskId);
        }
      );
    } catch (error) {
      console.error('Error setting up background sync:', error);
    }
  }

  async cacheResponse(endpoint, data, ttlMinutes = 60) {
    if (!this.realm) return;

    try {
      const id = `cache_${endpoint}_${Date.now()}`;
      const expiresAt = new Date(Date.now() + ttlMinutes * 60 * 1000);

      this.realm.write(() => {
        this.realm.create('CachedData', {
          id,
          endpoint,
          data: JSON.stringify(data),
          timestamp: new Date(),
          expiresAt,
        });
      });
    } catch (error) {
      console.error('Error caching response:', error);
    }
  }

  async getCachedResponse(endpoint) {
    if (!this.realm) return null;

    try {
      const cached = this.realm
        .objects('CachedData')
        .filtered('endpoint = $0 AND expiresAt > $1', endpoint, new Date())
        .sorted('timestamp', true)[0];

      if (cached) {
        return JSON.parse(cached.data);
      }

      return null;
    } catch (error) {
      console.error('Error retrieving cached response:', error);
      return null;
    }
  }

  async savePendingAction(type, endpoint, method, data) {
    if (!this.realm) return;

    try {
      const id = `action_${Date.now()}_${Math.random()}`;

      this.realm.write(() => {
        this.realm.create('PendingAction', {
          id,
          type,
          endpoint,
          method,
          data: JSON.stringify(data),
          timestamp: new Date(),
          retryCount: 0,
          synced: false,
        });
      });

      if (this.isOnline) {
        this.syncPendingActions();
      }
    } catch (error) {
      console.error('Error saving pending action:', error);
    }
  }

  async syncPendingActions() {
    if (!this.realm || !this.isOnline || this.syncInProgress) return;

    this.syncInProgress = true;

    try {
      const pendingActions = this.realm
        .objects('PendingAction')
        .filtered('synced = false AND retryCount < 3')
        .sorted('timestamp');

      const apiUrl = await AsyncStorage.getItem('api_url');
      const authToken = await AsyncStorage.getItem('auth_token');

      for (const action of pendingActions) {
        try {
          const response = await fetch(`${apiUrl}${action.endpoint}`, {
            method: action.method,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`,
            },
            body: action.method !== 'GET' ? action.data : undefined,
          });

          if (response.ok) {
            this.realm.write(() => {
              action.synced = true;
            });
          } else {
            this.realm.write(() => {
              action.retryCount += 1;
            });
          }
        } catch (error) {
          this.realm.write(() => {
            action.retryCount += 1;
          });
        }
      }

      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      const oldSyncedActions = this.realm
        .objects('PendingAction')
        .filtered('synced = true AND timestamp < $0', sevenDaysAgo);

      this.realm.write(() => {
        this.realm.delete(oldSyncedActions);
      });

    } catch (error) {
      console.error('Error syncing pending actions:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  async cleanupExpiredCache() {
    if (!this.realm) return;

    try {
      const expiredCache = this.realm
        .objects('CachedData')
        .filtered('expiresAt < $0', new Date());

      this.realm.write(() => {
        this.realm.delete(expiredCache);
      });
    } catch (error) {
      console.error('Error cleaning up expired cache:', error);
    }
  }

  isOffline() {
    return !this.isOnline;
  }

  getPendingActionsCount() {
    if (!this.realm) return 0;
    return this.realm.objects('PendingAction').filtered('synced = false').length;
  }
}

const offlineService = new OfflineService();

export const initializeOfflineSync = () => offlineService.initialize();
export const cacheAPIResponse = (endpoint, data, ttl) => offlineService.cacheResponse(endpoint, data, ttl);
export const getCachedAPIResponse = (endpoint) => offlineService.getCachedResponse(endpoint);
export const savePendingAction = (type, endpoint, method, data) => offlineService.savePendingAction(type, endpoint, method, data);
export const syncPendingActions = () => offlineService.syncPendingActions();

export default offlineService;

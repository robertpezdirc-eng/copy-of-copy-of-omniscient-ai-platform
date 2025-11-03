import AsyncStorage from '@react-native-async-storage/async-storage';
import {AxiosInstance} from 'axios';
import {OFFLINE_CONFIG} from '../config/app.config';
import {OfflineQueueItem} from '../types';

export class OfflineQueueService {
  private queue: OfflineQueueItem[] = [];
  private isProcessing: boolean = false;

  constructor() {
    this.loadQueue();
  }

  async loadQueue() {
    try {
      const queueData = await AsyncStorage.getItem(OFFLINE_CONFIG.STORAGE_KEY);
      if (queueData) {
        this.queue = JSON.parse(queueData);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
    }
  }

  async saveQueue() {
    try {
      await AsyncStorage.setItem(
        OFFLINE_CONFIG.STORAGE_KEY,
        JSON.stringify(this.queue),
      );
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  async addToQueue(item: Omit<OfflineQueueItem, 'id' | 'timestamp' | 'retries'>) {
    const queueItem: OfflineQueueItem = {
      ...item,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
      retries: 0,
    };

    // Check if queue is full
    if (this.queue.length >= OFFLINE_CONFIG.MAX_QUEUE_SIZE) {
      // Remove oldest item
      this.queue.shift();
    }

    this.queue.push(queueItem);
    await this.saveQueue();
  }

  async processQueue(client: AxiosInstance) {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    const itemsToProcess = [...this.queue];
    this.queue = [];

    for (const item of itemsToProcess) {
      try {
        await client.request({
          url: item.url,
          method: item.method,
          data: item.data,
          headers: item.headers,
        });
        console.log(`Successfully processed queued request: ${item.id}`);
      } catch (error) {
        // If failed, re-queue with incremented retry count
        if (item.retries < 3) {
          this.queue.push({
            ...item,
            retries: item.retries + 1,
          });
        } else {
          console.error(`Failed to process request after 3 retries: ${item.id}`);
        }
      }
    }

    await this.saveQueue();
    this.isProcessing = false;
  }

  getQueueLength(): number {
    return this.queue.length;
  }

  async clearQueue() {
    this.queue = [];
    await AsyncStorage.removeItem(OFFLINE_CONFIG.STORAGE_KEY);
  }
}

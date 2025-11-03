import messaging from '@react-native-firebase/messaging';
import notifee, {AndroidImportance, EventType} from '@notifee/react-native';
import {Platform} from 'react-native';
import {PUSH_CONFIG} from '../config/app.config';
import AsyncStorage from '@react-native-async-storage/async-storage';

const FCM_TOKEN_KEY = '@fcm_token';

class PushNotificationService {
  async initialize() {
    // Request permission
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log('Push notification authorization status:', authStatus);
      await this.registerDevice();
      this.setupNotificationHandlers();
    }
  }

  async registerDevice() {
    try {
      // Get FCM token
      const token = await messaging().getToken();
      console.log('FCM Token:', token);

      // Save token locally
      await AsyncStorage.setItem(FCM_TOKEN_KEY, token);

      // Subscribe to topic
      await messaging().subscribeToTopic(PUSH_CONFIG.TOPIC);

      // Send token to backend
      // await apiService.post('/api/notifications/register', { token, platform: Platform.OS });

      // Listen for token refresh
      messaging().onTokenRefresh(async newToken => {
        console.log('FCM Token refreshed:', newToken);
        await AsyncStorage.setItem(FCM_TOKEN_KEY, newToken);
        // await apiService.post('/api/notifications/register', { token: newToken, platform: Platform.OS });
      });
    } catch (error) {
      console.error('Error registering device:', error);
    }
  }

  setupNotificationHandlers() {
    // Handle foreground messages
    messaging().onMessage(async remoteMessage => {
      console.log('Foreground message received:', remoteMessage);
      await this.displayNotification(remoteMessage);
    });

    // Handle background messages
    messaging().setBackgroundMessageHandler(async remoteMessage => {
      console.log('Background message received:', remoteMessage);
    });

    // Handle notification interactions
    notifee.onBackgroundEvent(async ({type, detail}) => {
      if (type === EventType.PRESS) {
        console.log('User pressed notification:', detail.notification);
        // Handle navigation based on notification data
      }
    });

    notifee.onForegroundEvent(({type, detail}) => {
      if (type === EventType.PRESS) {
        console.log('User pressed notification:', detail.notification);
        // Handle navigation based on notification data
      }
    });
  }

  async displayNotification(remoteMessage: any) {
    const channelId = await notifee.createChannel({
      id: 'default',
      name: 'Default Channel',
      importance: AndroidImportance.HIGH,
    });

    await notifee.displayNotification({
      title: remoteMessage.notification?.title,
      body: remoteMessage.notification?.body,
      data: remoteMessage.data,
      android: {
        channelId,
        smallIcon: 'ic_launcher',
        pressAction: {
          id: 'default',
        },
      },
      ios: {
        sound: 'default',
      },
    });
  }

  async sendLocalNotification(title: string, body: string, data?: any) {
    const channelId = await notifee.createChannel({
      id: 'default',
      name: 'Default Channel',
      importance: AndroidImportance.HIGH,
    });

    await notifee.displayNotification({
      title,
      body,
      data,
      android: {
        channelId,
        smallIcon: 'ic_launcher',
        pressAction: {
          id: 'default',
        },
      },
      ios: {
        sound: 'default',
      },
    });
  }

  async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem(FCM_TOKEN_KEY);
  }

  async cancelAllNotifications() {
    await notifee.cancelAllNotifications();
  }
}

export default new PushNotificationService();

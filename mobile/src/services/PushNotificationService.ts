/**
 * Push Notification Service
 * iOS (APNs) and Android (FCM) Support
 */

import messaging from '@react-native-firebase/messaging';
import notifee, { AndroidImportance } from '@notifee/react-native';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

class PushNotificationService {
  constructor() {
    this.fcmToken = null;
  }

  async initialize() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      await this.getFCMToken();
      this.setupMessageHandlers();
      
      if (Platform.OS === 'android') {
        await this.createNotificationChannels();
      }
    }
  }

  async getFCMToken() {
    try {
      const token = await messaging().getToken();
      this.fcmToken = token;
      await AsyncStorage.setItem('fcm_token', token);
      await this.sendTokenToBackend(token);
      return token;
    } catch (error) {
      console.error('Error getting FCM token:', error);
    }
  }

  async sendTokenToBackend(token) {
    try {
      const apiUrl = await AsyncStorage.getItem('api_url');
      const authToken = await AsyncStorage.getItem('auth_token');
      
      await fetch(`${apiUrl}/api/v1/notifications/register-device`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          token,
          platform: Platform.OS,
          device_info: {
            os_version: Platform.Version,
            model: Platform.constants.Model || 'Unknown',
          }
        }),
      });
    } catch (error) {
      console.error('Error sending token to backend:', error);
    }
  }

  setupMessageHandlers() {
    messaging().onMessage(async (remoteMessage) => {
      await this.displayNotification(remoteMessage);
    });

    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      await this.displayNotification(remoteMessage);
    });

    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          this.handleNotificationOpen(remoteMessage);
        }
      });

    messaging().onNotificationOpenedApp((remoteMessage) => {
      this.handleNotificationOpen(remoteMessage);
    });
  }

  async displayNotification(remoteMessage) {
    const channelId = await notifee.createChannel({
      id: 'default',
      name: 'Default Channel',
      importance: AndroidImportance.HIGH,
    });

    await notifee.displayNotification({
      title: remoteMessage.notification?.title || 'New Notification',
      body: remoteMessage.notification?.body || '',
      data: remoteMessage.data,
      android: {
        channelId,
        smallIcon: 'ic_launcher',
        importance: AndroidImportance.HIGH,
        pressAction: {
          id: 'default',
        },
      },
      ios: {
        sound: 'default',
        badgeCount: 1,
      },
    });
  }

  async createNotificationChannels() {
    await notifee.createChannel({
      id: 'default',
      name: 'Default Notifications',
      importance: AndroidImportance.HIGH,
      sound: 'default',
    });

    await notifee.createChannel({
      id: 'alerts',
      name: 'Important Alerts',
      importance: AndroidImportance.HIGH,
      sound: 'alert',
    });
  }

  handleNotificationOpen(remoteMessage) {
    const { data } = remoteMessage;
    console.log('Notification opened:', data);
  }

  async subscribeToTopic(topic) {
    try {
      await messaging().subscribeToTopic(topic);
    } catch (error) {
      console.error('Error subscribing to topic:', error);
    }
  }
}

const pushNotificationService = new PushNotificationService();

export const initializePushNotifications = () => pushNotificationService.initialize();
export const getFCMToken = () => pushNotificationService.getFCMToken();
export const subscribeToTopic = (topic) => pushNotificationService.subscribeToTopic(topic);

export default pushNotificationService;

/**
 * Omni Mobile App - Main Entry Point
 * iOS & Android Support
 */

import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar, Platform } from 'react-native';
import AppNavigator from './navigation/AppNavigator';
import { initializePushNotifications } from './services/PushNotificationService';
import { initializeBiometrics } from './services/BiometricService';
import { initializeOfflineSync } from './services/OfflineService';

const App = () => {
  useEffect(() => {
    const initializeServices = async () => {
      await initializePushNotifications();
      await initializeBiometrics();
      await initializeOfflineSync();
    };

    initializeServices();
  }, []);

  return (
    <NavigationContainer>
      <StatusBar
        barStyle={Platform.OS === 'ios' ? 'dark-content' : 'light-content'}
        backgroundColor="#1e3a8a"
      />
      <AppNavigator />
    </NavigationContainer>
  );
};

export default App;

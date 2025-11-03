import React, {useEffect} from 'react';
import {StatusBar} from 'react-native';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import NetInfo from '@react-native-community/netinfo';
import AppNavigator from './navigation/AppNavigator';
import pushNotificationService from './services/pushNotification.service';
import {useAppStore} from './store/appStore';

function App(): React.JSX.Element {
  const {setNetworkState, notificationsEnabled} = useAppStore();

  useEffect(() => {
    // Initialize push notifications if enabled
    if (notificationsEnabled) {
      pushNotificationService.initialize();
    }

    // Monitor network status
    const unsubscribe = NetInfo.addEventListener(state => {
      setNetworkState({
        isConnected: state.isConnected ?? false,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
      });
    });

    return () => {
      unsubscribe();
    };
  }, [notificationsEnabled, setNetworkState]);

  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      <AppNavigator />
    </GestureHandlerRootView>
  );
}

export default App;

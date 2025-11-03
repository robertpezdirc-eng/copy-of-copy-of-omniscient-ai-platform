import {create} from 'zustand';
import {persist, createJSONStorage} from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {User, NetworkState} from '../types';

interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;

  // Network state
  networkState: NetworkState;
  setNetworkState: (state: NetworkState) => void;

  // Offline queue
  offlineQueueLength: number;
  setOfflineQueueLength: (length: number) => void;

  // Push notifications
  pushToken: string | null;
  setPushToken: (token: string | null) => void;
  notificationsEnabled: boolean;
  setNotificationsEnabled: (enabled: boolean) => void;

  // Biometric auth
  biometricEnabled: boolean;
  setBiometricEnabled: (enabled: boolean) => void;

  // App settings
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // User state
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({user, isAuthenticated: !!user}),
      logout: () => set({user: null, isAuthenticated: false}),

      // Network state
      networkState: {
        isConnected: true,
        isInternetReachable: true,
        type: 'wifi',
      },
      setNetworkState: (networkState) => set({networkState}),

      // Offline queue
      offlineQueueLength: 0,
      setOfflineQueueLength: (offlineQueueLength) => set({offlineQueueLength}),

      // Push notifications
      pushToken: null,
      setPushToken: (pushToken) => set({pushToken}),
      notificationsEnabled: true,
      setNotificationsEnabled: (notificationsEnabled) =>
        set({notificationsEnabled}),

      // Biometric auth
      biometricEnabled: false,
      setBiometricEnabled: (biometricEnabled) => set({biometricEnabled}),

      // App settings
      theme: 'light',
      setTheme: (theme) => set({theme}),
    }),
    {
      name: 'omni-storage',
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist certain fields
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        biometricEnabled: state.biometricEnabled,
        notificationsEnabled: state.notificationsEnabled,
        theme: state.theme,
      }),
    },
  ),
);

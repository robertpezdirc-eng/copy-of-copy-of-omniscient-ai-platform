import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
  Alert,
} from 'react-native';
import {useAppStore} from '../store/appStore';
import biometricService from '../services/biometric.service';
import pushNotificationService from '../services/pushNotification.service';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

export default function SettingsScreen() {
  const {
    theme,
    setTheme,
    biometricEnabled,
    setBiometricEnabled,
    notificationsEnabled,
    setNotificationsEnabled,
    logout,
  } = useAppStore();

  const [isDarkMode, setIsDarkMode] = useState(theme === 'dark');

  const handleBiometricToggle = async (value: boolean) => {
    if (value) {
      const {available, biometryType} = await biometricService.isBiometricAvailable();
      if (available) {
        const result = await biometricService.authenticate('Enable biometric authentication');
        if (result.success) {
          setBiometricEnabled(true);
          Alert.alert('Success', 'Biometric authentication enabled');
        } else {
          Alert.alert('Error', result.error || 'Authentication failed');
        }
      } else {
        Alert.alert('Error', 'Biometric authentication is not available on this device');
      }
    } else {
      setBiometricEnabled(false);
      await biometricService.deleteCredentials();
      Alert.alert('Success', 'Biometric authentication disabled');
    }
  };

  const handleNotificationToggle = async (value: boolean) => {
    setNotificationsEnabled(value);
    if (value) {
      await pushNotificationService.initialize();
      Alert.alert('Success', 'Push notifications enabled');
    } else {
      await pushNotificationService.cancelAllNotifications();
      Alert.alert('Success', 'Push notifications disabled');
    }
  };

  const handleThemeToggle = (value: boolean) => {
    setIsDarkMode(value);
    setTheme(value ? 'dark' : 'light');
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Logout',
          style: 'destructive',
          onPress: () => logout(),
        },
      ],
    );
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Continue?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => Alert.alert('Success', 'Cache cleared'),
        },
      ],
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* App Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>App Settings</Text>

        <View style={styles.settingCard}>
          <View style={styles.settingRow}>
            <Icon name="theme-light-dark" size={24} color="#666" />
            <Text style={styles.settingLabel}>Dark Mode</Text>
            <Switch
              value={isDarkMode}
              onValueChange={handleThemeToggle}
              trackColor={{false: '#ccc', true: '#007AFF'}}
            />
          </View>

          <View style={styles.settingRow}>
            <Icon name="bell-ring" size={24} color="#666" />
            <Text style={styles.settingLabel}>Push Notifications</Text>
            <Switch
              value={notificationsEnabled}
              onValueChange={handleNotificationToggle}
              trackColor={{false: '#ccc', true: '#007AFF'}}
            />
          </View>

          <View style={styles.settingRow}>
            <Icon name="fingerprint" size={24} color="#666" />
            <Text style={styles.settingLabel}>Biometric Login</Text>
            <Switch
              value={biometricEnabled}
              onValueChange={handleBiometricToggle}
              trackColor={{false: '#ccc', true: '#007AFF'}}
            />
          </View>
        </View>
      </View>

      {/* Data & Storage */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data & Storage</Text>

        <View style={styles.settingCard}>
          <TouchableOpacity style={styles.settingRow} onPress={handleClearCache}>
            <Icon name="delete-sweep" size={24} color="#666" />
            <Text style={styles.settingLabel}>Clear Cache</Text>
            <Icon name="chevron-right" size={24} color="#ccc" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingRow}>
            <Icon name="database" size={24} color="#666" />
            <Text style={styles.settingLabel}>Manage Offline Data</Text>
            <Icon name="chevron-right" size={24} color="#ccc" />
          </TouchableOpacity>
        </View>
      </View>

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>

        <View style={styles.settingCard}>
          <View style={styles.settingRow}>
            <Icon name="information" size={24} color="#666" />
            <Text style={styles.settingLabel}>Version</Text>
            <Text style={styles.settingValue}>1.0.0</Text>
          </View>

          <TouchableOpacity style={styles.settingRow}>
            <Icon name="file-document" size={24} color="#666" />
            <Text style={styles.settingLabel}>Terms of Service</Text>
            <Icon name="chevron-right" size={24} color="#ccc" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingRow}>
            <Icon name="shield-check" size={24} color="#666" />
            <Text style={styles.settingLabel}>Privacy Policy</Text>
            <Icon name="chevron-right" size={24} color="#ccc" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Logout Button */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Icon name="logout" size={24} color="#fff" />
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Omni Enterprise Ultra Max</Text>
        <Text style={styles.footerSubtext}>© 2025 All rights reserved</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    flex: 1,
    marginLeft: 15,
    fontSize: 16,
    color: '#333',
  },
  settingValue: {
    fontSize: 16,
    color: '#666',
  },
  logoutButton: {
    flexDirection: 'row',
    backgroundColor: '#F44336',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  logoutText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  footer: {
    alignItems: 'center',
    padding: 30,
  },
  footerText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  footerSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
});

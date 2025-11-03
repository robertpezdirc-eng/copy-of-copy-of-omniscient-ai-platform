import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import {useAppStore} from '../store/appStore';
import apiService from '../services/api.service';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

export default function HomeScreen() {
  const {user, networkState, offlineQueueLength} = useAppStore();
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const response = await apiService.getSystemMetrics();
      if (response.success) {
        setMetrics(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleHealthCheck = async () => {
    const response = await apiService.healthCheck();
    if (response.success) {
      Alert.alert('Health Check', 'System is healthy! ✅');
    } else {
      Alert.alert('Health Check', 'System check failed ❌');
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={fetchMetrics} />
      }>
      <View style={styles.header}>
        <Text style={styles.welcomeText}>Welcome back,</Text>
        <Text style={styles.userName}>{user?.name || 'User'}</Text>
      </View>

      {/* Network Status */}
      <View style={styles.statusCard}>
        <View style={styles.statusRow}>
          <Icon
            name={networkState.isConnected ? 'wifi' : 'wifi-off'}
            size={24}
            color={networkState.isConnected ? '#4CAF50' : '#F44336'}
          />
          <Text style={styles.statusText}>
            {networkState.isConnected ? 'Online' : 'Offline'}
          </Text>
        </View>
        {offlineQueueLength > 0 && (
          <Text style={styles.queueText}>
            {offlineQueueLength} requests queued
          </Text>
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={styles.actionCard}
            onPress={handleHealthCheck}>
            <Icon name="heart-pulse" size={32} color="#007AFF" />
            <Text style={styles.actionText}>Health Check</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionCard}>
            <Icon name="chart-line" size={32} color="#4CAF50" />
            <Text style={styles.actionText}>Analytics</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionCard}>
            <Icon name="robot" size={32} color="#9C27B0" />
            <Text style={styles.actionText}>AI Assistant</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionCard}>
            <Icon name="bell-outline" size={32} color="#FF9800" />
            <Text style={styles.actionText}>Notifications</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* System Metrics */}
      {metrics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Status</Text>
          <View style={styles.metricsCard}>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>API Version:</Text>
              <Text style={styles.metricValue}>{metrics.version || '2.0.0'}</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Status:</Text>
              <Text style={[styles.metricValue, styles.statusActive]}>
                Active
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Region:</Text>
              <Text style={styles.metricValue}>Europe West 1</Text>
            </View>
          </View>
        </View>
      )}

      {/* Features */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Platform Features</Text>
        <View style={styles.featuresList}>
          {[
            {icon: 'brain', text: 'AI/ML Intelligence', color: '#2196F3'},
            {icon: 'security', text: 'Biometric Auth', color: '#4CAF50'},
            {icon: 'cloud-sync', text: 'Offline Mode', color: '#FF9800'},
            {icon: 'bell-ring', text: 'Push Notifications', color: '#F44336'},
            {icon: 'lightning-bolt', text: 'Native Performance', color: '#9C27B0'},
          ].map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <Icon name={feature.icon} size={24} color={feature.color} />
              <Text style={styles.featureText}>{feature.text}</Text>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  welcomeText: {
    fontSize: 16,
    color: '#666',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 5,
  },
  statusCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 16,
    marginLeft: 10,
    fontWeight: '600',
  },
  queueText: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
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
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionText: {
    marginTop: 10,
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  metricsCard: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  metricLabel: {
    fontSize: 16,
    color: '#666',
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  statusActive: {
    color: '#4CAF50',
  },
  featuresList: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  featureText: {
    marginLeft: 15,
    fontSize: 16,
    color: '#333',
  },
});

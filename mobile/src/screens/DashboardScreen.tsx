/**
 * Dashboard Screen - Main App Screen
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getCachedAPIResponse, cacheAPIResponse } from '../services/OfflineService';

const DashboardScreen = () => {
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async (useCache = true) => {
    try {
      const endpoint = '/api/v1/omni/summary';
      
      if (useCache) {
        const cachedData = await getCachedAPIResponse(endpoint);
        if (cachedData) {
          setData(cachedData);
          setOffline(true);
          return;
        }
      }

      const apiUrl = await AsyncStorage.getItem('api_url') || 'https://omni-ultra-backend-prod-661612368188.europe-west1.run.app';
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const apiData = await response.json();
        setData(apiData);
        setOffline(false);
        
        await cacheAPIResponse(endpoint, apiData, 5);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setOffline(true);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData(false);
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {offline && (
        <View style={styles.offlineBanner}>
          <Icon name="cloud-off" size={16} color="#fff" />
          <Text style={styles.offlineText}>Offline Mode - Showing cached data</Text>
        </View>
      )}

      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>Omni Enterprise Ultra Max</Text>
      </View>

      {data && (
        <View>
          <View style={styles.metricsGrid}>
            <MetricCard
              title="Revenue 24h"
              value={data.revenue_24h}
              change={data.revenue_change}
              icon="attach-money"
              color="#10b981"
            />
            <MetricCard
              title="Active Users"
              value={data.active_users.toLocaleString()}
              change={data.users_change}
              icon="people"
              color="#3b82f6"
            />
            <MetricCard
              title="API Calls/Hour"
              value={data.api_calls_hour.toLocaleString()}
              change={data.api_change}
              icon="api"
              color="#8b5cf6"
            />
            <MetricCard
              title="Uptime"
              value={data.uptime}
              change={data.uptime_change}
              icon="check-circle"
              color="#06b6d4"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Services Status</Text>
            <ServiceStatus services={data.services_status} />
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const MetricCard = ({ title, value, change, icon, color }) => (
  <View style={styles.metricCard}>
    <View style={[styles.metricIcon, { backgroundColor: color }]}>
      <Icon name={icon} size={24} color="#fff" />
    </View>
    <Text style={styles.metricTitle}>{title}</Text>
    <Text style={styles.metricValue}>{value}</Text>
    <Text style={[styles.metricChange, { color: change >= 0 ? '#10b981' : '#ef4444' }]}>
      {change >= 0 ? '+' : ''}{change}%
    </Text>
  </View>
);

const ServiceStatus = ({ services }) => (
  <View style={styles.servicesContainer}>
    {Object.entries(services).map(([service, status]) => (
      <View key={service} style={styles.serviceRow}>
        <Icon
          name={status === 'healthy' ? 'check-circle' : 'error'}
          size={20}
          color={status === 'healthy' ? '#10b981' : '#ef4444'}
        />
        <Text style={styles.serviceName}>{service}</Text>
        <Text style={[
          styles.serviceStatus,
          { color: status === 'healthy' ? '#10b981' : '#ef4444' }
        ]}>
          {status}
        </Text>
      </View>
    ))}
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  offlineBanner: {
    backgroundColor: '#f59e0b',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
  },
  offlineText: {
    color: '#fff',
    marginLeft: 8,
    fontSize: 14,
  },
  header: {
    backgroundColor: '#1e3a8a',
    padding: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#93c5fd',
    marginTop: 4,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: '1%',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  metricIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 4,
  },
  metricChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#fff',
    margin: 10,
    borderRadius: 12,
    padding: 16,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  servicesContainer: {
    gap: 12,
  },
  serviceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  serviceName: {
    flex: 1,
    fontSize: 16,
    marginLeft: 12,
    textTransform: 'capitalize',
  },
  serviceStatus: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});

export default DashboardScreen;

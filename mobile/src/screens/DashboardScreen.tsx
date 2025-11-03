import React from 'react';
import {View, Text, StyleSheet, ScrollView} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

export default function DashboardScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>Real-time Analytics & Insights</Text>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <View style={[styles.statCard, {backgroundColor: '#E3F2FD'}]}>
          <Icon name="chart-line" size={32} color="#2196F3" />
          <Text style={styles.statValue}>1.2K</Text>
          <Text style={styles.statLabel}>Active Users</Text>
        </View>

        <View style={[styles.statCard, {backgroundColor: '#F3E5F5'}]}>
          <Icon name="api" size={32} color="#9C27B0" />
          <Text style={styles.statValue}>45K</Text>
          <Text style={styles.statLabel}>API Calls</Text>
        </View>

        <View style={[styles.statCard, {backgroundColor: '#E8F5E9'}]}>
          <Icon name="currency-usd" size={32} color="#4CAF50" />
          <Text style={styles.statValue}>$12.5K</Text>
          <Text style={styles.statLabel}>Revenue</Text>
        </View>

        <View style={[styles.statCard, {backgroundColor: '#FFF3E0'}]}>
          <Icon name="speedometer" size={32} color="#FF9800" />
          <Text style={styles.statValue}>99.9%</Text>
          <Text style={styles.statLabel}>Uptime</Text>
        </View>
      </View>

      {/* Chart Placeholder */}
      <View style={styles.chartCard}>
        <Text style={styles.chartTitle}>Performance Overview</Text>
        <View style={styles.chartPlaceholder}>
          <Icon name="chart-areaspline" size={80} color="#ccc" />
          <Text style={styles.chartText}>Chart visualization coming soon</Text>
        </View>
      </View>

      {/* Recent Activity */}
      <View style={styles.activityCard}>
        <Text style={styles.activityTitle}>Recent Activity</Text>
        {[
          {icon: 'check-circle', text: 'ML model deployed', time: '2 min ago', color: '#4CAF50'},
          {icon: 'alert-circle', text: 'High API usage detected', time: '15 min ago', color: '#FF9800'},
          {icon: 'information', text: 'System update completed', time: '1 hour ago', color: '#2196F3'},
        ].map((activity, index) => (
          <View key={index} style={styles.activityItem}>
            <Icon name={activity.icon} size={24} color={activity.color} />
            <View style={styles.activityContent}>
              <Text style={styles.activityText}>{activity.text}</Text>
              <Text style={styles.activityTime}>{activity.time}</Text>
            </View>
          </View>
        ))}
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 15,
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 10,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  chartCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  chartPlaceholder: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    borderRadius: 10,
  },
  chartText: {
    marginTop: 10,
    color: '#999',
  },
  activityCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  activityTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  activityContent: {
    marginLeft: 15,
    flex: 1,
  },
  activityText: {
    fontSize: 16,
    color: '#333',
  },
  activityTime: {
    fontSize: 12,
    color: '#999',
    marginTop: 3,
  },
});

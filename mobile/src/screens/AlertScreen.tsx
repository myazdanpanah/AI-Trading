import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { THEME } from '../../App';

interface Alert {
  id: string;
  name: string;
  symbol: string;
  type: string;
  threshold: number;
  isActive: boolean;
}

export default function AlertScreen() {
  const [alerts, setAlerts] = useState<Alert[]>([
    { id: '1', name: 'BTC Price Alert', symbol: 'BTC-USDT', type: 'price_above', threshold: 70000, isActive: true },
    { id: '2', name: 'ETH Dip Alert', symbol: 'ETH-USDT', type: 'price_below', threshold: 3000, isActive: true },
    { id: '3', name: 'SOL Buy Signal', symbol: 'SOL-USDT', type: 'signal_buy', threshold: 0, isActive: false },
  ]);

  const toggleAlert = (id: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === id ? { ...alert, isActive: !alert.isActive } : alert
    ));
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Alerts</Text>
        <Text style={styles.subtitle}>Price and signal alerts</Text>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Active Alerts</Text>
          <TouchableOpacity style={styles.addButton}>
            <Text style={styles.addButtonText}>+ Add Alert</Text>
          </TouchableOpacity>
        </View>

        {alerts.map((alert) => (
          <View key={alert.id} style={styles.alertCard}>
            <View style={styles.alertLeft}>
              <View style={[styles.alertIcon, {
                backgroundColor: alert.isActive ? THEME.success + '20' : THEME.card
              }]}>
                <Text style={styles.alertIconText}>🔔</Text>
              </View>
              <View>
                <Text style={styles.alertName}>{alert.name}</Text>
                <Text style={styles.alertDetails}>
                  {alert.symbol} • {alert.type.replace('_', ' ')}
                  {alert.threshold > 0 ? ` • $${alert.threshold.toLocaleString()}` : ''}
                </Text>
              </View>
            </View>
            <Switch
              value={alert.isActive}
              onValueChange={() => toggleAlert(alert.id)}
              trackColor={{ false: THEME.card, true: THEME.success + '80' }}
              thumbColor={alert.isActive ? THEME.success : THEME.textSecondary}
            />
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.background,
  },
  header: {
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: THEME.text,
  },
  subtitle: {
    fontSize: 14,
    color: THEME.textSecondary,
    marginTop: 4,
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  addButton: {
    backgroundColor: THEME.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: THEME.text,
    fontWeight: '600',
  },
  alertCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: THEME.surface,
    borderRadius: 12,
    marginBottom: 12,
  },
  alertLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  alertIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  alertIconText: {
    fontSize: 20,
  },
  alertName: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  alertDetails: {
    fontSize: 12,
    color: THEME.textSecondary,
    marginTop: 4,
  },
});

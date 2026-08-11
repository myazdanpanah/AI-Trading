import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { THEME } from '../../App';
import { fetchSignals, Signal } from '../services/api';

export default function SignalsScreen() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'buy' | 'sell'>('all');

  useEffect(() => {
    loadSignals();
  }, []);

  const loadSignals = async () => {
    try {
      const data = await fetchSignals();
      setSignals(data);
    } catch (error) {
      console.error('Failed to load signals:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadSignals();
    setRefreshing(false);
  };

  const filteredSignals = signals.filter(signal => {
    if (filter === 'all') return true;
    return signal.direction.includes(filter);
  });

  const renderSignal = ({ item }: { item: Signal }) => (
    <View style={styles.signalCard}>
      <View style={styles.signalHeader}>
        <View style={styles.signalLeft}>
          <View style={[styles.directionBadge, {
            backgroundColor: item.direction.includes('buy') ? THEME.success + '20' : THEME.danger + '20'
          }]}>
            <Text style={[styles.directionText, {
              color: item.direction.includes('buy') ? THEME.success : THEME.danger
            }]}>
              {item.direction.toUpperCase()}
            </Text>
          </View>
          <View>
            <Text style={styles.signalSymbol}>{item.symbol}</Text>
            <Text style={styles.signalTime}>{item.timeframe}</Text>
          </View>
        </View>
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>{item.confidence}%</Text>
        </View>
      </View>

      <View style={styles.signalDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Entry</Text>
          <Text style={styles.detailValue}>${item.entry_price.toLocaleString()}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Stop Loss</Text>
          <Text style={[styles.detailValue, { color: THEME.danger }]}>
            ${item.stop_loss?.toLocaleString() || '-'}
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Risk</Text>
          <Text style={[styles.detailValue, {
            color: item.risk_score < 50 ? THEME.success : THEME.danger
          }]}>
            {item.risk_score}
          </Text>
        </View>
      </View>

      {item.take_profit && item.take_profit.length > 0 && (
        <View style={styles.takeProfitRow}>
          <Text style={styles.takeProfitLabel}>Take Profit:</Text>
          {item.take_profit.slice(0, 2).map((tp, idx) => (
            <Text key={idx} style={[styles.takeProfitValue, { color: THEME.success }]}>
              ${tp.toLocaleString()}
            </Text>
          ))}
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Trading Signals</Text>
        <Text style={styles.subtitle}>AI-generated signals</Text>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {(['all', 'buy', 'sell'] as const).map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterTab, filter === f && styles.filterTabActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filteredSignals}
        renderItem={renderSignal}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={THEME.primary} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🎯</Text>
            <Text style={styles.emptyText}>No signals yet</Text>
            <Text style={styles.emptySubtext}>Generate your first signal</Text>
          </View>
        }
      />
    </View>
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
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 8,
  },
  filterTab: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: THEME.surface,
  },
  filterTabActive: {
    backgroundColor: THEME.primary,
  },
  filterText: {
    color: THEME.textSecondary,
    fontWeight: '600',
  },
  filterTextActive: {
    color: THEME.text,
  },
  list: {
    padding: 16,
    paddingBottom: 100,
  },
  signalCard: {
    backgroundColor: THEME.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  signalLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  directionBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  directionText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  signalSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  signalTime: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  confidenceBadge: {
    backgroundColor: THEME.card,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
  },
  confidenceText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: THEME.text,
  },
  signalDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: THEME.border,
  },
  detailRow: {
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: THEME.textSecondary,
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME.text,
  },
  takeProfitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    gap: 8,
  },
  takeProfitLabel: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  takeProfitValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 60,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  emptySubtext: {
    fontSize: 14,
    color: THEME.textSecondary,
    marginTop: 8,
  },
});

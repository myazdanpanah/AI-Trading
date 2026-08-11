import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { THEME } from '../../App';
import PriceCard from '../components/PriceCard';
import MiniChart from '../components/MiniChart';
import { fetchPrices, PriceData } from '../services/api';

const WATCHLIST = [
  { symbol: 'BTC-USDT', name: 'Bitcoin' },
  { symbol: 'ETH-USDT', name: 'Ethereum' },
  { symbol: 'SOL-USDT', name: 'Solana' },
  { symbol: 'BNB-USDT', name: 'BNB' },
  { symbol: 'XRP-USDT', name: 'XRP' },
];

export default function HomeScreen({ navigation }: any) {
  const [prices, setPrices] = useState<PriceData[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC-USDT');

  useEffect(() => {
    loadPrices();
    const interval = setInterval(loadPrices, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  const loadPrices = async () => {
    try {
      const data = await fetchPrices();
      setPrices(data);
    } catch (error) {
      console.error('Failed to load prices:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPrices();
    setRefreshing(false);
  };

  const selectedPrice = prices.find(p => p.symbol === selectedSymbol);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={THEME.primary} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>AI-Trading</Text>
        <Text style={styles.subtitle}>Real-time Crypto Signals</Text>
      </View>

      {/* Portfolio Summary Card */}
      <View style={styles.portfolioCard}>
        <Text style={styles.portfolioLabel}>Portfolio Value</Text>
        <Text style={styles.portfolioValue}>$124,532.80</Text>
        <View style={styles.portfolioChange}>
          <Text style={[styles.portfolioChangeText, { color: THEME.success }]}>
            +$3,245.60 (+2.67%)
          </Text>
        </View>
      </View>

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>156</Text>
          <Text style={styles.statLabel}>Signals</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: THEME.success }]}>65.2%</Text>
          <Text style={styles.statLabel}>Win Rate</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: THEME.success }]}>1.45</Text>
          <Text style={styles.statLabel}>Sharpe</Text>
        </View>
      </View>

      {/* Watchlist */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Watchlist</Text>
          <TouchableOpacity>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        
        {prices.length > 0 ? (
          prices.slice(0, 5).map((price) => (
            <TouchableOpacity
              key={price.symbol}
              style={[styles.watchlistItem, selectedSymbol === price.symbol && styles.watchlistItemActive]}
              onPress={() => setSelectedSymbol(price.symbol)}
            >
              <View style={styles.watchlistLeft}>
                <View style={[styles.iconCircle, { backgroundColor: THEME.primary + '20' }]}>
                  <Text style={styles.iconText}>{price.symbol.charAt(0)}</Text>
                </View>
                <View>
                  <Text style={styles.watchlistSymbol}>{price.symbol.replace('-USDT', '')}/USDT</Text>
                  <Text style={styles.watchlistName}>
                    {WATCHLIST.find(w => w.symbol === price.symbol)?.name || price.symbol}
                  </Text>
                </View>
              </View>
              <View style={styles.watchlistRight}>
                <Text style={styles.watchlistPrice}>${price.price.toLocaleString()}</Text>
                <Text
                  style={[
                    styles.watchlistChange,
                    { color: price.change_24h >= 0 ? THEME.success : THEME.danger },
                  ]}
                >
                  {price.change_24h >= 0 ? '+' : ''}{price.change_24h.toFixed(2)}%
                </Text>
              </View>
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading prices...</Text>
          </View>
        )}
      </View>

      {/* Mini Chart */}
      {selectedPrice && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{selectedPrice.symbol.replace('-USDT', '')}/USDT Chart</Text>
          <MiniChart symbol={selectedPrice.symbol} />
        </View>
      )}

      {/* Recent Signals */}
      <View style={[styles.section, { marginBottom: 100 }]}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Signals</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Signals')}>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.signalItem}>
          <View style={[styles.signalDirection, { backgroundColor: THEME.success + '20' }]}>
            <Text style={[styles.signalDirectionText, { color: THEME.success }]}>BUY</Text>
          </View>
          <View style={styles.signalInfo}>
            <Text style={styles.signalSymbol}>BTC/USDT</Text>
            <Text style={styles.signalTime}>2 hours ago</Text>
          </View>
          <View style={styles.signalConfidence}>
            <Text style={styles.signalConfidenceText}>85%</Text>
          </View>
        </View>

        <View style={styles.signalItem}>
          <View style={[styles.signalDirection, { backgroundColor: THEME.danger + '20' }]}>
            <Text style={[styles.signalDirectionText, { color: THEME.danger }]}>SELL</Text>
          </View>
          <View style={styles.signalInfo}>
            <Text style={styles.signalSymbol}>SOL/USDT</Text>
            <Text style={styles.signalTime}>4 hours ago</Text>
          </View>
          <View style={styles.signalConfidence}>
            <Text style={styles.signalConfidenceText}>72%</Text>
          </View>
        </View>
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
  portfolioCard: {
    margin: 16,
    padding: 20,
    backgroundColor: THEME.surface,
    borderRadius: 16,
  },
  portfolioLabel: {
    fontSize: 14,
    color: THEME.textSecondary,
  },
  portfolioValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: THEME.text,
    marginTop: 8,
  },
  portfolioChange: {
    marginTop: 8,
  },
  portfolioChangeText: {
    fontSize: 16,
    fontWeight: '600',
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 16,
    backgroundColor: THEME.surface,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: THEME.text,
  },
  statLabel: {
    fontSize: 12,
    color: THEME.textSecondary,
    marginTop: 4,
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  seeAll: {
    fontSize: 14,
    color: THEME.primary,
  },
  watchlistItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: THEME.surface,
    borderRadius: 12,
    marginBottom: 8,
  },
  watchlistItemActive: {
    backgroundColor: THEME.card,
    borderWidth: 1,
    borderColor: THEME.primary,
  },
  watchlistLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: THEME.primary,
  },
  watchlistSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  watchlistName: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  watchlistRight: {
    alignItems: 'flex-end',
  },
  watchlistPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  watchlistChange: {
    fontSize: 14,
    marginTop: 4,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    color: THEME.textSecondary,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: THEME.surface,
    borderRadius: 12,
    marginBottom: 8,
  },
  signalDirection: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  signalDirectionText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  signalInfo: {
    flex: 1,
    marginLeft: 12,
  },
  signalSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  signalTime: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  signalConfidence: {
    backgroundColor: THEME.card,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  signalConfidenceText: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME.text,
  },
});

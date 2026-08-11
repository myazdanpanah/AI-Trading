import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { THEME } from '../../App';

interface Position {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

export default function PortfolioScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [positions] = useState<Position[]>([
    { symbol: 'BTC', side: 'long', quantity: 0.5, entryPrice: 65000, currentPrice: 67500, pnl: 1250, pnlPercent: 3.85 },
    { symbol: 'ETH', side: 'long', quantity: 5, entryPrice: 3200, currentPrice: 3450, pnl: 1250, pnlPercent: 7.81 },
    { symbol: 'SOL', side: 'long', quantity: 50, entryPrice: 150, currentPrice: 180, pnl: 1500, pnlPercent: 20 },
  ]);

  const totalValue = positions.reduce((sum, p) => sum + (p.quantity * p.currentPrice), 0);
  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);
  const totalCost = positions.reduce((sum, p) => sum + (p.quantity * p.entryPrice), 0);
  const totalPnlPercent = (totalPnl / totalCost) * 100;

  const onRefresh = async () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={THEME.primary} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Portfolio</Text>
        <Text style={styles.subtitle}>Your positions</Text>
      </View>

      {/* Portfolio Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>Total Balance</Text>
        <Text style={styles.summaryValue}>${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>
        <Text style={[styles.summaryPnl, { color: totalPnl >= 0 ? THEME.success : THEME.danger }]}>
          {totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)} ({totalPnlPercent >= 0 ? '+' : ''}{totalPnlPercent.toFixed(2)}%)
        </Text>
      </View>

      {/* Positions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Positions ({positions.length})</Text>
        
        {positions.map((position, index) => (
          <View key={index} style={styles.positionCard}>
            <View style={styles.positionHeader}>
              <View style={styles.positionLeft}>
                <View style={[styles.positionIcon, {
                  backgroundColor: position.side === 'long' ? THEME.success + '20' : THEME.danger + '20'
                }]}>
                  <Text style={[styles.positionIconText, {
                    color: position.side === 'long' ? THEME.success : THEME.danger
                  }]}>
                    {position.symbol.charAt(0)}
                  </Text>
                </View>
                <View>
                  <Text style={styles.positionSymbol}>{position.symbol}/USDT</Text>
                  <Text style={styles.positionSide}>{position.side.toUpperCase()} {position.quantity}</Text>
                </View>
              </View>
              <View style={styles.positionRight}>
                <Text style={styles.positionValue}>
                  ${(position.quantity * position.currentPrice).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </Text>
                <Text style={[styles.positionPnl, {
                  color: position.pnl >= 0 ? THEME.success : THEME.danger
                }]}>
                  {position.pnl >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%
                </Text>
              </View>
            </View>
            
            <View style={styles.positionDetails}>
              <View style={styles.positionDetail}>
                <Text style={styles.positionDetailLabel}>Entry</Text>
                <Text style={styles.positionDetailValue}>${position.entryPrice.toLocaleString()}</Text>
              </View>
              <View style={styles.positionDetail}>
                <Text style={styles.positionDetailLabel}>Current</Text>
                <Text style={styles.positionDetailValue}>${position.currentPrice.toLocaleString()}</Text>
              </View>
              <View style={styles.positionDetail}>
                <Text style={styles.positionDetailLabel}>P&L</Text>
                <Text style={[styles.positionDetailValue, {
                  color: position.pnl >= 0 ? THEME.success : THEME.danger
                }]}>
                  {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                </Text>
              </View>
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
  summaryCard: {
    margin: 16,
    padding: 24,
    backgroundColor: THEME.surface,
    borderRadius: 16,
  },
  summaryLabel: {
    fontSize: 14,
    color: THEME.textSecondary,
  },
  summaryValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: THEME.text,
    marginTop: 8,
  },
  summaryPnl: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 8,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
    marginBottom: 12,
  },
  positionCard: {
    backgroundColor: THEME.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  positionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  positionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  positionIconText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  positionSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  positionSide: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  positionRight: {
    alignItems: 'flex-end',
  },
  positionValue: {
    fontSize: 18,
    fontWeight: '600',
    color: THEME.text,
  },
  positionPnl: {
    fontSize: 14,
    marginTop: 4,
  },
  positionDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: THEME.border,
  },
  positionDetail: {
    alignItems: 'center',
  },
  positionDetailLabel: {
    fontSize: 12,
    color: THEME.textSecondary,
    marginBottom: 4,
  },
  positionDetailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME.text,
  },
});

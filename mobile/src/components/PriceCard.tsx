import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { THEME } from '../../App';

interface PriceCardProps {
  symbol: string;
  price: number;
  change24h: number;
  onPress?: () => void;
}

export default function PriceCard({ symbol, price, change24h, onPress }: PriceCardProps) {
  const isPositive = change24h >= 0;

  return (
    <TouchableOpacity style={styles.container} onPress={onPress}>
      <View style={styles.left}>
        <View style={[styles.icon, { backgroundColor: THEME.primary + '20' }]}>
          <Text style={styles.iconText}>{symbol.charAt(0)}</Text>
        </View>
        <View>
          <Text style={styles.symbol}>{symbol.replace('-USDT', '')}/USDT</Text>
          <Text style={styles.name}>Tether</Text>
        </View>
      </View>
      <View style={styles.right}>
        <Text style={styles.price}>${price.toLocaleString()}</Text>
        <Text style={[styles.change, { color: isPositive ? THEME.success : THEME.danger }]}>
          {isPositive ? '+' : ''}{change24h.toFixed(2)}%
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: THEME.surface,
    borderRadius: 12,
    marginBottom: 8,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  icon: {
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
  symbol: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  name: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
  right: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME.text,
  },
  change: {
    fontSize: 14,
    marginTop: 4,
  },
});

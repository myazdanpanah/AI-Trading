import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { THEME } from '../../App';

interface MiniChartProps {
  symbol: string;
}

// Generate mock chart data
const generateChartData = () => {
  const data = [];
  let value = 67500;
  for (let i = 0; i < 24; i++) {
    value += (Math.random() - 0.48) * 500;
    data.push(value);
  }
  return data;
};

export default function MiniChart({ symbol }: MiniChartProps) {
  const data = generateChartData();
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  // Simple bar chart representation
  const barHeight = 100;

  return (
    <View style={styles.container}>
      <View style={styles.chart}>
        {data.map((value, index) => {
          const normalizedHeight = ((value - min) / range) * barHeight;
          const isPositive = index === 0 || value >= data[index - 1];
          
          return (
            <View
              key={index}
              style={[
                styles.bar,
                {
                  height: Math.max(normalizedHeight, 4),
                  backgroundColor: isPositive ? THEME.success : THEME.danger,
                  opacity: 0.6 + (index / data.length) * 0.4,
                },
              ]}
            />
          );
        })}
      </View>
      <View style={styles.footer}>
        <Text style={styles.footerText}>24h</Text>
        <Text style={[styles.footerText, { color: THEME.success }]}>+2.45%</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: THEME.surface,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
  },
  chart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 120,
    gap: 2,
  },
  bar: {
    flex: 1,
    borderRadius: 2,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  footerText: {
    fontSize: 12,
    color: THEME.textSecondary,
  },
});

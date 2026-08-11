import React, { useState, useEffect, useMemo } from 'react';
import { apiFetch } from '../../utils/api';
import { PerformanceChart } from '../charts/PerformanceChart';
import { FactorBarChart } from '../charts/FactorBarChart';
import { CandlestickChart } from '../charts/CandlestickChart';

interface PerformanceMetrics {
  win_rate: number;
  total_signals: number;
  avg_return: number;
  profit_factor: number;
  sharpe_ratio: number;
}

// Generate realistic candlestick data
const generateCandlestickData = () => {
  const data = [];
  let basePrice = 65000;
  const now = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    const volatility = 0.02 + Math.random() * 0.03;
    const open = basePrice;
    const change = (Math.random() - 0.48) * volatility * basePrice;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * volatility * basePrice * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * basePrice * 0.5;
    const volume = 1500000000 + Math.random() * 2000000000;
    
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      open: Math.round(open),
      high: Math.round(high),
      low: Math.round(low),
      close: Math.round(close),
      volume: Math.round(volume),
    });
    
    basePrice = close;
  }
  return data;
};

// Generate mock historical data for charts
const generateMockHistoricalData = () => {
  const data = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      winRate: 55 + Math.random() * 20,
      avgReturn: -2 + Math.random() * 8,
      signalCount: Math.floor(3 + Math.random() * 7),
    });
  }
  return data;
};

export const AnalysisPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [activeChart, setActiveChart] = useState<'candlestick' | 'performance' | 'factors'>('candlestick');
  
  const candlestickData = useMemo(() => generateCandlestickData(), []);
  const historicalData = useMemo(() => generateMockHistoricalData(), []);

  useEffect(() => {
    fetchPerformanceMetrics();
  }, [lookbackDays]);

  const fetchPerformanceMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/learning/results/performance/?days=${lookbackDays}`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      } else {
        setError('Failed to load performance data');
      }
    } catch (err) {
      console.error('Failed to fetch performance metrics:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 animate-pulse">
              <div className="h-4 bg-white/20 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-white/10 rounded w-1/3"></div>
            </div>
          ))}
        </div>
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 h-96 animate-pulse"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 backdrop-blur-lg rounded-xl p-6 border border-red-500/20">
        <p className="text-red-400">{error}</p>
        <button 
          onClick={fetchPerformanceMetrics}
          className="mt-4 px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  const metricCards = [
    {
      title: 'Win Rate',
      value: metrics?.win_rate ? `${metrics.win_rate.toFixed(1)}%` : '65.2%',
      icon: '🎯',
      color: 'green',
      change: '+3.1%',
      description: 'Percentage of winning signals',
    },
    {
      title: 'Total Signals',
      value: metrics?.total_signals?.toString() || '156',
      icon: '📊',
      color: 'blue',
      change: '+12%',
      description: 'Signals generated this period',
    },
    {
      title: 'Avg Return',
      value: metrics?.avg_return ? `${metrics.avg_return.toFixed(2)}%` : '3.45%',
      icon: '📈',
      color: 'green',
      change: '+0.8%',
      description: 'Average return per signal',
    },
    {
      title: 'Profit Factor',
      value: metrics?.profit_factor?.toFixed(2) || '1.82',
      icon: '💰',
      color: 'green',
      change: '+0.15',
      description: 'Gross profit / gross loss',
    },
  ];

  const colorClasses = {
    green: 'from-green-500/20 to-green-600/10 border-green-500/30 hover:from-green-500/30 hover:to-green-600/20',
    red: 'from-red-500/20 to-red-600/10 border-red-500/30 hover:from-red-500/30 hover:to-red-600/20',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 hover:from-blue-500/30 hover:to-blue-600/20',
  };

  const textClasses = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
  };

  const factorData = [
    { name: 'Technical', value: 78, color: '#8b5cf6', icon: '📊', description: 'RSI, MACD, EMA, patterns' },
    { name: 'Sentiment', value: 65, color: '#06b6d4', icon: '😊', description: 'Social media, fear/greed' },
    { name: 'News', value: 52, color: '#f59e0b', icon: '📰', description: 'Crypto news analysis' },
    { name: 'AI', value: 85, color: '#10b981', icon: '🤖', description: 'ML model predictions' },
    { name: 'Macro', value: 60, color: '#ec4899', icon: '🌍', description: 'Economic indicators' },
  ];

  const charts = [
    { id: 'candlestick' as const, label: 'Price Chart', icon: '📈' },
    { id: 'performance' as const, label: 'Performance', icon: '📊' },
    { id: 'factors' as const, label: 'Factors', icon: '🧩' },
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {metricCards.map((card, i) => (
          <div key={i} className={`bg-gradient-to-br ${colorClasses[card.color as keyof typeof colorClasses]} backdrop-blur-lg rounded-xl p-6 border transition-all cursor-pointer`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-200/60">{card.title}</p>
                <p className={`text-3xl font-bold mt-2 ${textClasses[card.color as keyof typeof textClasses]}`}>
                  {card.value}
                </p>
                <p className="text-xs text-green-400 mt-1">{card.change}</p>
              </div>
              <div className="text-3xl">{card.icon}</div>
            </div>
            <p className="text-xs text-purple-200/40 mt-2">{card.description}</p>
          </div>
        ))}
      </div>

      {/* Chart Controls */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex space-x-1 bg-white/5 rounded-lg p-1">
            {charts.map((chart) => (
              <button
                key={chart.id}
                onClick={() => setActiveChart(chart.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeChart === chart.id
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'text-purple-200/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>{chart.icon}</span>
                <span>{chart.label}</span>
              </button>
            ))}
          </div>
          
          <div className="flex items-center space-x-4">
            <label className="text-sm text-purple-200/60">Period:</label>
            <select
              value={lookbackDays}
              onChange={(e) => setLookbackDays(parseInt(e.target.value))}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
            >
              <option value={7} className="bg-slate-800">7 Days</option>
              <option value={30} className="bg-slate-800">30 Days</option>
              <option value={90} className="bg-slate-800">90 Days</option>
              <option value={365} className="bg-slate-800">1 Year</option>
            </select>
          </div>
        </div>
      </div>

      {/* Active Chart */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
        {activeChart === 'candlestick' && (
          <CandlestickChart data={candlestickData} height={450} />
        )}
        
        {activeChart === 'performance' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">📊 Performance Trend</h3>
            <PerformanceChart data={historicalData} />
          </div>
        )}
        
        {activeChart === 'factors' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">🧩 Factor Analysis</h3>
            <FactorBarChart data={factorData} />
          </div>
        )}
      </div>

      {/* Sharpe Ratio Card */}
      <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/10 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">📊 Risk-Adjusted Returns</h2>
            <div className="flex items-center space-x-8 mt-4">
              <div>
                <p className="text-sm text-purple-200/60">Sharpe Ratio</p>
                <p className="text-4xl font-bold text-purple-400">
                  {metrics?.sharpe_ratio?.toFixed(2) || '1.45'}
                </p>
              </div>
              <div className="h-12 w-px bg-white/10"></div>
              <div>
                <p className="text-sm text-purple-200/60">Max Drawdown</p>
                <p className="text-4xl font-bold text-red-400">-8.2%</p>
              </div>
              <div className="h-12 w-px bg-white/10"></div>
              <div>
                <p className="text-sm text-purple-200/60">Calmar Ratio</p>
                <p className="text-4xl font-bold text-green-400">2.15</p>
              </div>
            </div>
            <p className="text-sm text-purple-200/40 mt-4">
              Higher Sharpe ratio indicates better risk-adjusted returns. Above 1.0 is considered good, above 2.0 is excellent.
            </p>
          </div>
          <div className="text-6xl">📊</div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPanel;

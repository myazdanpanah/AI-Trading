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
  factor_analysis: Record<string, any>;
  insights: any[];
  days: number;
  status?: string;
}

interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const AnalysisPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [activeChart, setActiveChart] = useState<'candlestick' | 'performance' | 'factors'>('candlestick');
  const [candlestickData, setCandlestickData] = useState<CandleData[]>([]);

  useEffect(() => {
    fetchPerformanceMetrics();
  }, [lookbackDays]);

  useEffect(() => {
    fetchCandlestickData();
  }, []);

  const fetchCandlestickData = async () => {
    try {
      const response = await apiFetch('/market/ticker/?symbol=BTC&days=60');
      if (response.ok) {
        const data = await response.json();
        if (data.candles && data.candles.length > 0) {
          const formatted = data.candles.map((c: any) => ({
            date: new Date(c.date || c.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume || 0,
          }));
          setCandlestickData(formatted);
          return;
        }
      }
    } catch (e) {
      console.warn('Failed to fetch candlestick data:', e);
    }
    // Fallback to generated data
    setCandlestickData(generateFallbackCandlestickData());
  };

  const generateFallbackCandlestickData = (): CandleData[] => {
    const data: CandleData[] = [];
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

  const historicalData = useMemo(() => generateMockHistoricalData(), []);

  const fetchPerformanceMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/feedback/analysis/results/performance/?days=${lookbackDays}`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      } else {
        // Fallback: set default metrics
        setMetrics({
          win_rate: 0,
          total_signals: 0,
          avg_return: 0,
          profit_factor: 0,
          sharpe_ratio: 0,
          factor_analysis: {},
          insights: [],
          days: lookbackDays,
          status: 'no_data',
        });
        setError(null);
      }
    } catch (err) {
      console.error('Failed to fetch performance metrics:', err);
      setMetrics({
        win_rate: 0,
        total_signals: 0,
        avg_return: 0,
        profit_factor: 0,
        sharpe_ratio: 0,
        factor_analysis: {},
        insights: [],
        days: lookbackDays,
        status: 'error',
      });
      setError(null);
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

  const winRate = metrics?.win_rate || 0;
  const totalSignals = metrics?.total_signals || 0;
  const avgReturn = metrics?.avg_return || 0;
  const profitFactor = metrics?.profit_factor || 0;

  const metricCards = [
    {
      title: 'Win Rate',
      value: totalSignals > 0 ? `${winRate.toFixed(1)}%` : 'No data yet',
      icon: '🎯',
      color: winRate >= 55 ? 'green' : winRate > 0 ? 'yellow' : 'blue',
      change: totalSignals > 0 ? `Over ${lookbackDays}d` : 'Generate signals first',
      description: 'Percentage of winning signals',
    },
    {
      title: 'Total Signals',
      value: totalSignals.toString(),
      icon: '📊',
      color: 'blue',
      change: totalSignals > 0 ? `${lookbackDays}d period` : 'Pending',
      description: 'Signals generated this period',
    },
    {
      title: 'Avg Return',
      value: totalSignals > 0 ? `${avgReturn.toFixed(2)}%` : 'No data yet',
      icon: '📈',
      color: avgReturn > 0 ? 'green' : avgReturn < 0 ? 'red' : 'blue',
      change: totalSignals > 0 ? (avgReturn > 0 ? 'Positive' : 'Negative') : 'Pending',
      description: 'Average return per signal',
    },
    {
      title: 'Profit Factor',
      value: totalSignals > 0 ? profitFactor.toFixed(2) : 'No data yet',
      icon: '💰',
      color: profitFactor > 1 ? 'green' : 'red',
      change: totalSignals > 0 ? (profitFactor > 1 ? 'Profitable' : 'Unprofitable') : 'Pending',
      description: 'Gross profit / gross loss',
    },
  ];

  const colorClasses: Record<string, string> = {
    green: 'from-green-500/20 to-green-600/10 border-green-500/30 hover:from-green-500/30 hover:to-green-600/20',
    red: 'from-red-500/20 to-red-600/10 border-red-500/30 hover:from-red-500/30 hover:to-red-600/20',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 hover:from-blue-500/30 hover:to-blue-600/20',
    yellow: 'from-yellow-500/20 to-yellow-600/10 border-yellow-500/30 hover:from-yellow-500/30 hover:to-yellow-600/20',
  };

  const textClasses: Record<string, string> = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
    yellow: 'text-yellow-400',
  };

  const factorData = [
    { name: 'Technical', value: metrics?.factor_analysis?.technical?.win_rate ? Math.round(metrics.factor_analysis.technical.win_rate) : 0, color: '#8b5cf6', icon: '📊', description: 'RSI, MACD, EMA, VWAP, Ichimoku' },
    { name: 'Sentiment', value: metrics?.factor_analysis?.sentiment?.win_rate ? Math.round(metrics.factor_analysis.sentiment.win_rate) : 0, color: '#06b6d4', icon: '😊', description: 'Fear & Greed, social media' },
    { name: 'News', value: metrics?.factor_analysis?.news?.win_rate ? Math.round(metrics.factor_analysis.news.win_rate) : 0, color: '#f59e0b', icon: '📰', description: 'Crypto news analysis' },
    { name: 'AI', value: metrics?.factor_analysis?.ai?.win_rate ? Math.round(metrics.factor_analysis.ai.win_rate) : 0, color: '#10b981', icon: '🤖', description: 'ML model predictions' },
    { name: 'Macro', value: metrics?.factor_analysis?.macro?.win_rate ? Math.round(metrics.factor_analysis.macro.win_rate) : 0, color: '#ec4899', icon: '🌍', description: 'Economic indicators' },
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
          <div key={i} className={`bg-gradient-to-br ${colorClasses[card.color]} backdrop-blur-lg rounded-xl p-6 border transition-all cursor-pointer`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-200/60">{card.title}</p>
                <p className={`text-3xl font-bold mt-2 ${textClasses[card.color]}`}>
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
          <CandlestickChart data={candlestickData.length > 0 ? candlestickData : generateFallbackCandlestickData()} height={450} />
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

      {/* Insights Section */}
      {metrics?.insights && metrics.insights.length > 0 && (
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">💡 AI Insights</h3>
          <div className="space-y-3">
            {metrics.insights.map((insight: any, i: number) => (
              <div key={i} className="bg-white/5 rounded-lg p-4 border border-white/5">
                <p className="text-sm text-purple-200/80">{insight.description || insight.text || JSON.stringify(insight)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sharpe Ratio Card */}
      <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/10 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">📊 Risk-Adjusted Returns</h2>
            <div className="flex items-center space-x-8 mt-4">
              <div>
                <p className="text-sm text-purple-200/60">Sharpe Ratio</p>
                <p className="text-4xl font-bold text-purple-400">
                  {metrics?.sharpe_ratio ? metrics.sharpe_ratio.toFixed(2) : '0.00'}
                </p>
              </div>
              <div className="h-12 w-px bg-white/10"></div>
              <div>
                <p className="text-sm text-purple-200/60">Lookback Period</p>
                <p className="text-4xl font-bold text-blue-400">{lookbackDays}d</p>
              </div>
              <div className="h-12 w-px bg-white/10"></div>
              <div>
                <p className="text-sm text-purple-200/60">Profit Factor</p>
                <p className={`text-4xl font-bold ${profitFactor > 1 ? 'text-green-400' : 'text-red-400'}`}>
                  {profitFactor > 0 ? profitFactor.toFixed(2) : '0.00'}
                </p>
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

import React, { useState, useEffect, useMemo } from 'react';
import { apiFetch } from '../../utils/api';
import { PerformanceChart } from '../charts/PerformanceChart';
import { FactorBarChart } from '../charts/FactorBarChart';
import { CandlestickChart } from '../charts/CandlestickChart';

interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface AnalysisResult {
  symbol: string;
  current_price: number;
  data_source: string;
  data_points: number;
  regime: {
    composite: { score: number; zone: string; guidance: string };
    exposure: { posture: string; max_exposure: number };
    components: Record<string, { label: string; score: number; signal: string }>;
  };
  technical: {
    overall_score: number;
    trend: { score: number; signal: string };
    momentum: { score: number; signal: string; rsi: number };
    volatility: { score: number; signal: string };
    vwap: { value: number; deviation: number; signal: string };
    ichimoku: { signal: string; cloud_color: string };
  };
  verdict: {
    signal: string;
    combined_score: number;
    regime_score: number;
    technical_score: number;
  };
  execution_time_ms: number;
}

export const AnalysisPanel: React.FC = () => {
  const [candlestickData, setCandlestickData] = useState<CandleData[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [activeChart, setActiveChart] = useState<'candlestick' | 'performance' | 'factors'>('candlestick');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');

  useEffect(() => {
    fetchData();
  }, [selectedSymbol, lookbackDays]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch candle data
      const candleRes = await apiFetch(`/market/candles/live/?symbol=${selectedSymbol}&days=${lookbackDays}`);
      if (candleRes.ok) {
        const candleData = await candleRes.json();
        if (candleData.candles) {
          setCandlestickData(candleData.candles);
        }
      }

      // Fetch full analysis
      const analysisRes = await apiFetch(`/skills/full-analysis/?symbol=${selectedSymbol}&account_size=10000`);
      if (analysisRes.ok) {
        const analysisData = await analysisRes.json();
        setAnalysis(analysisData);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const historicalData = useMemo(() => {
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
  }, []);

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

  // Calculate analysis metrics
  const regimeScore = analysis?.regime?.composite?.score || 50;
  const techScore = analysis?.technical?.overall_score || 50;
  const trendScore = analysis?.technical?.trend?.score || 50;
  const momentumScore = analysis?.technical?.momentum?.score || 50;
  const volatilityScore = analysis?.technical?.volatility?.score || 50;

  const metricCards = [
    {
      title: 'Regime Score',
      value: regimeScore.toFixed(1),
      icon: '🌐',
      color: regimeScore >= 60 ? 'green' : regimeScore >= 40 ? 'yellow' : 'red',
      change: analysis?.regime?.composite?.zone || 'N/A',
      description: 'Market regime analysis',
    },
    {
      title: 'Technical Score',
      value: techScore.toFixed(1),
      icon: '📊',
      color: techScore >= 60 ? 'green' : techScore >= 40 ? 'yellow' : 'red',
      change: analysis?.technical?.trend?.signal || 'N/A',
      description: 'Technical indicator analysis',
    },
    {
      title: 'Signal',
      value: analysis?.verdict?.signal || 'HOLD',
      icon: '🎯',
      color: analysis?.verdict?.signal?.includes('BUY') ? 'green' : analysis?.verdict?.signal?.includes('SELL') ? 'red' : 'yellow',
      change: `Score: ${analysis?.verdict?.combined_score?.toFixed(1) || 'N/A'}`,
      description: 'Combined verdict',
    },
    {
      title: 'RSI',
      value: analysis?.technical?.momentum?.rsi?.toFixed(1) || 'N/A',
      icon: '📈',
      color: (analysis?.technical?.momentum?.rsi || 50) < 30 ? 'green' : (analysis?.technical?.momentum?.rsi || 50) > 70 ? 'red' : 'blue',
      change: analysis?.technical?.momentum?.signal || 'N/A',
      description: 'Relative Strength Index',
    },
  ];

  const colorClasses: Record<string, string> = {
    green: 'from-green-500/20 to-green-600/10 border-green-500/30',
    red: 'from-red-500/20 to-red-600/10 border-red-500/30',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    yellow: 'from-yellow-500/20 to-yellow-600/10 border-yellow-500/30',
  };

  const textClasses: Record<string, string> = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
    yellow: 'text-yellow-400',
  };

  const factorData = [
    { name: 'Regime', value: Math.round(regimeScore), color: '#8b5cf6', icon: '🌐', description: 'Market regime analysis' },
    { name: 'Trend', value: Math.round(trendScore), color: '#06b6d4', icon: '📈', description: 'EMA alignment & ADX' },
    { name: 'Momentum', value: Math.round(momentumScore), color: '#f59e0b', icon: '⚡', description: 'RSI, MACD, Stochastic' },
    { name: 'Volatility', value: Math.round(volatilityScore), color: '#10b981', icon: '📊', description: 'ATR, Bollinger Bands' },
    { name: 'Overall', value: Math.round(techScore), color: '#ec4899', icon: '🎯', description: 'Combined technical' },
  ];

  const charts = [
    { id: 'candlestick' as const, label: 'Price Chart', icon: '📈' },
    { id: 'performance' as const, label: 'Performance', icon: '📊' },
    { id: 'factors' as const, label: 'Factors', icon: '🧩' },
  ];

  return (
    <div className="space-y-6">
      {/* Symbol Selector */}
      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          {['BTC', 'ETH', 'SOL', 'BNB', 'XRP'].map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                selectedSymbol === sym
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
              }`}
            >
              {sym}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-sm text-purple-200/60">Period:</span>
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(parseInt(e.target.value))}
            className="px-3 py-1.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value={7} className="bg-slate-800">7 Days</option>
            <option value={30} className="bg-slate-800">30 Days</option>
            <option value={90} className="bg-slate-800">90 Days</option>
            <option value={365} className="bg-slate-800">1 Year</option>
          </select>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {metricCards.map((card, i) => (
          <div key={i} className={`bg-gradient-to-br ${colorClasses[card.color]} backdrop-blur-lg rounded-xl p-5 border transition-all`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-200/60">{card.title}</p>
                <p className={`text-3xl font-bold mt-2 ${textClasses[card.color]}`}>
                  {card.value}
                </p>
                <p className="text-xs text-gray-400 mt-1">{card.change}</p>
              </div>
              <div className="text-3xl">{card.icon}</div>
            </div>
            <p className="text-xs text-purple-200/40 mt-2">{card.description}</p>
          </div>
        ))}
      </div>

      {/* Chart Controls */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
        <div className="flex space-x-1 bg-white/5 rounded-lg p-1 w-fit">
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
      </div>

      {/* Active Chart */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
        {activeChart === 'candlestick' && (
          <CandlestickChart data={candlestickData.length > 0 ? candlestickData : []} height={450} />
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

      {/* Regime Components Detail */}
      {analysis?.regime?.components && (
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">🌐 Regime Components</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(analysis.regime.components).map(([key, comp]) => (
              <div key={key} className="bg-white/5 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">{comp.label}</div>
                <div className="text-2xl font-bold" style={{ color: comp.score >= 60 ? '#10b981' : comp.score >= 40 ? '#f59e0b' : '#ef4444' }}>
                  {comp.score.toFixed(1)}
                </div>
                <div className="text-xs text-gray-500 mt-1">{comp.signal}</div>
                <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
                  <div className="h-1.5 rounded-full" style={{ width: `${comp.score}%`, backgroundColor: comp.score >= 60 ? '#10b981' : comp.score >= 40 ? '#f59e0b' : '#ef4444' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical Indicators Detail */}
      {analysis?.technical && (
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">📈 Technical Indicators</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400 mb-1">Trend</div>
              <div className="text-3xl font-bold" style={{ color: trendScore >= 60 ? '#10b981' : trendScore >= 40 ? '#f59e0b' : '#ef4444' }}>
                {trendScore.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysis.technical.trend.signal}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400 mb-1">Momentum</div>
              <div className="text-3xl font-bold" style={{ color: momentumScore >= 60 ? '#10b981' : momentumScore >= 40 ? '#f59e0b' : '#ef4444' }}>
                {momentumScore.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysis.technical.momentum.signal}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400 mb-1">Volatility</div>
              <div className="text-3xl font-bold" style={{ color: volatilityScore >= 60 ? '#10b981' : volatilityScore >= 40 ? '#f59e0b' : '#ef4444' }}>
                {volatilityScore.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysis.technical.volatility.signal}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400 mb-1">VWAP</div>
              <div className="text-3xl font-bold text-purple-400">
                {analysis.technical.vwap?.value ? `$${analysis.technical.vwap.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'N/A'}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysis.technical.vwap?.signal || 'N/A'}</div>
            </div>
          </div>
          {/* Ichimoku Detail */}
          {analysis.technical.ichimoku && (
            <div className="mt-4 bg-white/5 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm text-gray-400">Ichimoku Cloud: </span>
                  <span className={`text-sm font-medium ${analysis.technical.ichimoku.signal.includes('bullish') ? 'text-green-400' : analysis.technical.ichimoku.signal.includes('bearish') ? 'text-red-400' : 'text-yellow-400'}`}>
                    {analysis.technical.ichimoku.signal.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-sm text-gray-400">Cloud: </span>
                  <span className={`text-sm font-medium ${analysis.technical.ichimoku.cloud_color === 'bullish' ? 'text-green-400' : 'text-red-400'}`}>
                    {analysis.technical.ichimoku.cloud_color}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-xs text-gray-600 py-2">
        {analysis?.data_points || 0} data points | Source: {analysis?.data_source || 'N/A'} | Analysis in {analysis?.execution_time_ms || 0}ms | {selectedSymbol}/USD
      </div>
    </div>
  );
};

export default AnalysisPanel;

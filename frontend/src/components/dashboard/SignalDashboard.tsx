import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';

interface HistoricalPerformance {
  win_rate: number;
  total_signals: number;
  feedback_adjustment: number;
  factor_performance: Record<string, { win_rate: number; discrimination_power: number; sample_size: number }>;
  has_history: boolean;
}

interface AnalysisData {
  symbol: string;
  current_price: number;
  data_source: string;
  data_points: number;
  high_365d: number;
  low_365d: number;
  historical_performance: HistoricalPerformance;
  regime: {
    components: Record<string, {
      label: string;
      weight: string;
      score: number;
      signal: string;
      data_available?: boolean;
    }>;
    composite: {
      score: number | null;
      zone: string;
      guidance: string;
    };
    exposure: {
      posture: string;
      max_exposure: number;
      recommendation: string;
    };
  };
  technical: {
    overall_score: number;
    trend: { score: number; signal: string };
    momentum: { score: number; signal: string; rsi: number };
    volatility: { score: number; signal: string };
    support_resistance: { signal: string };
    vwap: { value: number; deviation: number; signal: string; upper_band: number; lower_band: number };
    ichimoku: { signal: string; cloud_color: string; above_cloud: boolean; below_cloud: boolean; tk_cross: string; tenkan_sen: number; kijun_sen: number; senkou_a: number; senkou_b: number };
  };
  position: {
    position_size: number;
    position_value_usd: number;
    risk_amount_usd: number;
    risk_reward_ratio: number;
    position_pct_of_account: number;
    entry_price: number;
    stop_loss: number;
    take_profits: Array<{ level: string; price: number; pct: number }>;
    risk_pct: number;
    account_size: number;
  };
  verdict: {
    signal: string;
    regime_score: number;
    technical_score: number;
    combined_score: number;
    posture: string;
    max_exposure: number;
    confidence_adjustment: number;
    historical_accuracy: number;
  };
  execution_time_ms: number;
}

const COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LINK'];

function getScoreColor(score: number): string {
  if (score >= 70) return '#10b981';
  if (score >= 40) return '#f59e0b';
  return '#ef4444';
}

// Radar Chart SVG component
const RadarChart: React.FC<{ data: Array<{ label: string; value: number }>; size?: number }> = ({ data, size = 280 }) => {
  const center = size / 2;
  const radius = size / 2 - 40;
  const n = data.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (index: number, value: number) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / 100) * radius;
    return { x: center + r * Math.cos(angle), y: center + r * Math.sin(angle) };
  };

  const polygonPoints = data.map((d, i) => {
    const p = getPoint(i, d.value);
    return `${p.x},${p.y}`;
  }).join(' ');

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {[20, 40, 60, 80, 100].map((level) => (
        <circle key={level} cx={center} cy={center} r={(level / 100) * radius} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
      ))}
      {data.map((_, i) => {
        const angle = i * angleStep - Math.PI / 2;
        return <line key={i} x1={center} y1={center} x2={center + radius * Math.cos(angle)} y2={center + radius * Math.sin(angle)} stroke="rgba(255,255,255,0.1)" strokeWidth={1} />;
      })}
      <polygon points={polygonPoints} fill="rgba(139, 92, 246, 0.3)" stroke="#8b5cf6" strokeWidth={2} />
      {data.map((d, i) => {
        const p = getPoint(i, d.value);
        return <circle key={i} cx={p.x} cy={p.y} r={5} fill={getScoreColor(d.value)} stroke="white" strokeWidth={2} />;
      })}
      {data.map((d, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const labelR = radius + 25;
        const x = center + labelR * Math.cos(angle);
        const y = center + labelR * Math.sin(angle);
        return <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fill="rgba(255,255,255,0.7)" fontSize={11}>{d.label}</text>;
      })}
    </svg>
  );
};

// Score bar component
const ScoreBar: React.FC<{ label: string; score: number; weight: string; signal: string; compact?: boolean; winRate?: number }> = ({
  label, score, weight, signal, compact, winRate,
}) => (
  <div className={`mb-3 ${compact ? 'mb-2' : ''}`}>
    <div className="flex items-center justify-between mb-1">
      <span className="text-sm text-gray-300">{label} <span className="text-gray-500">({weight})</span></span>
      <div className="flex items-center gap-2">
        {winRate !== undefined && winRate > 0 && (
          <span className="text-xs text-gray-500">WR: {winRate.toFixed(0)}%</span>
        )}
        <span className="text-sm font-bold" style={{ color: getScoreColor(score) }}>{score.toFixed(1)}</span>
      </div>
    </div>
    <div className="w-full bg-white/10 rounded-full h-2">
      <div className="h-2 rounded-full transition-all duration-500" style={{ width: `${score}%`, backgroundColor: getScoreColor(score) }} />
    </div>
    {!compact && <p className="text-xs text-gray-500 mt-1">{signal}</p>}
  </div>
);

// Gauge component
const Gauge: React.FC<{ value: number; max?: number; label: string; color?: string }> = ({
  value, max = 100, label, color,
}) => {
  const pct = (value / max) * 100;
  const gaugeColor = color || getScoreColor(value);
  return (
    <div className="text-center">
      <div className="relative w-24 h-12 mx-auto mb-2">
        <svg viewBox="0 0 100 50" className="w-full h-full">
          <path d="M 10 45 A 40 40 0 0 1 90 45" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={8} strokeLinecap="round" />
          <path d="M 10 45 A 40 40 0 0 1 90 45" fill="none" stroke={gaugeColor} strokeWidth={8} strokeLinecap="round" strokeDasharray={`${pct * 1.26} 126`} />
        </svg>
      </div>
      <div className="text-xl font-bold" style={{ color: gaugeColor }}>{value.toFixed(1)}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
};

export const SignalDashboard: React.FC = () => {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCoin, setSelectedCoin] = useState('BTC');
  const [accountSize, setAccountSize] = useState(10000);

  const fetchAnalysis = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Not logged in. Please login first.');
        setLoading(false);
        return;
      }
      const response = await apiFetch(
        `/skills/full-analysis/?symbol=${symbol}&account_size=${accountSize}&risk_pct=0.02`
      );
      if (response.ok) {
        const result = await response.json();
        setData(result);
      } else if (response.status === 401) {
        setError('Session expired. Please logout and login again.');
      } else {
        const errData = await response.json().catch(() => ({}));
        setError(errData.error || 'Failed to fetch analysis');
      }
    } catch (err) {
      setError('Network error: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
    }
  }, [accountSize]);

  useEffect(() => {
    fetchAnalysis(selectedCoin);
  }, [selectedCoin, fetchAnalysis]);

  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-purple-500 border-t-transparent mx-auto" />
          <p className="text-gray-400 mt-3">Running analysis on {selectedCoin}...</p>
          <p className="text-gray-500 text-sm mt-1">Fetching live data + running all skills + checking history</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <button onClick={() => fetchAnalysis(selectedCoin)} className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const hp = data.historical_performance;
  const factorPerf = hp.factor_performance;

  const radarData = [
    { label: 'Technical', value: data.technical.overall_score },
    { label: 'Trend', value: data.technical.trend.score },
    { label: 'Momentum', value: data.technical.momentum.score },
    { label: 'Volatility', value: data.technical.volatility.score },
    { label: 'Regime', value: data.regime.composite.score || 50 },
  ];

  const verdictColor = data.verdict.signal.includes('BUY') ? '#10b981'
    : data.verdict.signal.includes('SELL') ? '#ef4444' : '#f59e0b';

  const adjDirection = data.verdict.confidence_adjustment > 0 ? 'up' : data.verdict.confidence_adjustment < 0 ? 'down' : 'none';

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Signal Analysis Dashboard</h1>
          <p className="text-gray-400 text-sm">Live multi-factor analysis + historical performance feedback</p>
        </div>
        <div className="flex items-center gap-3">
          <input type="number" value={accountSize} onChange={(e) => setAccountSize(Number(e.target.value))} className="w-28 px-3 py-1.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm" placeholder="Account $" />
          <span className="text-gray-400 text-sm">ms: {data.execution_time_ms}</span>
        </div>
      </div>

      {/* Coin Selector */}
      <div className="flex gap-2 flex-wrap">
        {COINS.map((coin) => (
          <button key={coin} onClick={() => setSelectedCoin(coin)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${selectedCoin === coin ? 'bg-purple-600 text-white shadow-lg' : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'}`}>
            {coin}
          </button>
        ))}
      </div>

      {/* Price & Verdict Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Price Card */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-400 text-sm">{data.symbol}/USD</span>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${data.data_source === 'binance' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'}`}>
                {data.data_source === 'binance' ? '⚡ Binance' : '🦎 CoinGecko'}
              </span>
              <span className="text-xs text-gray-500">{data.data_points} candles</span>
            </div>
          </div>
          <div className="text-3xl font-bold text-white">${data.current_price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
          <div className="flex gap-4 mt-3 text-xs text-gray-400">
            <span>365d High: <span className="text-green-400">${data.high_365d.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></span>
            <span>365d Low: <span className="text-red-400">${data.low_365d.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></span>
          </div>
        </div>

        {/* Verdict Card - Enhanced with feedback */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10 flex flex-col items-center justify-center">
          <div className="text-xs text-gray-400 mb-1">FINAL SIGNAL</div>
          <div className="text-4xl font-black tracking-wider" style={{ color: verdictColor }}>{data.verdict.signal}</div>
          <div className="text-sm text-gray-400 mt-2">
            Combined: <span className="text-white font-bold">{data.verdict.combined_score}</span>/100
          </div>
          <div className="flex gap-4 mt-2 text-xs">
            <span className="text-gray-500">Regime: <span className="text-white">{data.verdict.regime_score}</span></span>
            <span className="text-gray-500">Tech: <span className="text-white">{data.verdict.technical_score}</span></span>
          </div>
          {/* Feedback adjustment indicator */}
          {hp.has_history && (
            <div className={`mt-2 text-xs px-2 py-0.5 rounded-full ${adjDirection === 'up' ? 'bg-green-500/20 text-green-400' : adjDirection === 'down' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {adjDirection === 'up' ? '↑' : adjDirection === 'down' ? '↓' : '—'} Adjusted by historical accuracy ({data.verdict.historical_accuracy.toFixed(0)}% WR)
            </div>
          )}
        </div>

        {/* Exposure Card */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <div className="text-xs text-gray-400 mb-2">EXPOSURE POSTURE</div>
          <div className="text-2xl font-bold text-white">{data.regime.exposure.posture}</div>
          <div className="text-sm text-gray-400 mt-1">
            Max Exposure: <span className="text-purple-400 font-bold">{(data.regime.exposure.max_exposure * 100).toFixed(0)}%</span>
          </div>
          <div className="mt-3 bg-white/10 rounded-full h-3">
            <div className="h-3 rounded-full bg-purple-500 transition-all duration-500" style={{ width: `${data.regime.exposure.max_exposure * 100}%` }} />
          </div>
          <p className="text-xs text-gray-500 mt-2">{data.regime.exposure.recommendation}</p>
        </div>
      </div>

      {/* Historical Performance Banner */}
      {hp.has_history && (
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 backdrop-blur-lg rounded-xl p-4 border border-blue-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-2xl">📊</span>
              <div>
                <h3 className="text-sm font-semibold text-white">Historical Performance Feedback</h3>
                <p className="text-xs text-gray-400">Based on {hp.total_signals} past signals over the last 30 days</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-lg font-bold" style={{ color: getScoreColor(hp.win_rate) }}>{hp.win_rate.toFixed(1)}%</div>
                <div className="text-xs text-gray-400">Win Rate</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-white">{hp.total_signals}</div>
                <div className="text-xs text-gray-400">Signals</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${hp.feedback_adjustment > 0 ? 'text-green-400' : hp.feedback_adjustment < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                  {hp.feedback_adjustment > 0 ? '+' : ''}{hp.feedback_adjustment.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400">Score Adj</div>
              </div>
            </div>
          </div>
          {/* Factor win rates */}
          {Object.keys(factorPerf).length > 0 && (
            <div className="flex gap-4 mt-3 pt-3 border-t border-white/5">
              {Object.entries(factorPerf).map(([factor, perf]) => (
                <div key={factor} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-500 capitalize">{factor}:</span>
                  <span className="font-mono" style={{ color: getScoreColor(perf.win_rate || 0) }}>
                    {perf.win_rate ? `${perf.win_rate.toFixed(0)}%` : 'N/A'}
                  </span>
                  <span className="text-gray-600">(n={perf.sample_size || 0})</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Chart + 5-Factor */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">5-Factor Analysis</h3>
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <RadarChart data={radarData} size={260} />
            </div>
            <div className="flex-1 ml-4">
              {[
                { label: 'Technical', score: data.technical.overall_score, weight: '30%', factorKey: 'technical' },
                { label: 'Trend', score: data.technical.trend.score, weight: '', factorKey: 'trend' },
                { label: 'Momentum', score: data.technical.momentum.score, weight: '', factorKey: 'momentum' },
                { label: 'Volatility', score: data.technical.volatility.score, weight: '', factorKey: 'volatility' },
                { label: 'Regime', score: data.regime.composite.score || 50, weight: '', factorKey: 'regime' },
              ].map((item) => (
                <ScoreBar key={item.label} label={item.label} score={item.score} weight={item.weight} signal="" compact winRate={factorPerf[item.factorKey]?.win_rate} />
              ))}
            </div>
          </div>
        </div>

        {/* Regime Analyzer */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-1">Regime Analyzer</h3>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl font-black" style={{ color: getScoreColor(data.regime.composite.score || 50) }}>
              {data.regime.composite.score?.toFixed(1) || 'N/A'}
            </span>
            <div>
              <div className="text-sm font-bold text-white">{data.regime.composite.zone}</div>
              <div className="text-xs text-gray-400">{data.regime.composite.guidance}</div>
            </div>
          </div>
          {Object.entries(data.regime.components).map(([key, comp]) => (
            <ScoreBar key={key} label={comp.label} score={comp.score} weight={comp.weight} signal={comp.signal} compact />
          ))}
        </div>

        {/* Technical Analysis */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Technical Analysis</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <Gauge value={data.technical.trend.score} label="Trend" />
            <Gauge value={data.technical.momentum.score} label="Momentum" />
            <Gauge value={data.technical.volatility.score} label="Volatility" />
            <Gauge value={data.technical.overall_score} label="Overall" color="#8b5cf6" />
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-300"><span>Trend:</span><span>{data.technical.trend.signal}</span></div>
            <div className="flex justify-between text-gray-300"><span>Momentum:</span><span>{data.technical.momentum.signal} (RSI: {data.technical.momentum.rsi})</span></div>
            <div className="flex justify-between text-gray-300"><span>Volatility:</span><span>{data.technical.volatility.signal}</span></div>
            <div className="flex justify-between text-gray-300"><span>S/R:</span><span>{data.technical.support_resistance.signal}</span></div>
            {data.technical.vwap && (
              <div className="flex justify-between text-gray-300">
                <span>VWAP:</span>
                <span>${data.technical.vwap.value.toLocaleString(undefined, { maximumFractionDigits: 2 })} <span className={`text-xs ${data.technical.vwap.signal === 'bullish' ? 'text-green-400' : 'text-red-400'}`}>({data.technical.vwap.deviation > 0 ? '+' : ''}{data.technical.vwap.deviation.toFixed(2)}%)</span></span>
              </div>
            )}
            {data.technical.ichimoku && (
              <div className="flex justify-between text-gray-300">
                <span>Ichimoku:</span>
                <span className={`text-xs ${data.technical.ichimoku.signal.includes('bullish') ? 'text-green-400' : data.technical.ichimoku.signal.includes('bearish') ? 'text-red-400' : 'text-yellow-400'}`}>{data.technical.ichimoku.signal.replace('_', ' ')} <span className="text-gray-500">(cloud: {data.technical.ichimoku.cloud_color})</span></span>
              </div>
            )}
          </div>
          {/* VWAP & Ichimoku Details */}
          {data.technical.vwap && data.technical.ichimoku && (
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-2">VWAP Bands</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-500">Upper:</span><span className="text-red-400">${data.technical.vwap.upper_band.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">VWAP:</span><span className="text-white">${data.technical.vwap.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Lower:</span><span className="text-green-400">${data.technical.vwap.lower_band.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                </div>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-2">Ichimoku Cloud</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-500">Tenkan:</span><span className="text-white">${data.technical.ichimoku.tenkan_sen.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Kijun:</span><span className="text-white">${data.technical.ichimoku.kijun_sen.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">TK Cross:</span><span className={data.technical.ichimoku.tk_cross === 'bullish' ? 'text-green-400' : 'text-red-400'}>{data.technical.ichimoku.tk_cross}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Position:</span><span className={data.technical.ichimoku.above_cloud ? 'text-green-400' : data.technical.ichimoku.below_cloud ? 'text-red-400' : 'text-yellow-400'}>{data.technical.ichimoku.above_cloud ? 'Above' : data.technical.ichimoku.below_cloud ? 'Below' : 'In'} Cloud</span></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Position Sizer */}
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-5 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Position Sizer</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-gray-400 text-xs">Entry Price</div>
              <div className="text-white font-bold">${data.position.entry_price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            </div>
            <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/20">
              <div className="text-gray-400 text-xs">Stop Loss</div>
              <div className="text-red-400 font-bold">${data.position.stop_loss.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            </div>
            {data.position.take_profits.map((tp) => (
              <div key={tp.level} className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                <div className="text-gray-400 text-xs">{tp.level} (+{tp.pct.toFixed(1)}%)</div>
                <div className="text-green-400 font-bold">${tp.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-lg font-bold text-purple-400">{data.position.position_size.toFixed(6)}</div>
              <div className="text-xs text-gray-400">{data.symbol} Size</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">${data.position.position_value_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
              <div className="text-xs text-gray-400">Position Value</div>
            </div>
            <div>
              <div className="text-lg font-bold text-yellow-400">{data.position.risk_reward_ratio.toFixed(2)}:1</div>
              <div className="text-xs text-gray-400">R:R Ratio</div>
            </div>
          </div>
          <div className="mt-3 flex justify-between text-xs text-gray-400">
            <span>Risk: ${data.position.risk_amount_usd.toFixed(0)} ({(data.position.risk_pct * 100).toFixed(1)}%)</span>
            <span>Account: ${data.position.account_size.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-600 py-2">
        Analysis completed in {data.execution_time_ms}ms | {data.data_points} data points | Source: {data.data_source === 'binance' ? 'Binance (real-time)' : 'CoinGecko (fallback)'} | {hp.has_history ? `Historical WR: ${hp.win_rate.toFixed(1)}% (${hp.total_signals} signals)` : 'No historical data yet'} | Powered by Trading Skills Engine
      </div>
    </div>
  );
};

export default SignalDashboard;

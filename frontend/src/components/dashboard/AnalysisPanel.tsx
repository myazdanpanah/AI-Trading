import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

const safe = {
  num: (v: any, d = 0): number => {
    if (v === null || v === undefined || v === '') return d;
    if (Array.isArray(v)) return v.length > 0 ? safe.num(v[0], d) : d;
    if (typeof v === 'object') return d;
    const n = typeof v === 'string' ? parseFloat(v) : v;
    return isNaN(n) ? d : n;
  },
  str: (v: any, d = '---'): string => {
    if (v === null || v === undefined || v === '') return d;
    return String(v);
  },
  price: (v: any): string => {
    const n = safe.num(v, 0);
    if (n === 0) return '---';
    if (n >= 1000) return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 1) return n.toFixed(2);
    return n.toFixed(6);
  },
  pct: (v: any): string => safe.num(v, 0).toFixed(1),
};

// Mini bar chart component
const MiniBar: React.FC<{ value: number; max?: number; color?: string; label?: string; showValue?: boolean }> = ({ value, max = 100, color, label, showValue = true }) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const barColor = color || (value >= 70 ? 'bg-green-500' : value >= 40 ? 'bg-yellow-500' : 'bg-red-500');
  const textColor = value >= 70 ? 'text-green-400' : value >= 40 ? 'text-yellow-400' : 'text-red-400';

  return (
    <div>
      {label && <div className="text-[10px] text-gray-500 mb-1">{label}</div>}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
          <div className={`h-full rounded transition-all ${barColor}`} style={{ width: `${pct}%` }} />
        </div>
        {showValue && <span className={`text-xs font-mono w-10 text-right ${textColor}`}>{value.toFixed(1)}</span>}
      </div>
    </div>
  );
};

// Gauge component
const Gauge: React.FC<{ value: number; label: string; size?: number }> = ({ value, label, size = 80 }) => {
  const pct = Math.min(100, Math.max(0, value));
  const color = value >= 70 ? '#10b981' : value >= 40 ? '#f59e0b' : '#ef4444';
  const circumference = 2 * Math.PI * 35;
  const offset = circumference - (pct / 100) * circumference * 0.75;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="35" fill="none" stroke="#374151" strokeWidth="6" strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`} strokeLinecap="round" transform="rotate(135 40 40)" />
        <circle cx="40" cy="40" r="35" fill="none" stroke={color} strokeWidth="6" strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(135 40 40)" />
        <text x="40" y="42" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">{value.toFixed(0)}</text>
      </svg>
      <div className="text-[10px] text-gray-400 mt-1">{label}</div>
    </div>
  );
};

// Sparkline component
const Sparkline: React.FC<{ data: number[]; color?: string; height?: number }> = ({ data, color = '#3b82f6', height = 30 }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 100;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * height}`).join(' ');

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={points} />
      <circle cx={(data.length - 1) / (data.length - 1) * width} cy={height - ((data[data.length - 1] - min) / range) * height} r="2" fill={color} />
    </svg>
  );
};

// Price Chart component (candlestick-style)
const PriceChart: React.FC<{ data: number[]; symbol: string; height?: number }> = ({ data, symbol, height = 120 }) => {
  if (!data || data.length < 2) return null;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const padding = 20;
  const chartWidth = 100;
  const chartHeight = height;
  
  // Generate candle data (simulate open/high/low/close from price data)
  const candles = data.map((close, i) => {
    const prev = i > 0 ? data[i - 1] : close;
    const open = prev;
    const high = Math.max(open, close) + range * 0.1;
    const low = Math.min(open, close) - range * 0.1;
    return { open, high, low, close, index: i };
  });
  
  const scaleY = (value: number) => {
    return padding + ((max - value) / range) * (chartHeight - 2 * padding);
  };
  
  const candleWidth = (chartWidth - 2 * padding) / data.length;
  const bodyWidth = Math.max(1, candleWidth * 0.6);
  
  // Generate path for price line
  const linePath = candles.map((c, i) => {
    const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding);
    const y = scaleY(c.close);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');
  
  // Generate gradient fill path
  const fillPath = `${linePath} L ${padding + ((data.length - 1) / (data.length - 1)) * (chartWidth - 2 * padding)} ${chartHeight - padding} L ${padding} ${chartHeight - padding} Z`;
  
  const lastPrice = data[data.length - 1];
  const firstPrice = data[0];
  const isUp = lastPrice >= firstPrice;
  const lineColor = isUp ? '#10b981' : '#ef4444';
  const fillColor = isUp ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
  
  return (
    <div className="relative">
      <svg width="100%" height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} preserveAspectRatio="none">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((pct) => (
          <line
            key={pct}
            x1={padding}
            y1={padding + pct * (chartHeight - 2 * padding)}
            x2={chartWidth - padding}
            y2={padding + pct * (chartHeight - 2 * padding)}
            stroke="#374151"
            strokeWidth="0.3"
            strokeDasharray="2,2"
          />
        ))}
        
        {/* Price labels */}
        <text x={2} y={padding + 4} fill="#6b7280" fontSize="3">${max.toFixed(0)}</text>
        <text x={2} y={chartHeight - padding} fill="#6b7280" fontSize="3">${min.toFixed(0)}</text>
        
        {/* Gradient fill */}
        <path d={fillPath} fill={fillColor} />
        
        {/* Price line */}
        <path d={linePath} fill="none" stroke={lineColor} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
        
        {/* Candle bodies */}
        {candles.map((c, i) => {
          const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding) - bodyWidth / 2;
          const bodyTop = scaleY(Math.max(c.open, c.close));
          const bodyBottom = scaleY(Math.min(c.open, c.close));
          const bodyHeight = Math.max(1, bodyBottom - bodyTop);
          const candleColor = c.close >= c.open ? '#10b981' : '#ef4444';
          
          return (
            <g key={i}>
              {/* Wick */}
              <line
                x1={x + bodyWidth / 2}
                y1={scaleY(c.high)}
                x2={x + bodyWidth / 2}
                y2={scaleY(c.low)}
                stroke={candleColor}
                strokeWidth="0.3"
              />
              {/* Body */}
              <rect
                x={x}
                y={bodyTop}
                width={bodyWidth}
                height={bodyHeight}
                fill={candleColor}
                rx="0.2"
              />
            </g>
          );
        })}
        
        {/* Current price marker */}
        <circle
          cx={padding + ((data.length - 1) / (data.length - 1)) * (chartWidth - 2 * padding)}
          cy={scaleY(lastPrice)}
          r="1.5"
          fill={lineColor}
        />
        <text
          x={chartWidth - padding + 1}
          y={scaleY(lastPrice) + 1}
          fill={lineColor}
          fontSize="3"
          fontWeight="bold"
        >
          ${lastPrice.toFixed(0)}
        </text>
      </svg>
      
      {/* Legend */}
      <div className="flex gap-4 mt-1 text-[10px] text-gray-500">
        <span>🟢 Bullish</span>
        <span>🔴 Bearish</span>
        <span>Candles: OHLC</span>
      </div>
    </div>
  );
};

export const AnalysisPanel: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t, language } = useLanguage();
  const [analysis, setAnalysis] = useState<any>(null);
  const [journalSummary, setJournalSummary] = useState<any>(null);
  const [weights, setWeights] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeSymbol, setActiveSymbol] = useState('BTC');
  const [activeSection, setActiveSection] = useState<'overview' | 'technical' | 'regime' | 'journal'>('overview');
  const [error, setError] = useState<string | null>(null);
  const [priceHistory, setPriceHistory] = useState<number[]>([]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const [analysisResp, weightsResp, journalResp] = await Promise.all([
        apiFetch(`/skills/full-analysis/?symbol=${activeSymbol}`),
        apiFetch('/signals/factor-weights/current/'),
        apiFetch('/journal/entries/?limit=5'),
      ]);

      if (analysisResp.ok) {
        const data = await analysisResp.json();
        setAnalysis(data);
        // Build price history from candles
        if (data.technical?.closes) {
          setPriceHistory(data.technical.closes.slice(-30));
        }
      }

      if (weightsResp.ok) {
        const data = await weightsResp.json();
        setWeights(data);
      }

      if (journalResp.ok) {
        const data = await journalResp.json();
        const entries = data.results || data || [];
        setJournalSummary(entries.length > 0 ? entries[0] : null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAnalysis(); }, [activeSymbol]);

  const symbolOptions = baseSymbols.length > 0 ? baseSymbols : ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'];

  const verdict = analysis?.verdict || {};
  const regime = analysis?.regime || {};
  const technical = analysis?.technical || {};
  const position = analysis?.position || {};
  const components = regime?.components || {};
  const composite = regime?.composite || {};
  const exposure = regime?.exposure || {};
  const historical = analysis?.historical_performance || {};

  const regimeScore = safe.num(composite?.score, 50);
  const techScore = safe.num(technical?.overall_score, 50);
  const combinedScore = safe.num(verdict?.combined_score, 50);
  const rsi = safe.num(technical?.momentum?.rsi, 50);

  const getVerdictColor = (signal: string) => {
    const s = safe.str(signal).toUpperCase();
    if (s.includes('BUY')) return 'text-green-400 bg-green-500/20 border-green-500/30';
    if (s.includes('SELL')) return 'text-red-400 bg-red-500/20 border-red-500/30';
    return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
  };

  const sections = [
    { id: 'overview' as const, label: language === 'fa' ? 'نمای کلی' : 'Overview', icon: '📊' },
    { id: 'technical' as const, label: language === 'fa' ? 'تکنیکال' : 'Technical', icon: '📈' },
    { id: 'regime' as const, label: language === 'fa' ? 'رژیم' : 'Regime', icon: '🎯' },
    { id: 'journal' as const, label: language === 'fa' ? 'ژورنال' : 'Journal', icon: '📝' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">{language === 'fa' ? 'تحلیل بازار' : 'Market Analysis'}</h2>
        <div className="flex items-center gap-2">
          <select value={activeSymbol} onChange={(e) => setActiveSymbol(e.target.value)} className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600">
            {symbolOptions.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={loadAnalysis} disabled={loading} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
            {loading ? '...' : '🔄'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="text-red-400">✕</button>
        </div>
      )}

      {loading && !analysis ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-400">{language === 'fa' ? 'در حال تحلیل...' : 'Analyzing...'}</p>
        </div>
      ) : analysis ? (
        <>
          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border mb-4 ${getVerdictColor(verdict.signal)}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-75 mb-1">{language === 'fa' ? 'حکم نهایی' : 'Final Verdict'}</div>
                <div className="text-2xl font-bold">{safe.str(verdict.signal)}</div>
                <div className="text-sm opacity-75 mt-1">{language === 'fa' ? 'وضعیت' : 'Posture'}: {safe.str(exposure.posture)} | Max: {safe.pct(exposure.max_exposure)}%</div>
              </div>
              <div className="flex items-center gap-6">
                <Gauge value={combinedScore} label={language === 'fa' ? 'ترکیبی' : 'Combined'} />
                <Gauge value={regimeScore} label={language === 'fa' ? 'رژیم' : 'Regime'} />
                <Gauge value={techScore} label={language === 'fa' ? 'تکنیکال' : 'Technical'} />
              </div>
            </div>
          </div>

          {/* Price & Position */}
          <div className="grid grid-cols-6 gap-3 mb-4">
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center col-span-1">
              <div className="text-xs text-gray-500">{language === 'fa' ? 'قیمت' : 'Price'}</div>
              <div className="text-lg font-mono font-bold text-white">${safe.price(analysis.current_price)}</div>
              <div className="text-xs text-gray-500">{language === 'fa' ? 'منبع' : 'Source'}: {safe.str(analysis.data_source)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-500">{language === 'fa' ? 'ورود' : 'Entry'}</div>
              <div className="text-lg font-mono text-blue-400">${safe.price(position.entry_price)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-500">{language === 'fa' ? 'حد ضرر' : 'Stop Loss'}</div>
              <div className="text-lg font-mono text-red-400">${safe.price(position.stop_loss)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-500">TP1</div>
              <div className="text-lg font-mono text-green-400">${safe.price(position.take_profits?.[0]?.price)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-500">TP2</div>
              <div className="text-lg font-mono text-green-400">${safe.price(position.take_profits?.[1]?.price)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-500">{language === 'fa' ? 'اندازه' : 'Size'}</div>
              <div className="text-sm font-mono text-white">${safe.price(position.position_size)}</div>
              <div className="text-xs text-gray-500">{safe.str(position.quantity)} {activeSymbol}</div>
            </div>
          </div>

          {/* Price Chart */}
          {priceHistory.length > 0 && (
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-300">{language === 'fa' ? 'نمودار قیمت' : 'Price Chart'} ({activeSymbol}/USDT)</h3>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{priceHistory.length} candles</span>
                  <span>|</span>
                  <span>{language === 'fa' ? 'آخرین' : 'Latest'}: ${safe.price(priceHistory[priceHistory.length - 1])}</span>
                </div>
              </div>
              <PriceChart data={priceHistory} symbol={activeSymbol} height={120} />
            </div>
          )}

          {/* Section Tabs */}
          <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1">
            {sections.map((sec) => (
              <button key={sec.id} onClick={() => setActiveSection(sec.id)} className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-all ${activeSection === sec.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
                {sec.icon} {sec.label}
              </button>
            ))}
          </div>

          {/* Overview Section */}
          {activeSection === 'overview' && (
            <div className="space-y-4">
              {/* Factor Scores */}
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'امتیازات فاکتورها' : 'Factor Scores'}</h3>
                <div className="grid grid-cols-5 gap-4">
                  {[
                    { label: language === 'fa' ? 'تکنیکال' : 'Technical', score: verdict.technical_score, weight: weights?.technical?.weight },
                    { label: language === 'fa' ? 'احساسات' : 'Sentiment', score: verdict.sentiment_score, weight: weights?.sentiment?.weight },
                    { label: language === 'fa' ? 'اخبار' : 'News', score: verdict.news_score, weight: weights?.news?.weight },
                    { label: 'AI', score: verdict.ai_score, weight: weights?.ai?.weight },
                    { label: language === 'fa' ? 'کلان' : 'Macro', score: verdict.macro_score, weight: weights?.macro?.weight },
                  ].map(({ label, score, weight }) => (
                    <div key={label} className="text-center">
                      <div className="text-xs text-gray-400 mb-1">{label}</div>
                      <div className="text-lg font-bold text-white">{safe.num(score).toFixed(0)}</div>
                      {weight && <div className="text-[10px] text-gray-500">w: {(parseFloat(weight) * 100).toFixed(0)}%</div>}
                      <MiniBar value={safe.num(score)} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Weight Distribution */}
              {weights && (
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'توزیع وزن‌ها' : 'Weight Distribution'}</h3>
                  <div className="flex items-end gap-1 h-16">
                    {Object.entries(weights).map(([name, data]: [string, any]) => {
                      const w = parseFloat(data?.weight || 0.2) * 100;
                      const colors: Record<string, string> = { technical: 'bg-blue-500', sentiment: 'bg-purple-500', news: 'bg-orange-500', ai: 'bg-green-500', macro: 'bg-cyan-500' };
                      return (
                        <div key={name} className="flex-1 flex flex-col items-center">
                          <div className="text-[10px] text-gray-400 mb-1">{w.toFixed(0)}%</div>
                          <div className={`w-full rounded-t ${colors[name] || 'bg-gray-500'} transition-all`} style={{ height: `${w * 0.6}px` }} />
                          <div className="text-[10px] text-gray-500 mt-1 capitalize">{name}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Historical Performance */}
              {historical.has_history && (
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'عملکرد تاریخی' : 'Historical Performance'}</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-xs text-gray-400">{language === 'fa' ? 'نرخ برد' : 'Win Rate'}</div>
                      <div className={`text-lg font-bold ${safe.num(historical.win_rate) >= 50 ? 'text-green-400' : 'text-red-400'}`}>{safe.num(historical.win_rate).toFixed(1)}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-400">{language === 'fa' ? 'کل سیگنال‌ها' : 'Total Signals'}</div>
                      <div className="text-lg font-bold text-white">{historical.total_signals || 0}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-400">{language === 'fa' ? 'تنظیم' : 'Adjustment'}</div>
                      <div className={`text-lg font-bold ${safe.num(historical.feedback_adjustment) >= 0 ? 'text-green-400' : 'text-red-400'}`}>{safe.num(historical.feedback_adjustment) > 0 ? '+' : ''}{safe.num(historical.feedback_adjustment).toFixed(0)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Technical Section */}
          {activeSection === 'technical' && (
            <div className="space-y-4">
              {/* Indicators Grid */}
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'اندیکاتورها' : 'Indicators'}</h3>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'RSI (14)', value: technical?.momentum?.rsi, signal: technical?.momentum?.rsi > 70 ? 'overbought' : technical?.momentum?.rsi < 30 ? 'oversold' : 'neutral', color: technical?.momentum?.rsi > 70 ? 'text-red-400' : technical?.momentum?.rsi < 30 ? 'text-green-400' : 'text-yellow-400' },
                    { label: 'MACD', value: null, signal: technical?.momentum?.macd_signal, color: safe.str(technical?.momentum?.macd_signal).includes('bullish') ? 'text-green-400' : 'text-red-400' },
                    { label: 'Trend', value: null, signal: technical?.trend?.signal, color: safe.str(technical?.trend?.signal).includes('up') ? 'text-green-400' : safe.str(technical?.trend?.signal).includes('down') ? 'text-red-400' : 'text-yellow-400' },
                    { label: 'Volatility', value: null, signal: technical?.volatility?.signal, color: 'text-blue-400' },
                    { label: 'VWAP', value: technical?.vwap?.value, signal: technical?.vwap?.signal, color: safe.str(technical?.vwap?.signal) === 'bullish' ? 'text-green-400' : 'text-red-400' },
                    { label: 'Ichimoku', value: null, signal: technical?.ichimoku?.signal, color: safe.str(technical?.ichimoku?.signal).includes('bullish') ? 'text-green-400' : 'text-red-400' },
                    { label: 'Bollinger', value: technical?.volatility?.bollinger_position, signal: technical?.volatility?.signal, color: 'text-purple-400' },
                    { label: 'ATR', value: technical?.volatility?.atr, signal: `${technical?.volatility?.atr_percent || 0}%`, color: 'text-orange-400' },
                  ].map(({ label, value, signal, color }) => (
                    <div key={label} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                      <span className="text-xs text-gray-400">{label}</span>
                      <div className="text-right">
                        {value != null && <div className="text-xs text-gray-300">{typeof value === 'number' ? value.toFixed(2) : value}</div>}
                        <div className={`text-sm font-medium ${color}`}>{safe.str(signal)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Support/Resistance Levels */}
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'سطوح حمایت و مقاومت' : 'Support & Resistance'}</h3>
                <div className="space-y-2">
                  {[
                    { label: 'Resistance 3', price: technical?.volatility?.bollinger_upper, color: 'text-red-400' },
                    { label: 'Resistance 2', price: position.take_profits?.[2]?.price, color: 'text-red-300' },
                    { label: 'Resistance 1', price: position.take_profits?.[1]?.price, color: 'text-red-200' },
                    { label: 'Current Price', price: analysis.current_price, color: 'text-white font-bold' },
                    { label: 'Support 1', price: position.take_profits?.[0]?.price, color: 'text-green-200' },
                    { label: 'Support 2', price: position.stop_loss, color: 'text-green-300' },
                    { label: 'Support 3', price: technical?.volatility?.bollinger_lower, color: 'text-green-400' },
                  ].filter(l => l.price).map(({ label, price, color }) => (
                    <div key={label} className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">{label}</span>
                      <span className={`text-sm font-mono ${color}`}>${safe.price(price)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Regime Section */}
          {activeSection === 'regime' && (
            <div className="space-y-4">
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'اجزای رژیم بازار' : 'Market Regime Components'}</h3>
                <div className="space-y-4">
                  {Object.entries(components).map(([key, comp]: [string, any]) => {
                    const score = safe.num(comp?.score, 50);
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-300">{comp?.label || key}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">{comp?.weight}</span>
                            <span className={`text-xs font-mono ${score >= 60 ? 'text-green-400' : score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{score.toFixed(0)}</span>
                            <span className="text-xs text-gray-500">{safe.str(comp?.signal)}</span>
                          </div>
                        </div>
                        <MiniBar value={score} />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Composite Score Visualization */}
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'نمایش امتیاز ترکیبی' : 'Composite Score Breakdown'}</h3>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-gray-400">{language === 'fa' ? 'امتیاز رژیم' : 'Regime'}:</span>
                      <span className="text-sm font-mono text-white">{regimeScore.toFixed(1)}</span>
                      <span className="text-xs text-gray-500">× 0.5</span>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-gray-400">{language === 'fa' ? 'امتیاز تکنیکال' : 'Technical'}:</span>
                      <span className="text-sm font-mono text-white">{techScore.toFixed(1)}</span>
                      <span className="text-xs text-gray-500">× 0.5</span>
                    </div>
                    <div className="border-t border-gray-700 pt-2 flex items-center gap-2">
                      <span className="text-sm text-gray-400">{language === 'fa' ? 'ترکیبی' : 'Combined'}:</span>
                      <span className="text-lg font-bold text-white">{combinedScore.toFixed(1)}</span>
                    </div>
                  </div>
                  <Gauge value={combinedScore} label={language === 'fa' ? 'نتیجه نهایی' : 'Final'} size={100} />
                </div>
              </div>
            </div>
          )}

          {/* Journal Summary Section */}
          {activeSection === 'journal' && (
            <div className="space-y-4">
              {journalSummary ? (
                <>
                  <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xl">📝</span>
                      <h3 className="text-sm font-semibold text-gray-300">{language === 'fa' ? 'آخرین یادداشت ژورنال' : 'Latest Journal Entry'}</h3>
                      <span className="text-xs text-gray-500">{new Date(journalSummary.created_at).toLocaleDateString('en-US', { timeZone: 'Asia/Tehran' })}</span>
                    </div>
                    <div className="text-sm text-white font-medium mb-2">{journalSummary.title}</div>
                    <div className="text-xs text-gray-400 mb-3 line-clamp-3">{journalSummary.summary || journalSummary.content?.slice(0, 200)}</div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{language === 'fa' ? 'مدل' : 'Model'}: {journalSummary.ai_model}</span>
                      <span>{language === 'fa' ? 'اطمینان' : 'Confidence'}: {((journalSummary.ai_confidence || 0) * 100).toFixed(0)}%</span>
                      <span>{language === 'fa' ? 'منابع' : 'Sources'}: {journalSummary.news_count || 0}</span>
                    </div>
                  </div>

                  {/* Key Findings */}
                  {journalSummary.key_findings?.length > 0 && (
                    <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
                      <h4 className="text-sm font-semibold text-blue-400 mb-2">{language === 'fa' ? 'یافته‌های کلیدی' : 'Key Findings'}</h4>
                      <ul className="space-y-1">
                        {journalSummary.key_findings.slice(0, 3).map((f: string, i: number) => (
                          <li key={i} className="text-xs text-gray-300">• {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Risks & Opportunities */}
                  <div className="grid grid-cols-2 gap-3">
                    {journalSummary.risks_identified?.length > 0 && (
                      <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/20">
                        <h4 className="text-xs font-semibold text-red-400 mb-2">{language === 'fa' ? 'ریسک‌ها' : 'Risks'}</h4>
                        <ul className="space-y-1">
                          {journalSummary.risks_identified.slice(0, 2).map((r: string, i: number) => (
                            <li key={i} className="text-[11px] text-gray-300">⚠ {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {journalSummary.opportunities?.length > 0 && (
                      <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                        <h4 className="text-xs font-semibold text-green-400 mb-2">{language === 'fa' ? 'فرصت‌ها' : 'Opportunities'}</h4>
                        <ul className="space-y-1">
                          {journalSummary.opportunities.slice(0, 2).map((o: string, i: number) => (
                            <li key={i} className="text-[11px] text-gray-300">🚀 {o}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* AI Weights Thinking */}
                  <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'تحلیل وزن‌های AI' : 'AI Weight Analysis'}</h3>
                    <div className="text-xs text-gray-400 space-y-2">
                      <p>{language === 'fa' ? 'AI از فاکتورهای زیر برای تصمیم‌گیری استفاده می‌کند:' : 'AI uses these factors for decision making:'}</p>
                      {weights && Object.entries(weights).map(([name, data]: [string, any]) => {
                        const w = parseFloat(data?.weight || 0.2) * 100;
                        const perf = historical.factor_performance?.[name];
                        return (
                          <div key={name} className="flex items-center gap-2">
                            <span className="capitalize w-20">{name}</span>
                            <div className="flex-1 h-1.5 bg-gray-700 rounded overflow-hidden">
                              <div className="h-full bg-blue-500 rounded" style={{ width: `${w}%` }} />
                            </div>
                            <span className="w-10 text-right">{w.toFixed(0)}%</span>
                            {perf && <span className={`w-16 text-right ${perf.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>{perf.win_rate?.toFixed(0)}% WR</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📝</div>
                  <p>{language === 'fa' ? 'هنوز یادداشتی نیست' : 'No journal entries yet'}</p>
                  <p className="text-sm mt-2">{language === 'fa' ? 'از تب ژورنال یادداشت تولید کنید' : 'Generate entries in the Journal tab'}</p>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="mt-4 text-center text-xs text-gray-500">
            {safe.str(analysis.data_points)} {language === 'fa' ? 'نقطه داده' : 'data points'} · {safe.str(analysis.execution_time_ms)}ms · {safe.str(analysis.data_source)}
          </div>
        </>
      ) : null}
    </div>
  );
};

export default AnalysisPanel;

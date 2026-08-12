import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

// Safe helpers - never crash
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
  pct: (v: any, d = 0): string => {
    const n = safe.num(v, d);
    // If value is 0-1 (decimal), multiply by 100. If already 0-100, keep as-is.
    if (n >= 0 && n <= 1) return (n * 100).toFixed(1);
    return n.toFixed(1);
  },
  price: (v: any): string => {
    const n = safe.num(v, 0);
    if (n === 0) return '---';
    if (n >= 1000) return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 1) return n.toFixed(2);
    return n.toFixed(6);
  },
  date: (v: any): string => {
    try {
      if (!v) return '---';
      return new Date(v).toLocaleString('en-US', { timeZone: 'Asia/Tehran' });
    } catch {
      return '---';
    }
  },
  color: (v: any): string => {
    const n = safe.num(v, 0);
    if (n >= 0.65) return 'text-green-400';
    if (n <= 0.35) return 'text-red-400';
    return 'text-yellow-400';
  },
};

export const SignalDashboard: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t, language } = useLanguage();
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState('1h');

  const loadSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiFetch(`/signals/signals/?symbol=${selectedSymbol}&is_active=true`);
      
      if (!response.ok) {
        // Don't throw, just show empty state
        setSignals([]);
        return;
      }
      
      const data = await response.json();
      
      // Handle different response formats
      let signalList = [];
      if (Array.isArray(data)) {
        signalList = data;
      } else if (data.results && Array.isArray(data.results)) {
        signalList = data.results;
      } else if (data.signal) {
        signalList = [data.signal];
      }
      
      setSignals(signalList);
    } catch (err) {
      console.error('Load signals error:', err);
      setSignals([]); // Show empty state instead of error
    } finally {
      setLoading(false);
    }
  };

  const generateSignal = async () => {
    try {
      setGenerating(true);
      setError(null);
      
      const response = await apiFetch('/signals/signals/generate/', {
        method: 'POST',
        body: JSON.stringify({ 
          symbol: selectedSymbol,
          timeframe: timeframe,
        }),
      });
      
      // Handle empty or non-JSON response
      const text = await response.text();
      let data: any = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        console.error('Invalid JSON response:', text);
        setError(language === 'fa' ? 'خطا در پاسخ سرور' : 'Invalid server response');
        return;
      }
      
      if (!response.ok) {
        const errMsg = data.error || data.detail || 'Failed to generate signal';
        setError(typeof errMsg === 'string' ? errMsg : 'Failed to generate signal');
        return;
      }
      
      // Add new signal to list
      if (data.signal) {
        setSignals(prev => [data.signal, ...prev]);
      } else if (data.details) {
        // Backend returned details without signal object
        setSignals(prev => [data.details, ...prev]);
      } else if (data.symbol || data.direction) {
        // Backend returned the signal directly
        setSignals(prev => [data, ...prev]);
      } else {
        await loadSignals();
      }
    } catch (err) {
      console.error('Generate signal error:', err);
      setError(language === 'fa' ? 'خطا در تولید سیگنال' : 'Error generating signal');
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    loadSignals();
  }, [selectedSymbol]);

  const symbolOptions = baseSymbols.length > 0 ? baseSymbols : ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'];

  const getDirectionColor = (dir: string) => {
    const d = safe.str(dir).toUpperCase();
    if (d === 'BUY' || d === 'LONG') return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (d === 'SELL' || d === 'SHORT') return 'bg-red-500/20 text-red-400 border-red-500/30';
    return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  };

  const getDirectionLabel = (dir: string) => {
    const d = safe.str(dir).toUpperCase();
    if (d === 'BUY' || d === 'LONG') return language === 'fa' ? 'خرید' : 'BUY';
    if (d === 'SELL' || d === 'SHORT') return language === 'fa' ? 'فروش' : 'SELL';
    return language === 'fa' ? 'نگه داشتن' : 'HOLD';
  };

  const factors = [
    { key: 'technical', label: language === 'fa' ? 'تکنیکال' : 'Technical' },
    { key: 'sentiment', label: language === 'fa' ? 'احساسات' : 'Sentiment' },
    { key: 'news', label: language === 'fa' ? 'اخبار' : 'News' },
    { key: 'ai', label: 'AI' },
    { key: 'macro', label: language === 'fa' ? 'کلان' : 'Macro' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">
          {language === 'fa' ? 'سیگنال‌های ترید' : 'Trading Signals'}
        </h2>
        <div className="flex gap-2">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600"
          >
            {symbolOptions.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600"
          >
            {['1m', '5m', '15m', '1h', '4h', '1d'].map(tf => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
          <button
            onClick={generateSignal}
            disabled={generating}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium disabled:opacity-50 flex items-center gap-2"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                {language === 'fa' ? 'در حال تولید...' : 'Generating...'}
              </>
            ) : (
              <>+ {language === 'fa' ? 'تولید سیگنال' : 'Generate'}</>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p>{language === 'fa' ? 'در حال بارگذاری...' : 'Loading signals...'}</p>
        </div>
      ) : signals.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <div className="text-5xl mb-4">🔔</div>
          <p className="text-lg mb-2">{language === 'fa' ? 'هنوز سیگنالی وجود ندارد' : 'No signals yet'}</p>
          <p className="text-sm mb-4">
            {language === 'fa' 
              ? `اولین سیگنال ${selectedSymbol} را تولید کنید`
              : `Generate your first signal for ${selectedSymbol}`}
          </p>
          <button
            onClick={generateSignal}
            disabled={generating}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {language === 'fa' ? 'تولید سیگنال' : 'Generate Signal'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {signals.map((signal, index) => {
            const direction = safe.str(signal.direction || signal.action);
            const confidence = safe.num(signal.confidence);
            const entryPrice = signal.entry_price || signal.entry;
            const stopLoss = signal.stop_loss || signal.sl;
            const takeProfitRaw = signal.take_profit || signal.tp;
            const takeProfit = Array.isArray(takeProfitRaw) ? takeProfitRaw[0] : takeProfitRaw;
            
            return (
              <div key={signal.id || index} className="bg-gray-900 rounded-lg border border-gray-600 p-4 hover:border-gray-500 transition-colors">
                {/* Header Row */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-xl text-white">{safe.str(signal.symbol)}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getDirectionColor(direction)}`}>
                      {getDirectionLabel(direction)}
                    </span>
                    <span className="text-sm text-gray-400">
                      {language === 'fa' ? 'اطمینان' : 'Confidence'}: {safe.pct(confidence)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-300">
                      {safe.str(signal.timeframe)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {safe.date(signal.created_at)}
                    </span>
                  </div>
                </div>

                {/* Price Levels */}
                <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-800 rounded-lg">
                  <div className="text-center">
                    <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'ورود' : 'Entry'}</div>
                    <div className="text-lg font-mono text-white">${safe.price(entryPrice)}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'حد ضرر' : 'Stop Loss'}</div>
                    <div className="text-lg font-mono text-red-400">${safe.price(stopLoss)}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'حد سود' : 'Take Profit'}</div>
                    <div className="text-lg font-mono text-green-400">${safe.price(takeProfit)}</div>
                  </div>
                </div>

                {/* Factor Scores */}
                <div className="grid grid-cols-5 gap-2">
                  {factors.map(({ key, label }) => {
                    const score = safe.num(signal[key + '_score'] || signal.factors?.[key]);
                    return (
                      <div key={key} className="text-center p-2 bg-gray-800 rounded">
                        <div className="text-[10px] text-gray-500 mb-1">{label}</div>
                        <div className={`text-sm font-mono font-bold ${safe.color(score)}`}>
                          {safe.pct(score, 0)}%
                        </div>
                        <div className="h-1 bg-gray-700 rounded mt-1 overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded transition-all"
                            style={{ width: `${Math.min(100, Math.max(0, safe.num(score) * 100))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Reasons */}
                {signal.reasons && Array.isArray(signal.reasons) && signal.reasons.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="text-xs text-gray-500 mb-2">
                      {language === 'fa' ? 'دلایل:' : 'Reasons:'}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {signal.reasons.slice(0, 4).map((reason: any, i: number) => (
                        <span key={i} className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-300">
                          {safe.str(reason.description || reason)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

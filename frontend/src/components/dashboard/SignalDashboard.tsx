import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface Signal {
  id?: string;
  symbol: string;
  direction: string;
  confidence: any;
  risk_score: any;
  entry_price: any;
  stop_loss: any;
  take_profit: any;
  timeframe: string;
  technical_score: any;
  sentiment_score: any;
  news_score: any;
  ai_score: any;
  macro_score: any;
  composite_score: any;
  is_active: boolean;
  created_at: string;
  reasons?: Array<{
    reason_type: string;
    description: string;
    confidence: any;
  }>;
}

// Safe number conversion helpers
const safeNumber = (value: any, defaultValue: number = 0): number => {
  if (value === null || value === undefined || value === '') return defaultValue;
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? defaultValue : num;
};

const safeToFixed = (value: any, digits: number = 2): string => {
  const num = safeNumber(value, 0);
  return num.toFixed(digits);
};

const safePercent = (value: any, digits: number = 1): string => {
  const num = safeNumber(value, 0);
  return (num * 100).toFixed(digits);
};

const formatPrice = (price: any): string => {
  const num = safeNumber(price, 0);
  if (num === 0) return '---';
  if (num >= 1000) return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (num >= 1) return num.toFixed(2);
  return num.toFixed(6);
};

export const SignalDashboard: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t } = useLanguage();
  const [signals, setSignals] = useState<Signal[]>([]);
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
        throw new Error('Failed to load signals');
      }
      const data = await response.json();
      setSignals(data.results || data || []);
    } catch (error) {
      console.error('Failed to load signals:', error);
      setError('Failed to load signals. Please try again.');
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
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate signal');
      }
      
      if (data.signal) {
        setSignals(prev => [data.signal, ...prev]);
      } else {
        await loadSignals();
      }
    } catch (error) {
      console.error('Failed to generate signal:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate signal. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    loadSignals();
  }, [selectedSymbol]);

  const getActionColor = (direction: string) => {
    switch (direction?.toUpperCase()) {
      case 'BUY':
      case 'LONG':
        return 'text-green-400 bg-green-500/20';
      case 'SELL':
      case 'SHORT':
        return 'text-red-400 bg-red-500/20';
      default:
        return 'text-yellow-400 bg-yellow-500/20';
    }
  };

  const getActionLabel = (direction: string) => {
    switch (direction?.toUpperCase()) {
      case 'BUY':
      case 'LONG':
        return t('signals.buy');
      case 'SELL':
      case 'SHORT':
        return t('signals.sell');
      default:
        return t('signals.hold');
    }
  };

  const symbolOptions = baseSymbols.length > 0 ? baseSymbols : ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{t('signals.title')}</h2>
        <div className="flex gap-2">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm"
          >
            {symbolOptions.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm"
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1D</option>
          </select>
          <button
            onClick={generateSignal}
            disabled={generating}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium disabled:opacity-50"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Generating...
              </span>
            ) : (
              `+ Generate`
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-400 hover:text-red-300">✕</button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          Loading signals...
        </div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-4">🔔</div>
          <p className="text-lg mb-2">No signals yet</p>
          <p className="text-sm mb-4">Generate your first signal for {selectedSymbol}</p>
          <button
            onClick={generateSignal}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Signal'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {signals.map((signal, index) => (
            <div key={signal.id || index} className="bg-gray-800 rounded-lg border border-gray-600 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-bold text-lg">{signal.symbol}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getActionColor(signal.direction)}`}>
                      {getActionLabel(signal.direction)}
                    </span>
                    <span className="text-sm text-gray-400">
                      Confidence: {safePercent(signal.confidence)}%
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-gray-700 rounded text-gray-300">
                      {signal.timeframe}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {new Date(signal.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Price Levels */}
              <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Entry:</span>
                  <span className="ml-2 text-white font-mono">${formatPrice(signal.entry_price)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Stop Loss:</span>
                  <span className="ml-2 text-red-400 font-mono">${formatPrice(signal.stop_loss)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Take Profit:</span>
                  <span className="ml-2 text-green-400 font-mono">${formatPrice(signal.take_profit)}</span>
                </div>
              </div>

              {/* Factor Breakdown */}
              <div className="mt-4 grid grid-cols-5 gap-2">
                {[
                  { key: 'technical', label: 'Technical', score: signal.technical_score },
                  { key: 'sentiment', label: 'Sentiment', score: signal.sentiment_score },
                  { key: 'news', label: 'News', score: signal.news_score },
                  { key: 'ai', label: 'AI', score: signal.ai_score },
                  { key: 'macro', label: 'Macro', score: signal.macro_score },
                ].map(({ key, label, score }) => (
                  <div key={key} className="text-center">
                    <div className="text-xs text-gray-400 mb-1">{label}</div>
                    <div className="text-sm font-mono">
                      {safePercent(score, 0)}%
                    </div>
                    <div className="h-1 bg-gray-600 rounded mt-1">
                      <div
                        className="h-1 bg-blue-500 rounded"
                        style={{ width: `${Math.min(100, Math.max(0, safeNumber(score) * 100))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Signal Reasons */}
              {signal.reasons && signal.reasons.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="text-xs text-gray-500 mb-2">Reasons:</div>
                  <div className="flex flex-wrap gap-2">
                    {signal.reasons.slice(0, 3).map((reason, i) => (
                      <span key={i} className="text-xs px-2 py-1 bg-gray-700 rounded text-gray-300">
                        {reason.description}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

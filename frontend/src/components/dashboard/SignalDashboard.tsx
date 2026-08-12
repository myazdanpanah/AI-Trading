import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface Signal {
  symbol: string;
  action: string;
  confidence: number;
  factors: {
    technical: number;
    sentiment: number;
    ai: number;
    macro: number;
    news: number;
  };
  metadata: any;
  created_at: string;
  model_used?: string;
  has_history?: boolean;
}

export const SignalDashboard: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t } = useLanguage();
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [error, setError] = useState<string | null>(null);

  const loadSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/signals/?symbol=${selectedSymbol}`);
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
      const response = await apiFetch('/signals/generate/', {
        method: 'POST',
        body: JSON.stringify({ symbol: selectedSymbol }),
      });
      if (!response.ok) {
        throw new Error('Failed to generate signal');
      }
      await loadSignals();
    } catch (error) {
      console.error('Failed to generate signal:', error);
      setError('Failed to generate signal. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    loadSignals();
  }, [selectedSymbol]);

  const getActionColor = (action: string) => {
    switch (action?.toUpperCase()) {
      case 'BUY':
        return 'text-green-400 bg-green-500/20';
      case 'SELL':
        return 'text-red-400 bg-red-500/20';
      default:
        return 'text-yellow-400 bg-yellow-500/20';
    }
  };

  const getActionLabel = (action: string) => {
    switch (action?.toUpperCase()) {
      case 'BUY':
        return t('signals.buy');
      case 'SELL':
        return t('signals.sell');
      default:
        return t('signals.hold');
    }
  };

  // Ensure baseSymbols has at least some options
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
          <button
            onClick={generateSignal}
            disabled={generating}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium disabled:opacity-50"
          >
            {generating ? t('common.loading') : `+ ${t('signals.generate')}`}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">{t('common.loading')}</div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-4">🔔</div>
          <p className="text-lg mb-2">{t('common.noData')}</p>
          <button
            onClick={generateSignal}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t('signals.generate')}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {signals.map((signal, index) => (
            <div key={index} className="bg-gray-800 rounded-lg border border-gray-600 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-bold text-lg">{signal.symbol}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getActionColor(signal.action)}`}>
                      {getActionLabel(signal.action)}
                    </span>
                    <span className="text-sm text-gray-400">
                      {t('signals.confidence')}: {(signal.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {new Date(signal.created_at).toLocaleString()}
                  </div>
                </div>
                {signal.model_used && (
                  <div className="text-xs text-gray-500">
                    {t('chatbot.modelUsed')}: {signal.model_used}
                  </div>
                )}
              </div>

              {/* Factor Breakdown */}
              <div className="mt-4 grid grid-cols-5 gap-2">
                {Object.entries(signal.factors).map(([factor, score]) => (
                  <div key={factor} className="text-center">
                    <div className="text-xs text-gray-400 mb-1">
                      {t(`signals.${factor}`)}
                    </div>
                    <div className="text-sm font-mono">
                      {((score as number) * 100).toFixed(0)}%
                    </div>
                    <div className="h-1 bg-gray-600 rounded mt-1">
                      <div
                        className="h-1 bg-blue-500 rounded"
                        style={{ width: `${(score as number) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

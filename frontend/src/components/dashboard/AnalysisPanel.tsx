import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface AnalysisData {
  regime: {
    score: number;
    components: {
      btc_trend: number;
      alt_breadth: number;
      dominance: number;
      funding: number;
      drawdown: number;
      momentum: number;
    };
  };
  technical: {
    score: number;
    indicators: {
      trend: number;
      momentum: number;
      volatility: number;
      rsi: number;
      vwap: number;
      ichimoku: number;
    };
  };
  candlestick: {
    patterns: any[];
    overall: number;
  };
}

export const AnalysisPanel: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t } = useLanguage();
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeSymbol, setActiveSymbol] = useState('BTC');
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/skills/full-analysis/?symbol=${activeSymbol}`);
      if (!response.ok) {
        throw new Error('Failed to load analysis');
      }
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to load analysis:', error);
      setError('Failed to load analysis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, [activeSymbol]);

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-400';
    if (score >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Ensure baseSymbols has at least some options
  const symbolOptions = baseSymbols.length > 0 ? baseSymbols : ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{t('analysis.title')}</h2>
        <select
          value={activeSymbol}
          onChange={(e) => setActiveSymbol(e.target.value)}
          className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm"
        >
          {symbolOptions.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          {t('common.loading')}
        </div>
      ) : !analysis ? (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-lg mb-2">{t('common.noData')}</p>
          <button
            onClick={loadAnalysis}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t('common.retry')}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Score Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.regimeScore')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.regime?.score || 50)}`}>
                {(analysis.regime?.score || 50).toFixed(1)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.technicalScore')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.technical?.score || 50)}`}>
                {(analysis.technical?.score || 50).toFixed(1)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.rsi')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.technical?.indicators?.rsi || 50)}`}>
                {(analysis.technical?.indicators?.rsi || 50).toFixed(1)}
              </div>
            </div>
          </div>

          {/* Technical Indicators */}
          {analysis.technical?.indicators && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-sm font-semibold mb-3">{t('analysis.technicalIndicators')}</h3>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(analysis.technical.indicators).map(([key, value]) => (
                  <div key={key}>
                    <div className="text-xs text-gray-400 mb-1">{t(`analysis.${key}`)}</div>
                    <div className="h-2 bg-gray-600 rounded">
                      <div
                        className="h-2 bg-blue-500 rounded"
                        style={{ width: `${Math.min(100, Math.max(0, value as number))}%` }}
                      />
                    </div>
                    <div className="text-xs text-right mt-1">{(value as number).toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regime Components */}
          {analysis.regime?.components && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-sm font-semibold mb-3">{t('analysis.regimeComponents')}</h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(analysis.regime.components).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className="text-sm text-gray-300 w-24">{t(`analysis.${key}`)}</div>
                    <div className="flex-1 h-2 bg-gray-600 rounded">
                      <div
                        className="h-2 bg-blue-500 rounded"
                        style={{ width: `${Math.min(100, Math.max(0, (value as number) * 100))}%` }}
                      />
                    </div>
                    <div className="text-sm font-mono w-12 text-right">
                      {((value as number) * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Candlestick Patterns */}
          {analysis.candlestick?.patterns && analysis.candlestick.patterns.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <h3 className="text-sm font-semibold mb-3">{t('analysis.patterns')}</h3>
              <div className="space-y-2">
                {analysis.candlestick.patterns.slice(0, 5).map((pattern, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{pattern.name}</span>
                    <span
                      className={`text-sm ${
                        pattern.direction === 'bullish'
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {pattern.direction === 'bullish' ? t('analysis.bullish') : t('analysis.bearish')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

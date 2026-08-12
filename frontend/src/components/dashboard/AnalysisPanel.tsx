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

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const response = await apiFetch(`/skills/full-analysis/?symbol=${activeSymbol}`);
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to load analysis:', error);
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

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{t('analysis.title')}</h2>
        <select
          value={activeSymbol}
          onChange={(e) => setActiveSymbol(e.target.value)}
          className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm"
        >
          {baseSymbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400">{t('common.loading')}</div>
      ) : !analysis ? (
        <div className="text-center py-8 text-gray-400">{t('common.noData')}</div>
      ) : (
        <div className="space-y-6">
          {/* Score Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.regimeScore')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.regime.score)}`}>
                {analysis.regime.score.toFixed(1)}
              </div>
            </div>
            <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.technicalScore')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.technical.score)}`}>
                {analysis.technical.score.toFixed(1)}
              </div>
            </div>
            <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
              <div className="text-sm text-gray-400 mb-1">{t('analysis.rsi')}</div>
              <div className={`text-3xl font-bold ${getScoreColor(analysis.technical.indicators.rsi)}`}>
                {analysis.technical.indicators.rsi.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
            <h3 className="text-sm font-semibold mb-3">{t('analysis.technicalIndicators')}</h3>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(analysis.technical.indicators).map(([key, value]) => (
                <div key={key}>
                  <div className="text-xs text-gray-400 mb-1">{t(`analysis.${key}`)}</div>
                  <div className="h-2 bg-gray-600 rounded">
                    <div
                      className="h-2 bg-blue-500 rounded"
                      style={{ width: `${value}%` }}
                    />
                  </div>
                  <div className="text-xs text-right mt-1">{(value as number).toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>

          {/* Regime Components */}
          <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
            <h3 className="text-sm font-semibold mb-3">{t('analysis.regimeComponents')}</h3>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(analysis.regime.components).map(([key, value]) => (
                <div key={key} className="flex items-center gap-3">
                  <div className="text-sm text-gray-300 w-24">{t(`analysis.${key}`)}</div>
                  <div className="flex-1 h-2 bg-gray-600 rounded">
                    <div
                      className="h-2 bg-blue-500 rounded"
                      style={{ width: `${(value as number) * 100}%` }}
                    />
                  </div>
                  <div className="text-sm font-mono w-12 text-right">
                    {((value as number) * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Candlestick Patterns */}
          {analysis.candlestick && analysis.candlestick.patterns.length > 0 && (
            <div className="bg-gray-750 rounded-lg p-4 border border-gray-600">
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

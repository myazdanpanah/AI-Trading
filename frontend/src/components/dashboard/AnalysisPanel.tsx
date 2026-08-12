import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

const safe = {
  num: (v: any, d = 0): number => {
    if (v === null || v === undefined || v === '') return d;
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
  color: (v: any): string => {
    const n = safe.num(v, 50);
    if (n >= 70) return 'text-green-400';
    if (n >= 40) return 'text-yellow-400';
    return 'text-red-400';
  },
  barColor: (v: any): string => {
    const n = safe.num(v, 50);
    if (n >= 70) return 'bg-green-500';
    if (n >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  },
};

export const AnalysisPanel: React.FC = () => {
  const { baseSymbols } = useWatchlist();
  const { t, language } = useLanguage();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeSymbol, setActiveSymbol] = useState('BTC');
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/skills/full-analysis/?symbol=${activeSymbol}`);
      if (!response.ok) {
        const text = await response.text();
        let errMsg = 'Failed to load analysis';
        try { const j = JSON.parse(text); errMsg = j.error || errMsg; } catch {}
        throw new Error(errMsg);
      }
      const data = await response.json();
      setAnalysis(data);
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, [activeSymbol]);

  const symbolOptions = baseSymbols.length > 0 ? baseSymbols : ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'];

  const verdict = analysis?.verdict || {};
  const regime = analysis?.regime || {};
  const technical = analysis?.technical || {};
  const position = analysis?.position || {};
  const components = regime?.components || {};
  const composite = regime?.composite || {};
  const exposure = regime?.exposure || {};

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

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">
          {language === 'fa' ? 'تحلیل بازار' : 'Market Analysis'}
        </h2>
        <div className="flex items-center gap-2">
          <select
            value={activeSymbol}
            onChange={(e) => setActiveSymbol(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600"
          >
            {symbolOptions.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            onClick={loadAnalysis}
            disabled={loading}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '...' : language === 'fa' ? 'بروزرسانی' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="text-red-400">✕</button>
        </div>
      )}

      {/* Loading */}
      {loading && !analysis && (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p>{language === 'fa' ? 'در حال تحلیل بازار...' : 'Analyzing market data...'}</p>
        </div>
      )}

      {/* Empty */}
      {!loading && !analysis && !error && (
        <div className="text-center py-12 text-gray-400">
          <div className="text-5xl mb-4">📊</div>
          <p className="text-lg mb-2">{language === 'fa' ? 'تحلیلی بارگذاری نشد' : 'No analysis loaded'}</p>
          <button onClick={loadAnalysis} className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            {language === 'fa' ? 'شروع تحلیل' : 'Run Analysis'}
          </button>
        </div>
      )}

      {/* Analysis Content */}
      {analysis && (
        <div className="space-y-4">
          {/* Verdict Banner */}
          <div className={`p-4 rounded-xl border ${getVerdictColor(verdict.signal)}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-75 mb-1">
                  {language === 'fa' ? 'حکم نهایی' : 'Final Verdict'}
                </div>
                <div className="text-2xl font-bold">{safe.str(verdict.signal)}</div>
              </div>
              <div className="text-right">
                <div className="text-sm opacity-75 mb-1">
                  {language === 'fa' ? 'امتیاز ترکیبی' : 'Combined Score'}
                </div>
                <div className="text-3xl font-bold">{safe.pct(combinedScore)}</div>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm opacity-75">
              <div>{language === 'fa' ? 'وضعیت' : 'Posture'}: {safe.str(exposure.posture)}</div>
              <div>{language === 'fa' ? 'حداکثر نمایشی' : 'Max Exposure'}: {safe.pct(exposure.max_exposure)}%</div>
            </div>
          </div>

          {/* Score Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'امتیاز رژیم' : 'Regime Score'}</div>
              <div className={`text-2xl font-bold ${safe.color(regimeScore)}`}>{safe.pct(regimeScore)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'امتیاز تکنیکال' : 'Technical Score'}</div>
              <div className={`text-2xl font-bold ${safe.color(techScore)}`}>{safe.pct(techScore)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
              <div className="text-xs text-gray-400 mb-1">RSI</div>
              <div className={`text-2xl font-bold ${safe.color(rsi)}`}>{safe.pct(rsi)}</div>
            </div>
          </div>

          {/* Price & Position */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              {language === 'fa' ? 'سطوح قیمتی' : 'Price Levels'}
            </h3>
            <div className="grid grid-cols-4 gap-3">
              <div className="text-center">
                <div className="text-xs text-gray-500">{language === 'fa' ? 'قیمت فعلی' : 'Current'}</div>
                <div className="text-lg font-mono text-white">${safe.price(analysis.current_price)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500">{language === 'fa' ? 'ورود' : 'Entry'}</div>
                <div className="text-lg font-mono text-blue-400">${safe.price(position.entry_price)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500">{language === 'fa' ? 'حد ضرر' : 'Stop Loss'}</div>
                <div className="text-lg font-mono text-red-400">${safe.price(position.stop_loss)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500">{language === 'fa' ? 'حد سود' : 'Take Profit'}</div>
                <div className="text-lg font-mono text-green-400">
                  ${safe.price(position.take_profits?.[0]?.price)}
                </div>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3 text-xs text-gray-400">
              <div>{language === 'fa' ? 'اندازه پوزیشن' : 'Position Size'}: ${safe.price(position.position_size)}</div>
              <div>{language === 'fa' ? 'ریسک' : 'Risk'}: ${safe.price(position.risk_amount)}</div>
              <div>{language === 'fa' ? 'تعداد سکه' : 'Qty'}: {safe.str(position.quantity)}</div>
            </div>
          </div>

          {/* Regime Components */}
          {Object.keys(components).length > 0 && (
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                {language === 'fa' ? 'اجزای تحلیل رژیم' : 'Regime Components'}
              </h3>
              <div className="space-y-3">
                {Object.entries(components).map(([key, comp]: [string, any]) => {
                  const score = safe.num(comp?.score, 50);
                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-300">{comp?.label || key}</span>
                        <span className="text-xs text-gray-500">{comp?.weight || ''} · {safe.str(comp?.signal)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
                          <div className={`h-full rounded transition-all ${safe.barColor(score)}`} style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
                        </div>
                        <span className={`text-xs font-mono w-8 text-right ${safe.color(score)}`}>{safe.pct(score)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Technical Indicators */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              {language === 'fa' ? 'اندیکاتورهای تکنیکال' : 'Technical Indicators'}
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'RSI', value: technical?.momentum?.rsi },
                { label: 'MACD', value: technical?.momentum?.macd_signal },
                { label: 'Trend', value: technical?.trend?.signal },
                { label: 'Volatility', value: technical?.volatility?.signal },
                { label: 'VWAP', value: technical?.vwap?.signal, extra: technical?.vwap?.value },
                { label: 'Ichimoku', value: technical?.ichimoku?.signal },
              ].map(({ label, value, extra }) => (
                <div key={label} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                  <span className="text-xs text-gray-400">{label}</span>
                  <span className={`text-sm font-medium ${
                    safe.str(value).toLowerCase().includes('bullish') || safe.str(value).toLowerCase().includes('buy')
                      ? 'text-green-400'
                      : safe.str(value).toLowerCase().includes('bearish') || safe.str(value).toLowerCase().includes('sell')
                        ? 'text-red-400'
                        : 'text-yellow-400'
                  }`}>
                    {safe.str(value)}{extra != null ? ` (${safe.price(extra)})` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Data Source */}
          <div className="text-center text-xs text-gray-500 py-2">
            {language === 'fa' ? 'منبع داده' : 'Data source'}: {safe.str(analysis.data_source)} ·
            {' '}{safe.str(analysis.data_points)} {language === 'fa' ? 'نقطه داده' : 'data points'} ·
            {' '}{safe.str(analysis.execution_time_ms)}ms
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPanel;

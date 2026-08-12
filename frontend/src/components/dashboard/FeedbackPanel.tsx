import React, { useState, useEffect, useCallback } from 'react';
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
  pct: (v: any): string => safe.num(v, 0).toFixed(1),
};

interface PerformanceMetrics {
  win_rate: number;
  total_signals: number;
  avg_return: number;
  profit_factor: number;
  sharpe_ratio: number;
  factor_analysis: Record<string, any>;
  insights: string[];
  days: number;
}

interface Insight {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  confidence: number;
  impact_score: number;
  related_symbols: string[];
  related_factors: string[];
  supporting_evidence: string[];
  was_implemented: boolean;
  created_at: string;
}

interface FeedbackCycle {
  id: string;
  cycle_type: string;
  status: string;
  signals_evaluated: number;
  signals_correct: number;
  insights_generated: number;
  weights_adjusted: boolean;
  pre_cycle_accuracy: number;
  post_cycle_accuracy: number;
  summary: string;
  recommendations: string[];
  started_at: string;
  completed_at: string;
}

export const FeedbackPanel: React.FC = () => {
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'performance' | 'insights' | 'cycles' | 'record'>('performance');
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [cycles, setCycles] = useState<FeedbackCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningCycle, setRunningCycle] = useState(false);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  // Record outcome state
  const [recordForm, setRecordForm] = useState({
    signal_id: '',
    exit_price: '',
    profit_loss_percent: '',
    holding_period_hours: '',
    notes: '',
  });
  const [recording, setRecording] = useState(false);

  const loadPerformance = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`/feedback/performance/results/performance/?days=${lookbackDays}`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      } else {
        // Default empty metrics
        setMetrics({
          win_rate: 0, total_signals: 0, avg_return: 0,
          profit_factor: 0, sharpe_ratio: 0,
          factor_analysis: {}, insights: [], days: lookbackDays,
        });
      }
    } catch (err) {
      console.error('Failed to load performance:', err);
      setError(language === 'fa' ? 'خطا در بارگذاری عملکرد' : 'Failed to load performance');
    } finally {
      setLoading(false);
    }
  }, [lookbackDays, language]);

  const loadInsights = useCallback(async () => {
    try {
      const response = await apiFetch('/feedback/performance/insights/?limit=20');
      if (response.ok) {
        const data = await response.json();
        setInsights(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to load insights');
    }
  }, []);

  const loadCycles = useCallback(async () => {
    try {
      const response = await apiFetch('/feedback/cycles/history/?limit=10');
      if (response.ok) {
        const data = await response.json();
        setCycles(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to load cycles');
    }
  }, []);

  useEffect(() => {
    loadPerformance();
    loadInsights();
    loadCycles();
  }, [loadPerformance, loadInsights, loadCycles]);

  const runFeedbackCycle = async (cycleType: string) => {
    try {
      setRunningCycle(true);
      setError(null);
      const response = await apiFetch('/feedback/cycles/run_cycle/', {
        method: 'POST',
        body: JSON.stringify({
          cycle_type: cycleType,
          lookback_days: lookbackDays,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setCycles(prev => [data, ...prev]);
        // Reload performance after cycle
        loadPerformance();
        loadInsights();
      } else {
        const err = await response.json();
        setError(err.error || 'Failed to run cycle');
      }
    } catch (err) {
      setError(language === 'fa' ? 'خطا در اجرای چرخه' : 'Failed to run feedback cycle');
    } finally {
      setRunningCycle(false);
    }
  };

  const recordOutcome = async () => {
    if (!recordForm.signal_id || !recordForm.exit_price || !recordForm.profit_loss_percent) {
      setError(language === 'fa' ? 'لطفاً فیلدهای ضروری را پر کنید' : 'Please fill required fields');
      return;
    }
    try {
      setRecording(true);
      setError(null);
      const response = await apiFetch('/feedback/signal-memories/record_outcome/', {
        method: 'POST',
        body: JSON.stringify({
          signal_id: recordForm.signal_id,
          exit_price: parseFloat(recordForm.exit_price),
          profit_loss_percent: parseFloat(recordForm.profit_loss_percent),
          holding_period_hours: parseInt(recordForm.holding_period_hours || '0'),
        }),
      });
      if (response.ok) {
        setRecordForm({ signal_id: '', exit_price: '', profit_loss_percent: '', holding_period_hours: '', notes: '' });
        loadPerformance();
      } else {
        const err = await response.json();
        setError(err.error || 'Failed to record outcome');
      }
    } catch (err) {
      setError(language === 'fa' ? 'خطا در ثبت نتیجه' : 'Failed to record outcome');
    } finally {
      setRecording(false);
    }
  };

  const getMetricColor = (value: number, type: 'rate' | 'score') => {
    if (type === 'rate') {
      if (value >= 60) return 'text-green-400';
      if (value >= 40) return 'text-yellow-400';
      return 'text-red-400';
    }
    if (value >= 70) return 'text-green-400';
    if (value >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getInsightIcon = (type: string) => {
    const icons: Record<string, string> = {
      weight_adjustment: '⚖️',
      strategy_recommendation: '🎯',
      risk_alert: '⚠️',
      performance_analysis: '📊',
      market_regime_change: '🔄',
      factor_importance: '📈',
    };
    return icons[type] || '💡';
  };

  const tabs = [
    { id: 'performance' as const, label: language === 'fa' ? 'عملکرد' : 'Performance', icon: '📊' },
    { id: 'insights' as const, label: language === 'fa' ? 'بینش‌ها' : 'Insights', icon: '🧠' },
    { id: 'cycles' as const, label: language === 'fa' ? 'چرخه‌ها' : 'Cycles', icon: '🔄' },
    { id: 'record' as const, label: language === 'fa' ? 'ثبت نتیجه' : 'Record', icon: '📝' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">
          {language === 'fa' ? '🧠 حلقه بازخورد و یادگیری' : '🧠 AI Feedback & Learning'}
        </h2>
        <div className="flex items-center gap-2">
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(parseInt(e.target.value))}
            className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600"
          >
            <option value={7}>7D</option>
            <option value={14}>14D</option>
            <option value={30}>30D</option>
            <option value={90}>90D</option>
          </select>
          <button
            onClick={loadPerformance}
            disabled={loading}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '...' : '🔄'}
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

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-4">
          {loading && !metrics ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
              <p className="text-gray-400">{language === 'fa' ? 'در حال بارگذاری...' : 'Loading...'}</p>
            </div>
          ) : metrics ? (
            <>
              {/* Metric Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'نرخ برد' : 'Win Rate'}</div>
                  <div className={`text-2xl font-bold ${getMetricColor(metrics.win_rate, 'rate')}`}>
                    {safe.num(metrics.win_rate).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'کل سیگنال‌ها' : 'Total Signals'}</div>
                  <div className="text-2xl font-bold text-white">{metrics.total_signals}</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'میانگین بازگشت' : 'Avg Return'}</div>
                  <div className={`text-2xl font-bold ${safe.num(metrics.avg_return) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {safe.num(metrics.avg_return) >= 0 ? '+' : ''}{safe.num(metrics.avg_return).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'فاکتور سود' : 'Profit Factor'}</div>
                  <div className={`text-2xl font-bold ${getMetricColor(safe.num(metrics.profit_factor) * 100, 'score')}`}>
                    {safe.num(metrics.profit_factor).toFixed(2)}
                  </div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">Sharpe Ratio</div>
                  <div className={`text-2xl font-bold ${getMetricColor(safe.num(metrics.sharpe_ratio) * 50, 'score')}`}>
                    {safe.num(metrics.sharpe_ratio).toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Factor Analysis */}
              {Object.keys(metrics.factor_analysis).length > 0 && (
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">
                    {language === 'fa' ? 'عملکرد فاکتورها' : 'Factor Performance'}
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(metrics.factor_analysis).map(([factor, data]: [string, any]) => {
                      const winRate = safe.num(data?.win_rate, 50);
                      const count = safe.num(data?.total_signals, 0);
                      return (
                        <div key={factor}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-gray-300 capitalize">{factor}</span>
                            <span className="text-xs text-gray-500">{count} signals</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
                              <div
                                className={`h-full rounded transition-all ${getMetricColor(winRate, 'rate') === 'text-green-400' ? 'bg-green-500' : getMetricColor(winRate, 'rate') === 'text-yellow-400' ? 'bg-yellow-500' : 'bg-red-500'}`}
                                style={{ width: `${Math.min(100, Math.max(0, winRate))}%` }}
                              />
                            </div>
                            <span className={`text-xs font-mono w-12 text-right ${getMetricColor(winRate, 'rate')}`}>
                              {winRate.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* AI Insights from Performance */}
              {metrics.insights && metrics.insights.length > 0 && (
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">
                    {language === 'fa' ? 'تفسیر هوش مصنوعی' : 'AI Interpretation'}
                  </h3>
                  <div className="space-y-2">
                    {metrics.insights.map((insight, i) => (
                      <div key={i} className="text-sm text-gray-300 p-2 bg-gray-800 rounded">
                        💡 {insight}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {metrics.total_signals === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <p className="text-lg mb-2">{language === 'fa' ? 'هنوز داده‌ای وجود ندارد' : 'No data yet'}</p>
                  <p className="text-sm">
                    {language === 'fa'
                      ? 'سیگنال‌ها را تولید کنید و نتایج آنها را ثبت کنید تا AI از آنها یاد بگیرد'
                      : 'Generate signals and record their outcomes so the AI learns from them'}
                  </p>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-3">
          {insights.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-4">🧠</div>
              <p className="text-lg mb-2">{language === 'fa' ? 'هنوز بینشی تولید نشده' : 'No insights yet'}</p>
              <p className="text-sm">
                {language === 'fa'
                  ? 'چرخه بازخورد را اجرا کنید تا هوش مصنوعی بینش‌های جدید تولید کند'
                  : 'Run a feedback cycle to generate AI insights'}
              </p>
              <button
                onClick={() => runFeedbackCycle('daily')}
                disabled={runningCycle}
                className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {runningCycle ? '...' : language === 'fa' ? '🔄 اجرای چرخه' : '🔄 Run Feedback Cycle'}
              </button>
            </div>
          ) : (
            insights.map((insight) => (
              <div
                key={insight.id}
                className={`bg-gray-900 rounded-lg p-4 border ${
                  insight.was_implemented ? 'border-green-500/30' : 'border-gray-700'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getInsightIcon(insight.insight_type)}</span>
                    <div>
                      <h4 className="text-sm font-semibold text-white">{insight.title}</h4>
                      <span className="text-xs text-gray-500 capitalize">{insight.insight_type.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {insight.was_implemented && (
                      <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded">✓ Implemented</span>
                    )}
                    <span className="text-xs text-gray-500">
                      {new Date(insight.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-300 mb-2">{insight.description}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>Confidence: {(safe.num(insight.confidence) * 100).toFixed(0)}%</span>
                  <span>Impact: {(safe.num(insight.impact_score) * 100).toFixed(0)}%</span>
                  {insight.related_symbols.length > 0 && (
                    <span>Symbols: {insight.related_symbols.join(', ')}</span>
                  )}
                </div>
                {insight.supporting_evidence.length > 0 && (
                  <div className="mt-2 p-2 bg-gray-800 rounded text-xs text-gray-400">
                    <strong>Evidence:</strong> {insight.supporting_evidence.join(' · ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Cycles Tab */}
      {activeTab === 'cycles' && (
        <div className="space-y-4">
          {/* Run Cycle Buttons */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {[
              { type: 'daily', label: language === 'fa' ? 'روزانه' : 'Daily', icon: '📅' },
              { type: 'weekly', label: language === 'fa' ? 'هفتگی' : 'Weekly', icon: '📆' },
              { type: 'signal_based', label: language === 'fa' ? 'بر اساس سیگنال' : 'Signal-Based', icon: '🎯' },
              { type: 'manual', label: language === 'fa' ? 'دستی' : 'Manual', icon: '🔧' },
            ].map(({ type, label, icon }) => (
              <button
                key={type}
                onClick={() => runFeedbackCycle(type)}
                disabled={runningCycle}
                className="p-3 bg-gray-900 border border-gray-700 rounded-lg text-center hover:border-blue-500 transition-colors disabled:opacity-50"
              >
                <div className="text-lg mb-1">{icon}</div>
                <div className="text-xs text-gray-300">{label}</div>
                {runningCycle && <div className="text-xs text-blue-400 mt-1">Running...</div>}
              </button>
            ))}
          </div>

          {/* Cycle History */}
          {cycles.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-4">🔄</div>
              <p>{language === 'fa' ? 'هنوز چرخه‌ای اجرا نشده' : 'No cycles run yet'}</p>
            </div>
          ) : (
            cycles.map((cycle) => (
              <div key={cycle.id} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      cycle.status === 'completed' ? 'bg-green-400' :
                      cycle.status === 'running' ? 'bg-blue-400 animate-pulse' : 'bg-red-400'
                    }`}></span>
                    <span className="text-sm font-medium text-white capitalize">{cycle.cycle_type.replace(/_/g, ' ')}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      cycle.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      cycle.status === 'running' ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/20 text-red-400'
                    }`}>{cycle.status}</span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(cycle.started_at).toLocaleString()}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-3 text-xs text-gray-400 mb-2">
                  <div>Signals: {cycle.signals_evaluated}</div>
                  <div>Correct: {cycle.signals_correct}</div>
                  <div>Insights: {cycle.insights_generated}</div>
                  <div>Weights: {cycle.weights_adjusted ? '✓' : '—'}</div>
                </div>
                {cycle.pre_cycle_accuracy > 0 && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-500">Accuracy:</span>
                    <span className="text-red-400">{Number(cycle.pre_cycle_accuracy).toFixed(1)}%</span>
                    <span>→</span>
                    <span className="text-green-400">{Number(cycle.post_cycle_accuracy).toFixed(1)}%</span>
                  </div>
                )}
                {cycle.summary && (
                  <p className="text-xs text-gray-400 mt-2 p-2 bg-gray-800 rounded">{cycle.summary}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Record Tab */}
      {activeTab === 'record' && (
        <div className="max-w-md mx-auto space-y-4">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              {language === 'fa' ? 'ثبت نتیجه سیگنال' : 'Record Signal Outcome'}
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              {language === 'fa'
                ? 'نتیجه سیگنال خود را ثبت کنید تا AI از آن یاد بگیرد'
                : 'Record the outcome of a signal so the AI learns from it'}
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  {language === 'fa' ? 'شناسه سیگنال' : 'Signal ID'} *
                </label>
                <input
                  type="text"
                  value={recordForm.signal_id}
                  onChange={(e) => setRecordForm(prev => ({ ...prev, signal_id: e.target.value }))}
                  placeholder="UUID of the signal"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">
                    {language === 'fa' ? 'قیمت خروج' : 'Exit Price'} *
                  </label>
                  <input
                    type="number"
                    value={recordForm.exit_price}
                    onChange={(e) => setRecordForm(prev => ({ ...prev, exit_price: e.target.value }))}
                    placeholder="64500"
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">
                    {language === 'fa' ? 'درصد سود/ضرر' : 'P/L %'} *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={recordForm.profit_loss_percent}
                    onChange={(e) => setRecordForm(prev => ({ ...prev, profit_loss_percent: e.target.value }))}
                    placeholder="2.5"
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  {language === 'fa' ? 'مدت نگهداری (ساعت)' : 'Holding Period (hours)'}
                </label>
                <input
                  type="number"
                  value={recordForm.holding_period_hours}
                  onChange={(e) => setRecordForm(prev => ({ ...prev, holding_period_hours: e.target.value }))}
                  placeholder="48"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                />
              </div>
              <button
                onClick={recordOutcome}
                disabled={recording}
                className="w-full py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 disabled:opacity-50 text-sm font-medium"
              >
                {recording ? '...' : language === 'fa' ? '📝 ثبت نتیجه' : '📝 Record Outcome'}
              </button>
            </div>
          </div>

          {/* How it works */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">
              {language === 'fa' ? 'چگونه کار می‌کند؟' : 'How does it work?'}
            </h3>
            <div className="space-y-2 text-xs text-gray-400">
              <p>1. {language === 'fa' ? 'سیگنال تولید کنید (در تب سیگنال‌ها)' : 'Generate a signal (in Signals tab)'}</p>
              <p>2. {language === 'fa' ? 'معامله کنید و منتظر بمانید' : 'Trade it and wait'}</p>
              <p>3. {language === 'fa' ? 'نتیجه را اینجا ثبت کنید' : 'Record the outcome here'}</p>
              <p>4. {language === 'fa' ? 'AI از الگوها یاد می‌گیرد و وزن‌ها را تنظیم می‌کند' : 'AI learns patterns and adjusts factor weights'}</p>
              <p>5. {language === 'fa' ? 'چرخه بازخورد را اجرا کنید تا بینش‌های جدید تولید شود' : 'Run feedback cycles to generate new insights'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackPanel;

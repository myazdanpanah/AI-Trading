import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';
import { WeightHistoryChart } from './WeightHistoryChart';

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
};

interface PerformanceMetrics {
  status: string;
  total_signals: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_return: number;
  profit_factor: number;
  sharpe_ratio: number;
  avg_win: number;
  avg_loss: number;
  factor_analysis: Record<string, { total_signals: number; win_rate: number; avg_return: number }>;
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
  was_implemented: boolean;
  created_at: string;
}

export const FeedbackPanel: React.FC = () => {
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'performance' | 'insights' | 'cycles' | 'record'>('performance');
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [cycles, setCycles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningCycle, setRunningCycle] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<any>(null);

  // Record outcome state
  const [recordForm, setRecordForm] = useState({ signal_id: '', exit_price: '', profit_loss_percent: '', holding_period_hours: '' });
  const [recording, setRecording] = useState(false);

  const loadPerformance = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Get performance from signal memories
      const resp = await apiFetch(`/feedback/signal-memories/?limit=100`);
      if (resp.ok) {
        const data = await resp.json();
        const memories = data.results || data || [];
        const total = memories.length;
        const correct = memories.filter((m: any) => m.was_correct).length;
        const winRate = total > 0 ? (correct / total) * 100 : 0;
        const returns = memories.map((m: any) => parseFloat(m.actual_return_percent || 0));
        const avgReturn = returns.length > 0 ? returns.reduce((a: number, b: number) => a + b, 0) / returns.length : 0;
        const wins = returns.filter((r: number) => r > 0);
        const losses = returns.filter((r: number) => r < 0).map((r: number) => Math.abs(r));
        const avgWin = wins.length > 0 ? wins.reduce((a: number, b: number) => a + b, 0) / wins.length : 0;
        const avgLoss = losses.length > 0 ? losses.reduce((a: number, b: number) => a + b, 0) / losses.length : 1;
        const profitFactor = avgLoss > 0 ? avgWin / avgLoss : avgWin > 0 ? 99 : 0;

        // Factor analysis
        const factorAnalysis: Record<string, any> = {};
        for (const mem of memories) {
          const factors = mem.factors_at_creation || {};
          for (const [factor, score] of Object.entries(factors)) {
            if (!factorAnalysis[factor]) factorAnalysis[factor] = { total: 0, correct: 0, returns: [] };
            factorAnalysis[factor].total++;
            if (mem.was_correct) factorAnalysis[factor].correct++;
            factorAnalysis[factor].returns.push(parseFloat(mem.actual_return_percent || 0));
          }
        }
        const factorResult: Record<string, any> = {};
        for (const [factor, data] of Object.entries(factorAnalysis)) {
          const d = data as any;
          factorResult[factor] = {
            total_signals: d.total,
            win_rate: d.total > 0 ? (d.correct / d.total) * 100 : 0,
            avg_return: d.returns.length > 0 ? d.returns.reduce((a: number, b: number) => a + b, 0) / d.returns.length : 0,
          };
        }

        setMetrics({
          status: total > 0 ? 'complete' : 'no_data',
          total_signals: total,
          wins: correct,
          losses: total - correct,
          win_rate: winRate,
          avg_return: avgReturn,
          profit_factor: profitFactor,
          sharpe_ratio: avgLoss > 0 ? avgReturn / avgLoss : 0,
          avg_win: avgWin,
          avg_loss: avgLoss,
          factor_analysis: factorResult,
          days: lookbackDays,
        });
      }
    } catch (err) {
      console.error('Failed to load performance:', err);
    } finally {
      setLoading(false);
    }
  }, [lookbackDays]);

  const loadInsights = useCallback(async () => {
    try {
      const resp = await apiFetch('/feedback/insights/?limit=20');
      if (resp.ok) {
        const data = await resp.json();
        setInsights(data.results || data || []);
      }
    } catch {}
  }, []);

  const loadCycles = useCallback(async () => {
    try {
      const resp = await apiFetch('/feedback/cycles/?limit=10');
      if (resp.ok) {
        const data = await resp.json();
        setCycles(data.results || data || []);
      }
    } catch {}
  }, []);

  useEffect(() => { loadPerformance(); loadInsights(); loadCycles(); }, [loadPerformance, loadInsights, loadCycles]);

  const evaluateSignals = async () => {
    try {
      setEvaluating(true);
      setError(null);
      const resp = await apiFetch('/signals/signals/evaluate/', { method: 'POST' });
      if (resp.ok) {
        const data = await resp.json();
        setEvalResult(data);
        loadPerformance(); // Reload after evaluation
      } else {
        const err = await resp.json();
        setError(err.error || 'Failed to evaluate');
      }
    } catch {
      setError('Failed to evaluate signals');
    } finally {
      setEvaluating(false);
    }
  };

  const runFeedbackCycle = async (cycleType: string) => {
    try {
      setRunningCycle(true);
      setError(null);
      const resp = await apiFetch('/feedback/cycles/run_cycle/', {
        method: 'POST',
        body: JSON.stringify({ cycle_type: cycleType, lookback_days: lookbackDays }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setCycles(prev => [data, ...prev]);
        loadInsights();
      } else {
        const err = await resp.json();
        setError(err.error || 'Failed to run cycle');
      }
    } catch {
      setError('Failed to run feedback cycle');
    } finally {
      setRunningCycle(false);
    }
  };

  const recordOutcome = async () => {
    if (!recordForm.signal_id || !recordForm.exit_price || !recordForm.profit_loss_percent) {
      setError('Fill required fields');
      return;
    }
    try {
      setRecording(true);
      const resp = await apiFetch('/feedback/signal-memories/record_outcome/', {
        method: 'POST',
        body: JSON.stringify({
          signal_id: recordForm.signal_id,
          exit_price: parseFloat(recordForm.exit_price),
          profit_loss_percent: parseFloat(recordForm.profit_loss_percent),
          holding_period_hours: parseInt(recordForm.holding_period_hours || '0'),
        }),
      });
      if (resp.ok) {
        setRecordForm({ signal_id: '', exit_price: '', profit_loss_percent: '', holding_period_hours: '' });
        loadPerformance();
      } else {
        const err = await resp.json();
        setError(err.error || 'Failed to record');
      }
    } catch {
      setError('Failed to record outcome');
    } finally {
      setRecording(false);
    }
  };

  const getBarColor = (val: number) => val >= 60 ? 'bg-green-500' : val >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  const getTextColor = (val: number) => val >= 60 ? 'text-green-400' : val >= 40 ? 'text-yellow-400' : 'text-red-400';

  const tabs = [
    { id: 'performance' as const, label: language === 'fa' ? 'عملکرد' : 'Performance', icon: '📊' },
    { id: 'insights' as const, label: language === 'fa' ? 'بینش‌ها' : 'Insights', icon: '🧠' },
    { id: 'cycles' as const, label: language === 'fa' ? 'چرخه‌ها' : 'Cycles', icon: '🔄' },
    { id: 'record' as const, label: language === 'fa' ? 'ثبت نتیجه' : 'Record', icon: '📝' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">{language === 'fa' ? '🧠 حلقه بازخورد و یادگیری' : '🧠 AI Feedback & Learning'}</h2>
        <div className="flex items-center gap-2">
          <button onClick={evaluateSignals} disabled={evaluating} className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50">
            {evaluating ? '...' : '⚡ ' + (language === 'fa' ? 'ارزیابی سیگنال‌ها' : 'Evaluate Signals')}
          </button>
          <select value={lookbackDays} onChange={(e) => setLookbackDays(parseInt(e.target.value))} className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600">
            <option value={7}>7D</option>
            <option value={14}>14D</option>
            <option value={30}>30D</option>
            <option value={90}>90D</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="text-red-400">✕</button>
        </div>
      )}

      {evalResult && (
        <div className="mb-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-300 text-sm">
          ✅ Evaluated {evalResult.evaluated} signals: {evalResult.wins} wins, {evalResult.losses} losses ({evalResult.win_rate?.toFixed(1)}% win rate)
          <button onClick={() => setEvalResult(null)} className="ml-2 text-green-400">✕</button>
        </div>
      )}

      <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div></div>
          ) : metrics ? (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'نرخ برد' : 'Win Rate'}</div>
                  <div className={`text-2xl font-bold ${getTextColor(metrics.win_rate)}`}>{metrics.win_rate.toFixed(1)}%</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'کل سیگنال‌ها' : 'Total Signals'}</div>
                  <div className="text-2xl font-bold text-white">{metrics.total_signals}</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'میانگین بازگشت' : 'Avg Return'}</div>
                  <div className={`text-2xl font-bold ${metrics.avg_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>{metrics.avg_return >= 0 ? '+' : ''}{metrics.avg_return.toFixed(2)}%</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">{language === 'fa' ? 'فاکتور سود' : 'Profit Factor'}</div>
                  <div className={`text-2xl font-bold ${getTextColor(metrics.profit_factor * 30)}`}>{metrics.profit_factor.toFixed(2)}</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
                  <div className="text-xs text-gray-400 mb-1">Sharpe</div>
                  <div className={`text-2xl font-bold ${getTextColor(metrics.sharpe_ratio * 50 + 30)}`}>{metrics.sharpe_ratio.toFixed(2)}</div>
                </div>
              </div>

              {metrics.total_signals > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                    <div className="text-xs text-green-400 mb-1">{language === 'fa' ? 'میانگین سود' : 'Avg Win'}</div>
                    <div className="text-lg font-bold text-green-400">+{metrics.avg_win.toFixed(2)}%</div>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                    <div className="text-xs text-red-400 mb-1">{language === 'fa' ? 'میانگین ضرر' : 'Avg Loss'}</div>
                    <div className="text-lg font-bold text-red-400">-{metrics.avg_loss.toFixed(2)}%</div>
                  </div>
                </div>
              )}

              {Object.keys(metrics.factor_analysis).length > 0 && (
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">{language === 'fa' ? 'عملکرد فاکتورها' : 'Factor Performance'}</h3>
                  <div className="space-y-3">
                    {Object.entries(metrics.factor_analysis).map(([factor, data]: [string, any]) => (
                      <div key={factor}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-300 capitalize">{factor}</span>
                          <span className="text-xs text-gray-500">{data.total_signals} signals</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
                            <div className={`h-full rounded transition-all ${getBarColor(data.win_rate)}`} style={{ width: `${Math.min(100, Math.max(0, data.win_rate))}%` }} />
                          </div>
                          <span className={`text-xs font-mono w-16 text-right ${getTextColor(data.win_rate)}`}>{data.win_rate.toFixed(1)}%</span>
                          <span className={`text-xs font-mono w-16 text-right ${data.avg_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>{data.avg_return >= 0 ? '+' : ''}{data.avg_return.toFixed(2)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {metrics.total_signals === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <p className="text-lg mb-2">{language === 'fa' ? 'هنوز داده‌ای نیست' : 'No data yet'}</p>
                  <p className="text-sm mb-4">{language === 'fa' ? 'سیگنال تولید کنید و دکمه ارزیابی را بزنید' : 'Generate signals and click Evaluate to start learning'}</p>
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
              <p className="text-lg mb-2">{language === 'fa' ? 'هنوز بینشی نیست' : 'No insights yet'}</p>
              <p className="text-sm mb-4">{language === 'fa' ? 'چرخه بازخورد را اجرا کنید' : 'Run a feedback cycle to generate insights'}</p>
              <button onClick={() => runFeedbackCycle('daily')} disabled={runningCycle} className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50">
                {runningCycle ? '...' : '🔄 Run Cycle'}
              </button>
            </div>
          ) : insights.map((insight) => (
            <div key={insight.id} className={`bg-gray-900 rounded-lg p-4 border ${insight.was_implemented ? 'border-green-500/30' : 'border-gray-700'}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="text-sm font-semibold text-white">{insight.title}</h4>
                  <span className="text-xs text-gray-500 capitalize">{insight.insight_type.replace(/_/g, ' ')}</span>
                </div>
                <span className="text-xs text-gray-500">{new Date(insight.created_at).toLocaleDateString('en-US', { timeZone: 'Asia/Tehran' })}</span>
              </div>
              <p className="text-sm text-gray-300 mb-2">{insight.description}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Confidence: {(safe.num(insight.confidence) * 100).toFixed(0)}%</span>
                <span>Impact: {(safe.num(insight.impact_score) * 100).toFixed(0)}%</span>
                {insight.related_symbols?.length > 0 && <span>Symbols: {insight.related_symbols.join(', ')}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cycles Tab */}
      {activeTab === 'cycles' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {[{ type: 'daily', label: 'Daily', icon: '📅' }, { type: 'weekly', label: 'Weekly', icon: '📆' }, { type: 'signal_based', label: 'Signal-Based', icon: '🎯' }, { type: 'manual', label: 'Manual', icon: '🔧' }].map(({ type, label, icon }) => (
              <button key={type} onClick={() => runFeedbackCycle(type)} disabled={runningCycle} className="p-3 bg-gray-900 border border-gray-700 rounded-lg text-center hover:border-blue-500 transition-colors disabled:opacity-50">
                <div className="text-lg mb-1">{icon}</div>
                <div className="text-xs text-gray-300">{label}</div>
              </button>
            ))}
          </div>

          {cycles.length === 0 ? (
            <div className="text-center py-8 text-gray-500"><div className="text-4xl mb-4">🔄</div><p>No cycles run yet</p></div>
          ) : cycles.map((cycle: any) => (
            <div key={cycle.id || cycle.cycle_id} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${cycle.status === 'completed' ? 'bg-green-400' : cycle.status === 'running' ? 'bg-blue-400 animate-pulse' : 'bg-red-400'}`}></span>
                  <span className="text-sm font-medium text-white capitalize">{(cycle.cycle_type || '').replace(/_/g, ' ')}</span>
                </div>
                <span className="text-xs text-gray-500">{cycle.started_at ? new Date(cycle.started_at).toLocaleString('en-US', { timeZone: 'Asia/Tehran' }) : ''}</span>
              </div>
              {cycle.steps && (
                <div className="text-xs text-gray-400 mt-2">
                  Signals: {cycle.steps.collection?.signals_found || 0} | Insights: {cycle.steps.insights?.insights_generated || 0}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Record Tab */}
      {activeTab === 'record' && (
        <div className="max-w-md mx-auto space-y-4">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Record Signal Outcome</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Signal ID *</label>
                <input type="text" value={recordForm.signal_id} onChange={(e) => setRecordForm(prev => ({ ...prev, signal_id: e.target.value }))} placeholder="UUID of the signal" className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Exit Price *</label>
                  <input type="number" value={recordForm.exit_price} onChange={(e) => setRecordForm(prev => ({ ...prev, exit_price: e.target.value }))} placeholder="64500" className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">P/L % *</label>
                  <input type="number" step="0.1" value={recordForm.profit_loss_percent} onChange={(e) => setRecordForm(prev => ({ ...prev, profit_loss_percent: e.target.value }))} placeholder="2.5" className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Holding Period (hours)</label>
                <input type="number" value={recordForm.holding_period_hours} onChange={(e) => setRecordForm(prev => ({ ...prev, holding_period_hours: e.target.value }))} placeholder="48" className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm" />
              </div>
              <button onClick={recordOutcome} disabled={recording} className="w-full py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 disabled:opacity-50 text-sm font-medium">
                {recording ? '...' : '📝 Record Outcome'}
              </button>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">How the Feedback Loop Works</h3>
            <div className="space-y-2 text-xs text-gray-400">
              <p>1. Generate signal (Signals tab)</p>
              <p>2. Click "Evaluate Signals" above — system checks what happened to price</p>
              <p>3. Outcomes recorded as SignalMemory in database</p>
              <p>4. AI analyzes patterns: which factors were right, which were wrong</p>
              <p>5. Run feedback cycle to generate insights and adjust weights</p>
              <p>6. Next signals benefit from learned patterns</p>
            </div>
          </div>

          {/* Weight History Chart */}
          <div className="mt-6">
            <WeightHistoryChart />
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackPanel;

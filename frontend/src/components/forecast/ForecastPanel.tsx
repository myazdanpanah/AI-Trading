import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';

interface Forecast {
  id: number;
  symbol: string;
  current_price: number;
  predicted_price: number;
  direction: string;
  confidence: number;
  scores: {
    technical: number;
    regime: number;
    momentum: number;
    volatility: number;
  };
  forecast_time: string;
  target_time: string;
  status: string;
  actual_price?: number;
  actual_direction?: string;
  price_error_pct?: number;
  direction_correct?: boolean;
  points_earned?: number;
}

interface AccuracyStats {
  total: number;
  correct: number;
  accuracy_rate: number;
  avg_confidence: number;
  avg_error_pct: number;
  total_points: number;
}

interface LearningStats {
  symbol: string;
  current_weights: Record<string, number>;
  accuracy_rate: number;
  total_predictions: number;
  adjustment_count: number;
  last_adjustment: string;
  recent_adjustments: any[];
}

export const ForecastPanel: React.FC = () => {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [stats, setStats] = useState<AccuracyStats | null>(null);
  const [learning, setLearning] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [activeTab, setActiveTab] = useState<'forecasts' | 'accuracy' | 'learning'>('forecasts');
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [selectedSymbol]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [forecastRes, statsRes, learningRes] = await Promise.all([
        apiFetch(`/forecast/forecasts/?symbol=${selectedSymbol}`),
        apiFetch(`/forecast/accuracy/?symbol=${selectedSymbol}&days=30`),
        apiFetch(`/forecast/learning-stats/?symbol=${selectedSymbol}`),
      ]);

      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecasts(data.results || data);
      }
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      if (learningRes.ok) {
        setLearning(await learningRes.json());
      }
    } catch (err) {
      console.error('Failed to fetch forecast data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runFullCycle = async () => {
    setRunning(true);
    setMessage(null);
    try {
      const res = await apiFetch('/forecast/full-cycle/', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Cycle complete: ${data.forecast?.forecasts_created || 0} forecasts, ${data.verification?.verified || 0} verified`);
        fetchData();
      } else {
        setMessage('Failed to run cycle');
      }
    } catch (err) {
      setMessage('Network error');
    } finally {
      setRunning(false);
    }
  };

  const runForecasts = async () => {
    setRunning(true);
    setMessage(null);
    try {
      const res = await apiFetch('/forecast/run/', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Created ${data.forecasts_created} forecasts`);
        fetchData();
      }
    } catch (err) {
      setMessage('Failed');
    } finally {
      setRunning(false);
    }
  };

  const verifyForecasts = async () => {
    setRunning(true);
    setMessage(null);
    try {
      const res = await apiFetch('/forecast/verify/', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Verified ${data.verified} forecasts: ${data.accuracy_rate?.toFixed(1)}% accuracy`);
        fetchData();
      }
    } catch (err) {
      setMessage('Failed');
    } finally {
      setRunning(false);
    }
  };

  const getDirectionColor = (dir: string) => {
    if (dir === 'UP') return 'text-green-400';
    if (dir === 'DOWN') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getDirectionIcon = (dir: string) => {
    if (dir === 'UP') return '↑';
    if (dir === 'DOWN') return '↓';
    return '→';
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-purple-500 border-t-transparent mx-auto" />
          <p className="text-gray-400 mt-3">Loading forecasts...</p>
        </div>
      </div>
    );
  }

  const weightBars = learning?.current_weights ? Object.entries(learning.current_weights).map(([key, value]) => ({
    label: key.charAt(0).toUpperCase() + key.slice(1),
    value: value * 100,
  })) : [];

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🔮 Price Forecasts</h1>
          <p className="text-gray-400 text-sm">AI predictions verified against real market data</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Cycle runs every 6 hours</span>
        </div>
      </div>

      {/* Symbol Selector */}
      <div className="flex gap-2">
        {['BTC', 'ETH', 'SOL', 'BNB', 'XRP'].map((sym) => (
          <button key={sym} onClick={() => setSelectedSymbol(sym)} className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${selectedSymbol === sym ? 'bg-purple-600 text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'}`}>
            {sym}
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={runFullCycle} disabled={running} className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm">
          {running ? 'Running...' : '🔄 Run Full Cycle'}
        </button>
        <button onClick={runForecasts} disabled={running} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm">
          🔮 Generate Forecasts
        </button>
        <button onClick={verifyForecasts} disabled={running} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm">
          ✅ Verify Predictions
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-blue-400 text-sm">
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 rounded-lg p-1 w-fit">
        {[
          { id: 'forecasts' as const, label: '🔮 Forecasts', count: forecasts.length },
          { id: 'accuracy' as const, label: '📊 Accuracy' },
          { id: 'learning' as const, label: '🧠 Learning' },
        ].map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'}`}>
            {tab.label} {tab.count !== undefined && `(${tab.count})`}
          </button>
        ))}
      </div>

      {/* Forecasts Tab */}
      {activeTab === 'forecasts' && (
        <div className="space-y-3">
          {forecasts.length === 0 ? (
            <div className="bg-white/5 rounded-xl p-8 text-center">
              <p className="text-gray-400 text-lg">No forecasts yet</p>
              <p className="text-gray-500 text-sm mt-2">Click "Generate Forecasts" to create predictions</p>
            </div>
          ) : (
            forecasts.map((f) => (
              <div key={f.id} className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-lg font-bold text-white">{f.symbol}/USD</span>
                      <div className="text-xs text-gray-500">Current: ${f.current_price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                    </div>
                    <div className="text-center">
                      <span className={`text-2xl font-bold ${getDirectionColor(f.direction)}`}>
                        {getDirectionIcon(f.direction)} {f.direction}
                      </span>
                      <div className="text-xs text-gray-500">→ ${f.predicted_price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                    </div>
                    <div className="text-center">
                      <span className="text-sm font-bold text-purple-400">{(f.confidence * 100).toFixed(0)}%</span>
                      <div className="text-xs text-gray-500">Confidence</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right text-xs text-gray-500">
                      <div>Target: {formatTime(f.target_time)}</div>
                      <div>Status: {f.status}</div>
                    </div>
                    {f.status === 'VERIFIED' && (
                      <div className={`text-center px-3 py-1 rounded-lg ${f.direction_correct ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        <div className="font-bold">{f.direction_correct ? '✓ Correct' : '✗ Wrong'}</div>
                        <div className="text-xs">{f.points_earned} pts</div>
                      </div>
                    )}
                  </div>
                </div>
                {/* Score bars */}
                <div className="flex gap-4 mt-3 text-xs">
                  {Object.entries(f.scores).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-1">
                      <span className="text-gray-500 capitalize">{key}:</span>
                      <span className="font-mono" style={{ color: val >= 60 ? '#10b981' : val >= 40 ? '#f59e0b' : '#ef4444' }}>
                        {typeof val === 'number' ? val.toFixed(1) : val}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Accuracy Tab */}
      {activeTab === 'accuracy' && stats && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-purple-400">{stats.accuracy_rate.toFixed(1)}%</div>
              <div className="text-sm text-gray-400 mt-1">Accuracy Rate</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-white">{stats.total}</div>
              <div className="text-sm text-gray-400 mt-1">Total Predictions</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-green-400">{stats.correct}</div>
              <div className="text-sm text-gray-400 mt-1">Correct</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-yellow-400">{stats.total_points}</div>
              <div className="text-sm text-gray-400 mt-1">Total Points</div>
            </div>
          </div>
          <div className="bg-white/5 rounded-xl p-5">
            <h3 className="text-lg font-semibold text-white mb-3">Accuracy Visualization</h3>
            <div className="w-full bg-white/10 rounded-full h-6">
              <div className="h-6 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all" style={{ width: `${stats.accuracy_rate}%` }} />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>0%</span>
              <span>Target: 60%+</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}

      {/* Learning Tab */}
      {activeTab === 'learning' && learning && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-purple-400">{(learning.accuracy_rate || 0).toFixed(1)}%</div>
              <div className="text-sm text-gray-400 mt-1">Model Accuracy</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-white">{learning.total_predictions}</div>
              <div className="text-sm text-gray-400 mt-1">Total Predictions</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-3xl font-bold text-blue-400">{learning.adjustment_count}</div>
              <div className="text-sm text-gray-400 mt-1">Adjustments Made</div>
            </div>
            <div className="bg-white/5 rounded-xl p-5 text-center">
              <div className="text-lg font-bold text-gray-300">{learning.last_adjustment ? formatTime(learning.last_adjustment) : 'Never'}</div>
              <div className="text-sm text-gray-400 mt-1">Last Adjustment</div>
            </div>
          </div>

          {/* Current Weights */}
          <div className="bg-white/5 rounded-xl p-5">
            <h3 className="text-lg font-semibold text-white mb-4">🧠 Current Model Weights</h3>
            <div className="space-y-3">
              {weightBars.map((w) => (
                <div key={w.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">{w.label}</span>
                    <span className="text-white font-mono">{w.value.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-3">
                    <div className="h-3 rounded-full bg-purple-500 transition-all" style={{ width: `${w.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">Weights are automatically adjusted based on which factors lead to correct predictions.</p>
          </div>

          {/* Recent Adjustments */}
          {learning.recent_adjustments && learning.recent_adjustments.length > 0 && (
            <div className="bg-white/5 rounded-xl p-5">
              <h3 className="text-lg font-semibold text-white mb-4">📝 Recent Weight Adjustments</h3>
              <div className="space-y-2">
                {learning.recent_adjustments.slice(0, 10).map((adj, i) => (
                  <div key={i} className="flex items-center justify-between bg-white/5 rounded-lg p-3 text-sm">
                    <div>
                      <span className="text-gray-400">{adj.factor}</span>
                      <span className="text-gray-600 mx-2">→</span>
                      <span className={adj.new_weight > adj.old_weight ? 'text-green-400' : 'text-red-400'}>
                        {adj.old_weight?.toFixed(3)} → {adj.new_weight?.toFixed(3)}
                      </span>
                    </div>
                    <span className="text-gray-500 text-xs">{adj.time ? formatTime(adj.time) : ''}</span>
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

export default ForecastPanel;

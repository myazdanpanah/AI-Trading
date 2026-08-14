import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

const safe = {
  num: (v: any, d = 0): number => {
    const n = parseFloat(v);
    return isNaN(n) ? d : n;
  },
  str: (v: any, d = ''): string => (v != null ? String(v) : d),
  obj: (v: any): Record<string, any> => (v && typeof v === 'object' ? v : {}),
  arr: (v: any): any[] => (Array.isArray(v) ? v : []),
};

interface SignalVersion {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  composite_score: number;
  timeframe: string;
  created_at: string;
}

interface LineageData {
  signal_id: string;
  lineage: {
    strategy_version: string;
    feature_version: string;
    model_version: string;
    prompt_version: string;
    ensemble_version: string;
    risk_version: string;
    regime: string;
    regime_confidence: number;
    weights_snapshot: Record<string, number>;
    factor_scores: Record<string, number>;
    market_snapshot: Record<string, any>;
    news_snapshot: Record<string, any>;
    social_snapshot: Record<string, any>;
    derivatives_snapshot: Record<string, any>;
    llm_context: Record<string, any>;
    llm_output: Record<string, any>;
    ensemble_output: Record<string, any>;
    risk_decision: Record<string, any>;
    created_at: string;
  };
  explanation: string;
}

export const ReproducibilityDashboard: React.FC = () => {
  const { language } = useLanguage();
  const [signals, setSignals] = useState<SignalVersion[]>([]);
  const [selectedSignalId, setSelectedSignalId] = useState<string>('');
  const [lineage, setLineage] = useState<LineageData | null>(null);
  const [versions, setVersions] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSignals();
    loadVersions();
  }, []);

  const loadSignals = async () => {
    try {
      const res = await apiFetch('/api/signals/signals/?format=json');
      const data = await res.json();
      const results = Array.isArray(data) ? data : data.results || [];
      setSignals(results.slice(0, 30));
      if (results.length > 0 && !selectedSignalId) {
        setSelectedSignalId(results[0].id);
      }
    } catch (e) {
      console.error('Failed to load signals:', e);
    }
  };

  const loadVersions = async () => {
    try {
      const res = await apiFetch('/api/signals/signals/versions/');
      const data = await res.json();
      setVersions(data);
    } catch (e) {
      console.error('Failed to load versions:', e);
    }
  };

  const loadLineage = async (signalId: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`/api/signals/signals/${signalId}/lineage/`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        setLineage(null);
      } else {
        setLineage(data);
      }
    } catch (e) {
      setError(String(e));
      setLineage(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedSignalId) {
      loadLineage(selectedSignalId);
    }
  }, [selectedSignalId]);

  const dirColor = (dir: string) => {
    if (dir === 'buy' || dir === 'bullish') return 'text-green-400';
    if (dir === 'sell' || dir === 'bearish') return 'text-red-400';
    return 'text-gray-400';
  };

  const renderVersionBadge = (label: string, version: string) => (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-900/30 border border-blue-700/50 rounded text-xs text-blue-300">
      <span className="font-semibold">{label}</span>
      <span>v{version}</span>
    </span>
  );

  const renderFactorBar = (name: string, score: number, weight: number) => {
    const contribution = score * weight;
    return (
      <div key={name} className="flex items-center gap-2">
        <span className="w-32 text-xs text-gray-400 truncate">{name}</span>
        <div className="flex-1 h-3 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-cyan-500 rounded-full transition-all"
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>
        <span className="w-16 text-xs text-right text-gray-300">{score.toFixed(1)}</span>
        <span className="w-12 text-xs text-right text-gray-500">{(weight * 100).toFixed(0)}%</span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            🔍 {language === 'fa' ? 'داشبورد بازتولیدپذیری' : 'Reproducibility Dashboard'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {language === 'fa'
              ? 'نسخه‌ها، داده‌ها و تصمیمات AI برای هر سیگنال'
              : 'Versions, data snapshots, and AI decisions for every signal'}
          </p>
        </div>
        <button
          onClick={() => { loadSignals(); loadVersions(); }}
          className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 text-sm"
        >
          🔄 {language === 'fa' ? 'بروزرسانی' : 'Refresh'}
        </button>
      </div>

      {/* System Versions */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">
          📦 {language === 'fa' ? 'نسخه‌های سیستم' : 'System Versions'}
        </h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(versions).map(([key, version]) => (
            <span
              key={key}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-700/50 border border-gray-600 rounded-lg text-xs"
            >
              <span className="text-gray-400">{key}:</span>
              <span className="text-white font-mono">v{version}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Signal Selector */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 max-h-[600px] overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            📋 {language === 'fa' ? 'سیگنال‌ها' : 'Signals'}
          </h3>
          <div className="space-y-1">
            {signals.map((sig) => (
              <button
                key={sig.id}
                onClick={() => setSelectedSignalId(sig.id)}
                className={`w-full text-left p-2 rounded-lg text-sm transition-colors ${
                  selectedSignalId === sig.id
                    ? 'bg-blue-600/20 border border-blue-600/50'
                    : 'hover:bg-gray-700/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-white">{sig.symbol}</span>
                  <span className={dirColor(sig.direction)}>{sig.direction.toUpperCase()}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-gray-400 text-xs">{sig.timeframe}</span>
                  <span className="text-gray-400 text-xs">{sig.confidence}%</span>
                </div>
                <div className="text-gray-500 text-xs mt-0.5">
                  {new Date(sig.created_at).toLocaleString()}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Lineage Detail */}
        <div className="lg:col-span-2 space-y-4">
          {loading && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
              <p className="text-gray-400 mt-2">Loading lineage...</p>
            </div>
          )}

          {error && (
            <div className="bg-gray-800 rounded-lg border border-red-700/50 p-4">
              <p className="text-red-400 text-sm">⚠️ {error}</p>
            </div>
          )}

          {!loading && !error && !lineage && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
              <p className="text-gray-400">
                {language === 'fa' ? 'خط سیری ثبت نشده' : 'No lineage data for this signal'}
              </p>
            </div>
          )}

          {!loading && lineage && lineage.lineage && (
            <>
              {/* Version Tags */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">
                  🏷️ {language === 'fa' ? 'نسخه‌های سیگنال' : 'Signal Versions'}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {renderVersionBadge('Strategy', lineage.lineage.strategy_version)}
                  {renderVersionBadge('Features', lineage.lineage.feature_version)}
                  {renderVersionBadge('Ensemble', lineage.lineage.ensemble_version)}
                  {renderVersionBadge('Risk', lineage.lineage.risk_version)}
                  {renderVersionBadge('Prompt', lineage.lineage.prompt_version)}
                  {lineage.lineage.model_version && (
                    renderVersionBadge('Model', lineage.lineage.model_version)
                  )}
                </div>
              </div>

              {/* Regime & Weights */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">
                  🎯 {language === 'fa' ? 'رژیم بازار و وزن‌ها' : 'Market Regime & Weights'}
                </h3>
                <div className="flex items-center gap-4 mb-4">
                  <span className="px-3 py-1 bg-purple-900/30 border border-purple-700/50 rounded-lg text-sm text-purple-300">
                    Regime: {lineage.lineage.regime}
                  </span>
                  <span className="text-xs text-gray-400">
                    Confidence: {(lineage.lineage.regime_confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="space-y-2">
                  {Object.entries(safe.obj(lineage.lineage.factor_scores)).map(([name, score]) => {
                    const weight = lineage.lineage.weights_snapshot[name] || 0;
                    return renderFactorBar(name, safe.num(score), weight);
                  })}
                </div>
              </div>

              {/* Human-readable Explanation */}
              {lineage.explanation && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">
                    💡 {language === 'fa' ? 'توضیح' : 'Explanation'}
                  </h3>
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                    {lineage.explanation}
                  </pre>
                </div>
              )}

              {/* Agent Ensemble Output */}
              {lineage.lineage.ensemble_output &&
                Object.keys(lineage.lineage.ensemble_output).length > 0 && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">
                    🤖 {language === 'fa' ? 'خروجی تیم AI' : 'Agent Ensemble Output'}
                  </h3>
                  <div className="flex items-center gap-4 mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      lineage.lineage.ensemble_output.verdict === 'validate'
                        ? 'bg-green-900/30 text-green-400 border border-green-700/50'
                        : lineage.lineage.ensemble_output.verdict === 'reject'
                        ? 'bg-red-900/30 text-red-400 border border-red-700/50'
                        : 'bg-yellow-900/30 text-yellow-400 border border-yellow-700/50'
                    }`}>
                      {lineage.lineage.ensemble_output.verdict?.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-400">
                      Model: {lineage.lineage.ensemble_output.model}
                    </span>
                    <span className="text-xs text-gray-400">
                      Agents: {lineage.lineage.ensemble_output.agents_succeeded}/5
                    </span>
                    <span className="text-xs text-gray-400">
                      {lineage.lineage.ensemble_output.total_latency_ms}ms
                    </span>
                  </div>

                  {/* Individual agent outputs */}
                  {Object.entries(safe.obj(lineage.lineage.ensemble_output.agent_analyses)).map(
                    ([name, agent]: [string, any]) => (
                      <div key={name} className="bg-gray-700/30 rounded-lg p-3 mb-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-white">{name}</span>
                          <span className={`text-xs ${
                            agent.success ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {agent.success ? '✅' : '❌'} {agent.latency_ms}ms
                          </span>
                        </div>
                        {agent.output && Object.entries(agent.output).map(([k, v]) => (
                          <div key={k} className="text-xs text-gray-400">
                            <span className="text-gray-500">{k}:</span>{' '}
                            {typeof v === 'object' ? JSON.stringify(v) : String(v).slice(0, 200)}
                          </div>
                        ))}
                      </div>
                    )
                  )}

                  {/* Reasons */}
                  {safe.arr(lineage.lineage.ensemble_output.reasons).length > 0 && (
                    <div className="mt-3">
                      <span className="text-xs text-gray-400 font-semibold">Reasons:</span>
                      {lineage.lineage.ensemble_output.reasons.map((r: string, i: number) => (
                        <p key={i} className="text-xs text-gray-400 mt-1">• {r}</p>
                      ))}
                    </div>
                  )}

                  {/* Risks */}
                  {safe.arr(lineage.lineage.ensemble_output.risks).length > 0 && (
                    <div className="mt-3">
                      <span className="text-xs text-gray-400 font-semibold">Risks:</span>
                      {lineage.lineage.ensemble_output.risks.map((r: string, i: number) => (
                        <p key={i} className="text-xs text-red-300/70 mt-1">⚠ {r}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Data Snapshots */}
              <div className="grid grid-cols-2 gap-4">
                {/* Market Snapshot */}
                {Object.keys(safe.obj(lineage.lineage.market_snapshot)).length > 0 && (
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">📈 Market</h3>
                    <div className="space-y-1">
                      {Object.entries(lineage.lineage.market_snapshot).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-gray-300 font-mono">{String(v).slice(0, 80)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* News Snapshot */}
                {Object.keys(safe.obj(lineage.lineage.news_snapshot)).length > 0 && (
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">📰 News</h3>
                    <div className="space-y-1">
                      {Object.entries(lineage.lineage.news_snapshot).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-gray-300 font-mono">{String(v).slice(0, 80)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Social Snapshot */}
                {Object.keys(safe.obj(lineage.lineage.social_snapshot)).length > 0 && (
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">🐦 Social</h3>
                    <div className="space-y-1">
                      {Object.entries(lineage.lineage.social_snapshot).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-gray-300 font-mono">{String(v).slice(0, 80)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Derivatives Snapshot */}
                {Object.keys(safe.obj(lineage.lineage.derivatives_snapshot)).length > 0 && (
                  <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2">📊 Derivatives</h3>
                    <div className="space-y-1">
                      {Object.entries(lineage.lineage.derivatives_snapshot).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-gray-300 font-mono">{String(v).slice(0, 80)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface LearningInsight {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  impact_score: number;
  related_symbols: string[];
  was_implemented: boolean;
  created_at: string;
}

interface FeedbackCycle {
  id: string;
  cycle_type: string;
  status: string;
  signals_evaluated: number;
  signals_correct: number;
  win_rate: number;
  insights_generated: number;
  summary: string;
  started_at: string;
  completed_at: string | null;
}

export const LearningInsights: React.FC = () => {
  const [insights, setInsights] = useState<LearningInsight[]>([]);
  const [cycles, setCycles] = useState<FeedbackCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'insights' | 'cycles' | 'analysis'>('insights');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [insightsRes, cyclesRes] = await Promise.all([
        apiFetch('/feedback/analysis/insights/'),
        apiFetch('/feedback/cycles/history/?limit=10'),
      ]);
      
      if (insightsRes.ok) setInsights(await insightsRes.json());
      if (cyclesRes.ok) setCycles(await cyclesRes.json());
    } catch (error) {
      console.error('Failed to fetch feedback data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runFeedbackCycle = async (cycleType: string = 'daily') => {
    try {
      const response = await apiFetch('/feedback/cycles/run_cycle/', {
        method: 'POST',
        body: JSON.stringify({ cycle_type: cycleType, lookback_days: cycleType === 'weekly' ? 7 : 1 }),
      });
      
      if (response.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('Failed to run feedback cycle:', error);
    }
  };

  const markInsightImplemented = async (insightId: string) => {
    try {
      await apiFetch(`/feedback/insights/${insightId}/implement/`, {
        method: 'POST',
        body: JSON.stringify({ result: 'Implemented' }),
      });
      fetchData();
    } catch (error) {
      console.error('Failed to mark insight:', error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 animate-pulse">
            <div className="h-4 bg-white/20 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-white/10 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  const tabs = [
    { id: 'insights' as const, label: 'Insights', icon: '💡', count: insights.length },
    { id: 'cycles' as const, label: 'Cycles', icon: '🔄', count: cycles.length },
    { id: 'analysis' as const, label: 'Analysis', icon: '📊', count: 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">🧠 Learning Feedback Loop</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => runFeedbackCycle('daily')}
            className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all shadow-lg shadow-green-500/25"
          >
            ▶️ Run Daily Cycle
          </button>
          <button
            onClick={() => runFeedbackCycle('weekly')}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg shadow-purple-500/25"
          >
            🔄 Run Weekly Cycle
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-white/5 rounded-xl p-1 border border-white/10">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium text-sm transition-all ${
              activeTab === tab.id
                ? 'bg-white/10 text-white shadow-lg'
                : 'text-purple-200/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.count > 0 && (
              <span className="px-2 py-0.5 text-xs bg-white/20 rounded-full">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          {insights.length === 0 ? (
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-12 text-center border border-white/10">
              <div className="text-4xl mb-4">💡</div>
              <p className="text-purple-200/60">No active insights. Run a feedback cycle to generate insights.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className={`bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:bg-white/15 transition-all ${
                    insight.was_implemented ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-500/20 text-blue-400">
                          {insight.type}
                        </span>
                        {insight.was_implemented && (
                          <span className="px-3 py-1 text-xs font-medium rounded-full bg-green-500/20 text-green-400">
                            ✓ Implemented
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-semibold text-white">{insight.title}</h3>
                      <p className="text-purple-200/60 mt-2">{insight.description}</p>
                      <div className="flex items-center space-x-4 mt-4 text-sm text-purple-200/60">
                        <span>Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
                        <span>Impact: {(insight.impact_score * 100).toFixed(0)}%</span>
                        {insight.related_symbols.length > 0 && (
                          <span>Symbols: {insight.related_symbols.join(', ')}</span>
                        )}
                      </div>
                    </div>
                    {!insight.was_implemented && (
                      <button
                        onClick={() => markInsightImplemented(insight.id)}
                        className="ml-4 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-all"
                      >
                        Mark Implemented
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Cycles Tab */}
      {activeTab === 'cycles' && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white">🔄 Feedback Cycle History</h2>
          
          {cycles.length === 0 ? (
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-12 text-center border border-white/10">
              <div className="text-4xl mb-4">🔄</div>
              <p className="text-purple-200/60">No feedback cycles recorded yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {cycles.map((cycle) => (
                <div key={cycle.id} className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-4">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        cycle.cycle_type === 'weekly' 
                          ? 'bg-purple-500/20 text-purple-400' 
                          : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {cycle.cycle_type === 'weekly' ? '🔄' : '📅'}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white capitalize">{cycle.cycle_type} Cycle</h3>
                        <p className="text-sm text-purple-200/60">
                          {new Date(cycle.started_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                      cycle.status === 'completed' 
                        ? 'bg-green-500/20 text-green-400' 
                        : cycle.status === 'failed'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {cycle.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-white/10">
                    <div>
                      <p className="text-sm text-purple-200/60">Signals</p>
                      <p className="text-lg font-semibold text-white">
                        {cycle.signals_correct}/{cycle.signals_evaluated}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-purple-200/60">Win Rate</p>
                      <p className={`text-lg font-semibold ${
                        cycle.win_rate >= 55 ? 'text-green-400' : cycle.win_rate < 45 ? 'text-red-400' : 'text-white'
                      }`}>
                        {cycle.win_rate.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-purple-200/60">Insights</p>
                      <p className="text-lg font-semibold text-white">{cycle.insights_generated}</p>
                    </div>
                    <div>
                      <p className="text-sm text-purple-200/60">Duration</p>
                      <p className="text-lg font-semibold text-white">
                        {cycle.completed_at 
                          ? `${Math.round((new Date(cycle.completed_at).getTime() - new Date(cycle.started_at).getTime()) / 60000)}m`
                          : 'Running...'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Analysis Tab */}
      {activeTab === 'analysis' && (
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-12 text-center border border-white/10">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-purple-200/60">Performance analysis coming soon</p>
        </div>
      )}
    </div>
  );
};

export default LearningInsights;

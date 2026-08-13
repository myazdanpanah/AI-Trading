import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface FeedbackCycle {
  id: string;
  cycle_type: string;
  status: string;
  signals_evaluated: number;
  signals_correct: number;
  insights_generated: number;
  weights_adjusted: boolean;
  summary: string;
  recommendations: string[];
  created_at: string;
}

interface LoopStatus {
  lastRun: FeedbackCycle | null;
  nextRunIn: string;
  isRunning: boolean;
  totalCycles: number;
  recentInsights: string[];
}

export const FeedbackLoopStatus: React.FC = () => {
  const { language } = useLanguage();
  const [status, setStatus] = useState<LoopStatus>({
    lastRun: null,
    nextRunIn: '--:--:--',
    isRunning: false,
    totalCycles: 0,
    recentInsights: [],
  });
  const [countdown, setCountdown] = useState(21600); // 6 hours in seconds

  const loadStatus = useCallback(async () => {
    try {
      const resp = await apiFetch('/feedback/cycles/?limit=5&cycle_type=6hour_btc');
      if (resp.ok) {
        const data = await resp.json();
        const cycles = data.results || data || [];
        const lastCycle = cycles[0] || null;

        // Calculate time since last run
        if (lastCycle) {
          const lastRun = new Date(lastCycle.created_at);
          const now = new Date();
          const diffMs = now.getTime() - lastRun.getTime();
          const diffSec = Math.floor(diffMs / 1000);
          const remaining = Math.max(0, 21600 - diffSec); // 6 hours - elapsed

          setCountdown(remaining);

          // Extract insights from summary
          const insights = (lastCycle.summary || '').split('\n').filter((s: string) => s.trim());

          setStatus({
            lastRun: lastCycle,
            nextRunIn: formatCountdown(remaining),
            isRunning: false,
            totalCycles: cycles.length,
            recentInsights: insights.slice(0, 5),
          });
        } else {
          setStatus(prev => ({ ...prev, totalCycles: cycles.length }));
        }
      }
    } catch (e) {
      console.error('Failed to load feedback status:', e);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadStatus]);

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        const next = Math.max(0, prev - 1);
        setStatus(s => ({ ...s, nextRunIn: formatCountdown(next) }));
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMin / 60);

    if (diffHr > 0) return `${diffHr}h ${diffMin % 60}m ago`;
    return `${diffMin}m ago`;
  };

  const runNow = async () => {
    setStatus(s => ({ ...s, isRunning: true }));
    try {
      const resp = await apiFetch('/feedback/cycles/run_cycle/', {
        method: 'POST',
        body: JSON.stringify({ cycle_type: '6hour_btc' }),
      });
      if (resp.ok) {
        setCountdown(21600); // Reset countdown
        setTimeout(loadStatus, 2000); // Reload after 2s
      }
    } catch (e) {
      console.error('Failed to run cycle:', e);
    } finally {
      setStatus(s => ({ ...s, isRunning: false }));
    }
  };

  const lastCycle = status.lastRun;
  const progressPercent = ((21600 - countdown) / 21600) * 100;

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">
          🔄 {language === 'fa' ? 'حلقه بازخورد ۶ ساعته BTC' : '6-Hour BTC Feedback Loop'}
        </h3>
        <button
          onClick={runNow}
          disabled={status.isRunning}
          className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:opacity-50"
        >
          {status.isRunning ? '⏳ Running...' : '▶️ Run Now'}
        </button>
      </div>

      {/* Timer */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400">
            {language === 'fa' ? 'اجرای بعدی' : 'Next Run'}
          </span>
          <span className="text-lg font-mono font-bold text-blue-400">
            {status.nextRunIn}
          </span>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-1000"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">0h</span>
          <span className="text-xs text-gray-500">6h</span>
        </div>
      </div>

      {/* Last Run Info */}
      {lastCycle ? (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center p-2 bg-gray-800 rounded">
              <div className="text-lg font-bold text-green-400">
                {lastCycle.signals_evaluated}
              </div>
              <div className="text-xs text-gray-400">
                {language === 'fa' ? 'سیگنال' : 'Signals'}
              </div>
            </div>
            <div className="text-center p-2 bg-gray-800 rounded">
              <div className="text-lg font-bold text-blue-400">
                {lastCycle.insights_generated}
              </div>
              <div className="text-xs text-gray-400">
                {language === 'fa' ? 'بینش' : 'Insights'}
              </div>
            </div>
            <div className="text-center p-2 bg-gray-800 rounded">
              <div className={`text-lg font-bold ${lastCycle.weights_adjusted ? 'text-yellow-400' : 'text-gray-500'}`}>
                {lastCycle.weights_adjusted ? '✅' : '—'}
              </div>
              <div className="text-xs text-gray-400">
                {language === 'fa' ? 'وزن‌ها' : 'Weights'}
              </div>
            </div>
          </div>

          {/* Win Rate */}
          {lastCycle.signals_evaluated > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-16">
                {language === 'fa' ? 'نرخ برد:' : 'Win Rate:'}
              </span>
              <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full"
                  style={{ width: `${(lastCycle.signals_correct / lastCycle.signals_evaluated) * 100}%` }}
                />
              </div>
              <span className="text-xs text-white w-12 text-right">
                {((lastCycle.signals_correct / lastCycle.signals_evaluated) * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Last Run Time */}
          <div className="text-xs text-gray-500">
            {language === 'fa' ? 'آخرین اجرا:' : 'Last run:'} {formatTimeAgo(lastCycle.created_at)}
          </div>

          {/* Recent Insights */}
          {status.recentInsights.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-gray-400 mb-2">
                {language === 'fa' ? 'بینش‌های اخیر:' : 'Recent Insights:'}
              </div>
              <div className="space-y-1">
                {status.recentInsights.map((insight, i) => (
                  <div key={i} className="text-xs text-gray-300 bg-gray-800/50 rounded p-1.5">
                    💡 {insight}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {lastCycle.recommendations && lastCycle.recommendations.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-gray-400 mb-2">
                {language === 'fa' ? 'توصیه‌ها:' : 'Recommendations:'}
              </div>
              {lastCycle.recommendations.map((rec: any, i) => {
                // Handle both string and object formats
                const isObject = typeof rec === 'object' && rec !== null;
                const title = isObject ? (rec.title || rec.message || '') : String(rec);
                const description = isObject ? rec.description : '';
                const action = isObject ? rec.action : '';
                const priority = isObject ? rec.priority : '';
                return (
                  <div key={i} className="text-xs bg-yellow-900/20 rounded p-1.5 mb-1">
                    <div className="flex items-start gap-1">
                      <span className={priority === 'high' ? 'text-red-400' : 'text-yellow-300'}>
                        {priority === 'high' ? '🔴' : '⚠️'}
                      </span>
                      <div>
                        <div className="text-yellow-300 font-medium">{title}</div>
                        {description && <div className="text-gray-400 mt-0.5">{description}</div>}
                        {action && <div className="text-blue-400 mt-0.5">→ {action}</div>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4 text-gray-500 text-sm">
          {language === 'fa'
            ? 'هنوز چرخه‌ای اجرا نشده. روی "Run Now" کلیک کنید.'
            : 'No cycles run yet. Click "Run Now" to start.'}
        </div>
      )}

      {/* Total Cycles */}
      <div className="mt-3 pt-3 border-t border-gray-700 flex justify-between text-xs text-gray-500">
        <span>{language === 'fa' ? 'کل چرخه‌ها:' : 'Total cycles:'} {status.totalCycles}</span>
        <span>{language === 'fa' ? 'هر ۶ ساعت' : 'Every 6 hours'}</span>
      </div>
    </div>
  );
};

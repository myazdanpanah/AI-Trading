import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface WeightChange {
  factor_name: string;
  old_weight: number;
  new_weight: number;
  change: number;
  win_rate: number;
  signals_evaluated: number;
  reason: string;
  adjustment_type: string;
  created_at: string;
}

const FACTOR_COLORS: Record<string, string> = {
  technical: '#3B82F6',  // blue
  sentiment: '#8B5CF6',  // purple
  news: '#10B981',       // green
  ai: '#F59E0B',         // amber
  macro: '#EF4444',      // red
};

const FACTOR_LABELS: Record<string, Record<string, string>> = {
  en: { technical: 'Technical', sentiment: 'Sentiment', news: 'News', ai: 'AI/LLM', macro: 'Macro' },
  fa: { technical: 'تکنیکال', sentiment: 'احساسات', news: 'اخبار', ai: 'هوش مصنوعی', macro: 'کلان' },
};

export const WeightHistoryChart: React.FC = () => {
  const { language } = useLanguage();
  const [history, setHistory] = useState<WeightChange[]>([]);
  const [currentWeights, setCurrentWeights] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load current weights
      const weightsResp = await apiFetch('/signals/weights/');
      if (weightsResp.ok) {
        const weightsData = await weightsResp.json();
        const weights: Record<string, number> = {};
        const items = weightsData.results || weightsData || [];
        for (const w of items) {
          weights[w.name] = parseFloat(w.weight);
        }
        setCurrentWeights(weights);
      }

      // Load weight history
      const historyResp = await apiFetch('/signals/weight-history/');
      if (historyResp.ok) {
        const historyData = await historyResp.json();
        setHistory(historyData.results || historyData || []);
      }
    } catch (e) {
      console.error('Failed to load weight data:', e);
    } finally {
      setLoading(false);
    }
  };

  const labels = FACTOR_LABELS[language] || FACTOR_LABELS.en;

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-gray-400 text-center py-8">Loading weight history...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">
          🧠 {language === 'fa' ? 'تاریخچه وزن‌های AI' : 'AI Weight History'}
        </h3>
        <button onClick={loadData} className="text-sm text-blue-400 hover:text-blue-300">
          🔄 {language === 'fa' ? 'بروزرسانی' : 'Refresh'}
        </button>
      </div>

      {/* Current Weights Display */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-300 mb-3">
          {language === 'fa' ? 'وزن‌های فعلی' : 'Current Weights'}
        </h4>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(currentWeights).map(([factor, weight]) => (
            <div key={factor} className="text-center">
              <div className="relative h-32 bg-gray-700 rounded-lg overflow-hidden">
                <div
                  className="absolute bottom-0 left-0 right-0 transition-all duration-500 rounded-lg"
                  style={{
                    height: `${weight * 100 * 4}%`,
                    backgroundColor: FACTOR_COLORS[factor] || '#6B7280',
                    maxHeight: '100%',
                  }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">{(weight * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-400">{labels[factor] || factor}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Weight History Timeline */}
      {history.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-3">
            {language === 'fa' ? 'تغییرات اخیر' : 'Recent Changes'}
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {history.slice(0, 20).map((item, idx) => {
              const change = item.new_weight - item.old_weight;
              const isIncrease = change > 0;
              return (
                <div key={idx} className="flex items-center gap-3 text-sm p-2 bg-gray-700/50 rounded-lg">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: FACTOR_COLORS[item.factor_name] || '#6B7280' }}
                  />
                  <span className="text-white font-medium w-20">{labels[item.factor_name] || item.factor_name}</span>
                  <span className="text-gray-400">
                    {(item.old_weight * 100).toFixed(1)}%
                  </span>
                  <span className={isIncrease ? 'text-green-400' : 'text-red-400'}>
                    {isIncrease ? '→' : '→'}
                  </span>
                  <span className="text-white font-medium">
                    {(item.new_weight * 100).toFixed(1)}%
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded ${isIncrease ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                    {isIncrease ? '+' : ''}{(change * 100).toFixed(2)}%
                  </span>
                  <span className="text-gray-500 text-xs ml-auto">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {history.length === 0 && (
        <div className="text-center text-gray-500 py-4 text-sm">
          {language === 'fa'
            ? 'هنوز تغییر وزنی ثبت نشده. وزن‌ها با اجرای Celery و تولید سیگنال‌ها تغییر می‌کنند.'
            : 'No weight changes yet. Weights will adjust as signals are generated and evaluated by Celery.'}
        </div>
      )}
    </div>
  );
};

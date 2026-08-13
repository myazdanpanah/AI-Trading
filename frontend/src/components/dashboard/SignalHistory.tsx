import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface Signal {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  composite_score: number;
  technical_score: number;
  sentiment_score: number;
  news_score: number;
  ai_score: number;
  macro_score: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number[];
  timeframe: string;
  risk_score: number;
  is_active: boolean;
  created_at: string;
  expires_at?: string;
}

interface SignalMemory {
  id: string;
  signal: string;
  signal_direction: string;
  entry_price: number;
  exit_price: number;
  actual_return_percent: number;
  was_correct: boolean;
  holding_period_hours: number;
  evaluated_at: string;
}

const safe = {
  num: (v: any, d = 0): number => {
    if (v === null || v === undefined || v === '') return d;
    const n = typeof v === 'string' ? parseFloat(v) : v;
    return isNaN(n) ? d : n;
  },
};

export const SignalHistory: React.FC = () => {
  const { language } = useLanguage();
  const [signals, setSignals] = useState<Signal[]>([]);
  const [evaluations, setEvaluations] = useState<SignalMemory[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'evaluated'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'confidence' | 'return'>('date');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const sigResp = await apiFetch('/signals/signals/?ordering=-created_at&limit=50');
      if (sigResp.ok) {
        const data = await sigResp.json();
        setSignals(data.results || data || []);
      }

      const evalResp = await apiFetch('/signals/signals/evaluated/?limit=50');
      if (evalResp.ok) {
        const data = await evalResp.json();
        setEvaluations(data.results || data || []);
      }
    } catch (e) {
      console.error('Failed to load signal history:', e);
    } finally {
      setLoading(false);
    }
  };

  const getDirectionColor = (dir: string) => {
    switch (dir?.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return 'text-green-400 bg-green-900/30';
      case 'sell':
      case 'strong_sell':
        return 'text-red-400 bg-red-900/30';
      default:
        return 'text-yellow-400 bg-yellow-900/30';
    }
  };

  const getDirectionLabel = (dir: string) => {
    const labels: Record<string, Record<string, string>> = {
      en: { buy: 'BUY', strong_buy: 'STRONG BUY', sell: 'SELL', strong_sell: 'STRONG SELL', hold: 'HOLD' },
      fa: { buy: 'خرید', strong_buy: 'خرید قوی', sell: 'فروش', strong_sell: 'فروش قوی', hold: 'نگهداری' },
    };
    return (labels[language] || labels.en)[dir] || dir?.toUpperCase();
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-gray-400 text-center py-8">Loading signal history...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">
          📊 {language === 'fa' ? 'تاریخچه سیگنال‌ها' : 'Signal History'}
        </h3>
        <div className="flex gap-2">
          {(['all', 'active', 'evaluated'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-sm ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
            >
              {f === 'all' ? (language === 'fa' ? 'همه' : 'All') : f === 'active' ? (language === 'fa' ? 'فعال' : 'Active') : (language === 'fa' ? 'ارزیابی شده' : 'Evaluated')}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="bg-gray-700/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-white">{signals.length}</div>
          <div className="text-xs text-gray-400">{language === 'fa' ? 'کل سیگنال‌ها' : 'Total Signals'}</div>
        </div>
        <div className="bg-green-900/30 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{signals.filter(s => s.direction?.includes('buy')).length}</div>
          <div className="text-xs text-gray-400">{language === 'fa' ? 'سیگنال خرید' : 'Buy Signals'}</div>
        </div>
        <div className="bg-red-900/30 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-red-400">{signals.filter(s => s.direction?.includes('sell')).length}</div>
          <div className="text-xs text-gray-400">{language === 'fa' ? 'سیگنال فروش' : 'Sell Signals'}</div>
        </div>
        <div className="bg-blue-900/30 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{evaluations.length}</div>
          <div className="text-xs text-gray-400">{language === 'fa' ? 'ارزیابی شده' : 'Evaluated'}</div>
        </div>
      </div>

      {/* Signals Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="text-left py-2 px-3">{language === 'fa' ? 'تاریخ' : 'Date'}</th>
              <th className="text-left py-2 px-3">{language === 'fa' ? 'نماد' : 'Symbol'}</th>
              <th className="text-left py-2 px-3">{language === 'fa' ? 'جهت' : 'Direction'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'اعتماد' : 'Confidence'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'ترکیبی' : 'Composite'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'تکنیکال' : 'Technical'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'اخبار' : 'News'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'AI' : 'AI'}</th>
              <th className="text-right py-2 px-3">{language === 'fa' ? 'قیمت ورود' : 'Entry'}</th>
              <th className="text-center py-2 px-3">{language === 'fa' ? 'وضعیت' : 'Status'}</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((signal) => (
              <tr key={signal.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                <td className="py-2 px-3 text-gray-300">
                  {new Date(signal.created_at).toLocaleDateString()}
                </td>
                <td className="py-2 px-3 text-white font-medium">{signal.symbol}</td>
                <td className="py-2 px-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${getDirectionColor(signal.direction)}`}>
                    {getDirectionLabel(signal.direction)}
                  </span>
                </td>
                <td className="py-2 px-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-1.5 bg-gray-600 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${safe.num(signal.confidence)}%`,
                          backgroundColor: safe.num(signal.confidence) > 70 ? '#10B981' : safe.num(signal.confidence) > 50 ? '#F59E0B' : '#EF4444',
                        }}
                      />
                    </div>
                    <span className="text-white w-10 text-right">{safe.num(signal.confidence).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-2 px-3 text-right text-white">{safe.num(signal.composite_score).toFixed(1)}</td>
                <td className="py-2 px-3 text-right text-gray-300">{safe.num(signal.technical_score).toFixed(1)}</td>
                <td className="py-2 px-3 text-right text-gray-300">{safe.num(signal.news_score).toFixed(1)}</td>
                <td className="py-2 px-3 text-right text-gray-300">{safe.num(signal.ai_score).toFixed(1)}</td>
                <td className="py-2 px-3 text-right text-gray-300">${safe.num(signal.entry_price).toLocaleString()}</td>
                <td className="py-2 px-3 text-center">
                  {signal.is_active ? (
                    <span className="text-green-400 text-xs">● {language === 'fa' ? 'فعال' : 'Active'}</span>
                  ) : (
                    <span className="text-gray-500 text-xs">○ {language === 'fa' ? 'منقضی' : 'Expired'}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Evaluated Signals (Outcomes) */}
      {evaluations.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">
            {language === 'fa' ? 'نتایج ارزیابی' : 'Evaluation Results'}
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {evaluations.map((ev) => (
              <div key={ev.id} className="flex items-center gap-3 text-sm p-2 bg-gray-700/50 rounded-lg">
                <span className={`w-2 h-2 rounded-full ${ev.was_correct ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-white font-medium">{ev.signal_direction?.toUpperCase()}</span>
                <span className="text-gray-400">
                  ${safe.num(ev.entry_price).toLocaleString()} → ${safe.num(ev.exit_price).toLocaleString()}
                </span>
                <span className={ev.actual_return_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {ev.actual_return_percent >= 0 ? '+' : ''}{safe.num(ev.actual_return_percent).toFixed(2)}%
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${ev.was_correct ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                  {ev.was_correct ? (language === 'fa' ? 'برد' : 'WIN') : (language === 'fa' ? 'باخت' : 'LOSS')}
                </span>
                <span className="text-gray-500 text-xs ml-auto">
                  {ev.holding_period_hours}h
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {signals.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          {language === 'fa'
            ? 'هنوز سیگنالی تولید نشده. با اجرای Celery سیگنال‌ها خودکار تولید می‌شوند.'
            : 'No signals generated yet. Celery will auto-generate signals once running.'}
        </div>
      )}
    </div>
  );
};

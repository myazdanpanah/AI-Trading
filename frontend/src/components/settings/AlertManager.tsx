import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';
import { useLanguage } from '../../contexts/LanguageContext';

interface AlertRule {
  id: string;
  symbol: string;
  alert_type: string;
  alert_type_display: string;
  threshold: number;
  is_active: boolean;
  cooldown_minutes: number;
  last_triggered: string | null;
  message_template: string;
  created_at: string;
}

interface AlertHistory {
  id: string;
  rule: string;
  rule_symbol: string;
  rule_alert_type: string;
  triggered_at: string;
  trigger_value: number;
  message: string;
  read: boolean;
}

const ALERT_TYPES = [
  { value: 'rsi_above', label: 'RSI Above', icon: '📈', color: 'text-red-400' },
  { value: 'rsi_below', label: 'RSI Below', icon: '📉', color: 'text-green-400' },
  { value: 'confidence_above', label: 'Confidence Above', icon: '🎯', color: 'text-blue-400' },
  { value: 'confidence_below', label: 'Confidence Below', icon: '🎯', color: 'text-yellow-400' },
  { value: 'composite_above', label: 'Composite Above', icon: '📊', color: 'text-green-400' },
  { value: 'composite_below', label: 'Composite Below', icon: '📊', color: 'text-red-400' },
  { value: 'technical_above', label: 'Technical Above', icon: '🔧', color: 'text-blue-400' },
  { value: 'technical_below', label: 'Technical Below', icon: '🔧', color: 'text-yellow-400' },
  { value: 'sentiment_above', label: 'Sentiment Above', icon: '💭', color: 'text-purple-400' },
  { value: 'sentiment_below', label: 'Sentiment Below', icon: '💭', color: 'text-orange-400' },
  { value: 'price_above', label: 'Price Above', icon: '💰', color: 'text-green-400' },
  { value: 'price_below', label: 'Price Below', icon: '💰', color: 'text-red-400' },
  { value: 'signal_buy', label: 'Buy Signal', icon: '🟢', color: 'text-green-400' },
  { value: 'signal_sell', label: 'Sell Signal', icon: '🔴', color: 'text-red-400' },
  { value: 'signal_strong_buy', label: 'Strong Buy', icon: '🟢', color: 'text-green-400' },
  { value: 'signal_strong_sell', label: 'Strong Sell', icon: '🔴', color: 'text-red-400' },
];

const QUICK_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];

export const AlertManager: React.FC = () => {
  const { language } = useLanguage();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [history, setHistory] = useState<AlertHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [checking, setChecking] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState<'rules' | 'history'>('rules');
  const [newRule, setNewRule] = useState({
    symbol: 'BTCUSDT',
    alert_type: 'rsi_above',
    threshold: 70,
    cooldown_minutes: 60,
    message_template: '',
  });

  const fetchRules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/signals/alerts/');
      if (res.ok) {
        const data = await res.json();
        setRules(data.results || data);
      }
    } catch (err) { /* ignore */ }
    setLoading(false);
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await apiFetch('/signals/alert-history/');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.results || data);
      }
    } catch (err) { /* ignore */ }
  }, []);

  const fetchUnread = useCallback(async () => {
    try {
      const res = await apiFetch('/signals/alert-history/unread_count/');
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.count || 0);
      }
    } catch (err) { /* ignore */ }
  }, []);

  useEffect(() => { fetchRules(); fetchHistory(); fetchUnread(); }, [fetchRules, fetchHistory, fetchUnread]);

  const addRule = async () => {
    try {
      const res = await apiFetch('/signals/alerts/', {
        method: 'POST',
        body: JSON.stringify(newRule),
      });
      if (res.ok) {
        setShowAddModal(false);
        setNewRule({ symbol: 'BTCUSDT', alert_type: 'rsi_above', threshold: 70, cooldown_minutes: 60, message_template: '' });
        fetchRules();
      }
    } catch (err) { /* ignore */ }
  };

  const deleteRule = async (id: string) => {
    try {
      await apiFetch(`/signals/alerts/${id}/`, { method: 'DELETE' });
      fetchRules();
    } catch (err) { /* ignore */ }
  };

  const toggleRule = async (rule: AlertRule) => {
    try {
      await apiFetch(`/signals/alerts/${rule.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !rule.is_active }),
      });
      fetchRules();
    } catch (err) { /* ignore */ }
  };

  const checkAlerts = async () => {
    setChecking(true);
    try {
      const res = await apiFetch('/signals/alerts/check/', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.total_triggered > 0) {
          fetchHistory();
          fetchUnread();
        }
      }
    } catch (err) { /* ignore */ }
    setChecking(false);
  };

  const markRead = async (id: string) => {
    try {
      await apiFetch(`/signals/alert-history/${id}/mark_read/`, { method: 'POST' });
      fetchUnread();
      fetchHistory();
    } catch (err) { /* ignore */ }
  };

  const markAllRead = async () => {
    try {
      await apiFetch('/signals/alert-history/mark_all_read/', { method: 'POST' });
      fetchUnread();
      fetchHistory();
    } catch (err) { /* ignore */ }
  };

  const loadDefaults = async () => {
    try {
      const res = await apiFetch('/signals/alerts/defaults/');
      if (res.ok) {
        const defaults = await res.json();
        for (const def of defaults) {
          await apiFetch('/signals/alerts/', {
            method: 'POST',
            body: JSON.stringify({ ...def, is_active: true, cooldown_minutes: 60 }),
          });
        }
        fetchRules();
      }
    } catch (err) { /* ignore */ }
  };

  const formatTime = (ts: string | null) => {
    if (!ts) return '—';
    return new Date(ts).toLocaleString('en-US', { timeZone: 'Asia/Tehran', hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            {language === 'fa' ? '🔔 هشدارها' : '🔔 Score Alerts'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {language === 'fa' ? 'هشدارها وقتی امتیازات از سطح عبور کنند' : 'Get alerts when scores cross certain levels'}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadDefaults} className="px-3 py-1.5 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 text-sm">
            {language === 'fa' ? 'پیش‌فرض' : 'Load Defaults'}
          </button>
          <button
            onClick={checkAlerts}
            disabled={checking}
            className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm disabled:opacity-50"
          >
            {checking ? '...' : '⚡ ' + (language === 'fa' ? 'بررسی' : 'Check Now')}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            + {language === 'fa' ? 'هشدار جدید' : 'Add Alert'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'rules' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          📋 {language === 'fa' ? 'قوانین' : 'Rules'} ({rules.length})
        </button>
        <button
          onClick={() => { setActiveTab('history'); markAllRead(); }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all relative ${
            activeTab === 'history' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          📜 {language === 'fa' ? 'تاریخچه' : 'History'} ({history.length})
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <>
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
            </div>
          ) : rules.length === 0 ? (
            <div className="bg-white/5 rounded-xl p-8 text-center">
              <div className="text-4xl mb-4">🔔</div>
              <p className="text-gray-400 mb-4">{language === 'fa' ? 'هشداری تنظیم نشده' : 'No alert rules configured'}</p>
              <button onClick={loadDefaults} className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                {language === 'fa' ? 'بارگذاری پیش‌فرض‌ها' : 'Load Default Alerts'}
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {rules.map(rule => {
                const alertDef = ALERT_TYPES.find(a => a.value === rule.alert_type);
                return (
                  <div
                    key={rule.id}
                    className={`bg-white/5 rounded-lg p-4 flex items-center gap-4 transition-all ${
                      rule.is_active ? 'border border-white/10' : 'border border-white/5 opacity-50'
                    }`}
                  >
                    <span className="text-2xl">{alertDef?.icon || '🔔'}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{rule.symbol.replace('USDT', '')}/USDT</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          rule.alert_type.includes('above') ? 'bg-green-500/20 text-green-400' :
                          rule.alert_type.includes('below') ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {rule.alert_type_display}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Threshold: <span className="text-white">{rule.threshold}</span> | 
                        Cooldown: {rule.cooldown_minutes}min | 
                        Last: {formatTime(rule.last_triggered)}
                      </div>
                      {rule.message_template && (
                        <div className="text-xs text-gray-500 mt-1 italic">"{rule.message_template}"</div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => toggleRule(rule)}
                        className={`w-10 h-6 rounded-full transition-all ${
                          rule.is_active ? 'bg-green-500' : 'bg-gray-600'
                        }`}
                      >
                        <div className={`w-4 h-4 rounded-full bg-white transition-all ${
                          rule.is_active ? 'translate-x-5' : 'translate-x-1'
                        }`} />
                      </button>
                      <button
                        onClick={() => deleteRule(rule.id)}
                        className="text-gray-500 hover:text-red-400 text-sm px-2"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <>
          {history.length === 0 ? (
            <div className="bg-white/5 rounded-xl p-8 text-center">
              <div className="text-4xl mb-4">📜</div>
              <p className="text-gray-400">{language === 'fa' ? 'هشداری فعال نشده' : 'No alerts triggered yet'}</p>
              <p className="text-gray-500 text-sm mt-1">{language === 'fa' ? 'هشدارها اینجا نمایش داده می‌شوند' : 'Triggered alerts will appear here'}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {history.map(h => (
                <div
                  key={h.id}
                  className={`rounded-lg p-4 flex items-center gap-4 transition-all ${
                    h.read ? 'bg-white/5 border border-white/5 opacity-60' : 'bg-white/5 border border-yellow-500/30'
                  }`}
                >
                  <span className={`text-2xl ${h.read ? 'opacity-50' : ''}`}>🔔</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">{h.rule_symbol?.replace('USDT', '')}</span>
                      <span className="text-xs text-gray-400">{h.rule_alert_type}</span>
                      {!h.read && <span className="w-2 h-2 bg-yellow-500 rounded-full" />}
                    </div>
                    <div className="text-sm text-gray-300 mt-1">{h.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Value: <span className="text-white">{h.trigger_value?.toFixed(2)}</span> | 
                      {formatTime(h.triggered_at)}
                    </div>
                  </div>
                  {!h.read && (
                    <button
                      onClick={() => markRead(h.id)}
                      className="text-gray-500 hover:text-green-400 text-xs px-2"
                    >
                      ✓ Read
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e1e2e] rounded-xl p-6 w-full max-w-md border border-white/20">
            <h3 className="text-lg font-bold text-white mb-4">
              {language === 'fa' ? 'هشدار جدید' : 'New Alert Rule'}
            </h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400">{language === 'fa' ? 'نماد' : 'Symbol'}</label>
                <select
                  value={newRule.symbol}
                  onChange={(e) => setNewRule({ ...newRule, symbol: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                >
                  {QUICK_SYMBOLS.map(s => (
                    <option key={s} value={s} className="bg-slate-800">{s.replace('USDT', '')}/USDT</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-400">{language === 'fa' ? 'نوع هشدار' : 'Alert Type'}</label>
                <select
                  value={newRule.alert_type}
                  onChange={(e) => setNewRule({ ...newRule, alert_type: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                >
                  {ALERT_TYPES.map(a => (
                    <option key={a.value} value={a.value} className="bg-slate-800">{a.icon} {a.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-400">{language === 'fa' ? 'آستانه' : 'Threshold'}: {newRule.threshold}</label>
                <input
                  type="range"
                  min="0"
                  max={newRule.alert_type.includes('price') ? '200000' : '100'}
                  value={newRule.threshold}
                  onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) })}
                  className="w-full mt-1"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0</span>
                  <span>{newRule.alert_type.includes('price') ? '$200,000' : '100'}</span>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-400">{language === 'fa' ? 'پیام سفارشی' : 'Custom Message'} ({language === 'fa' ? 'اختیاری' : 'optional'})</label>
                <input
                  type="text"
                  value={newRule.message_template}
                  onChange={(e) => setNewRule({ ...newRule, message_template: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="BTC RSI overbought - potential sell"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">{language === 'fa' ? 'فاصله هشدار (دقیقه)' : 'Cooldown (minutes)'}: {newRule.cooldown_minutes}</label>
                <input
                  type="range"
                  min="5"
                  max="360"
                  step="5"
                  value={newRule.cooldown_minutes}
                  onChange={(e) => setNewRule({ ...newRule, cooldown_minutes: parseInt(e.target.value) })}
                  className="w-full mt-1"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20"
              >
                {language === 'fa' ? 'لغو' : 'Cancel'}
              </button>
              <button
                onClick={addRule}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                {language === 'fa' ? 'افزودن' : 'Add Alert'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertManager;

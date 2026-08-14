import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

// ── Safe helpers ──────────────────────────────────────────────────────

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
    if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (Math.abs(n) >= 1) return n.toFixed(2);
    return n.toFixed(6);
  },
  pct: (v: any): string => safe.num(v).toFixed(2) + '%',
  date: (v: any): string => {
    try {
      if (!v) return '---';
      return new Date(v).toLocaleString('en-US', { timeZone: 'Asia/Tehran' });
    } catch {
      return '---';
    }
  },
  duration: (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`;
  },
};

// ── Types ─────────────────────────────────────────────────────────────

interface PaperPosition {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  stop_loss: number | null;
  take_profit: number | null;
  notional_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  fees_paid: number;
  slippage_cost: number;
  net_pnl: number;
  signal_confidence: number;
  opened_at: string;
}

interface PaperTrade {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  fees_paid: number;
  slippage_cost: number;
  holding_period_seconds: number;
  signal_confidence: number;
  close_reason: string;
  opened_at: string;
  closed_at: string;
  was_win: boolean;
}

interface AccountData {
  initial_capital: number;
  cash_balance: number;
  equity: number;
  used_margin: number;
  open_positions_count: number;
  open_positions: PaperPosition[];
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_return_pct: number;
  total_fees_paid: number;
  total_slippage_cost: number;
  peak_equity: number;
  max_drawdown: number;
  recent_trades: PaperTrade[];
}

interface PerformanceData {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  sharpe_ratio: number;
  avg_win: number;
  avg_loss: number;
  avg_holding_period_seconds: number;
  total_pnl: number;
  total_return_pct: number;
  max_drawdown: number;
  total_fees: number;
  total_slippage: number;
  peak_equity: number;
  message?: string;
}

// ── PaperTradingPanel Component ───────────────────────────────────────

export const PaperTradingPanel: React.FC = () => {
  const { language } = useLanguage();
  const [account, setAccount] = useState<AccountData | null>(null);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showOpenForm, setShowOpenForm] = useState(false);

  // Open position form
  const [formSymbol, setFormSymbol] = useState('BTCUSDT');
  const [formSide, setFormSide] = useState('long');
  const [formPrice, setFormPrice] = useState('');
  const [formQuantity, setFormQuantity] = useState('');
  const [formStopLoss, setFormStopLoss] = useState('');
  const [formTakeProfit, setFormTakeProfit] = useState('');
  const [formConfidence, setFormConfidence] = useState('75');
  const [submitting, setSubmitting] = useState(false);

  // Close position form
  const [closePositionId, setClosePositionId] = useState<string | null>(null);
  const [closePrice, setClosePrice] = useState('');
  const [closeReason, setCloseReason] = useState('manual');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const [statusRes, perfRes] = await Promise.all([
        apiFetch('/signals/signals/paper_status/'),
        apiFetch('/signals/signals/paper_performance/'),
      ]);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setAccount(statusData);
      }

      if (perfRes.ok) {
        const perfData = await perfRes.json();
        setPerformance(perfData);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [loadData]);

  const handleOpenPosition = async () => {
    try {
      setSubmitting(true);
      setError('');

      const body: any = {
        symbol: formSymbol,
        side: formSide,
      };
      if (formPrice) body.entry_price = parseFloat(formPrice);
      if (formQuantity) body.quantity = parseFloat(formQuantity);
      if (formStopLoss) body.stop_loss = parseFloat(formStopLoss);
      if (formTakeProfit) body.take_profit = parseFloat(formTakeProfit);
      body.signal_confidence = parseInt(formConfidence) || 75;

      // If no price provided, fetch current price
      if (!formPrice) {
        try {
          const tickerRes = await apiFetch(`/market/ticker/?symbol=${formSymbol.replace('USDT', '')}`);
          if (tickerRes.ok) {
            const ticker = await tickerRes.json();
            body.entry_price = parseFloat(ticker.price || ticker.current_price || 0);
          }
        } catch {
          // Continue without price — backend will reject
        }
      }

      if (!body.entry_price) {
        setError(language === 'fa' ? 'قیمت ورود الزامی است' : 'Entry price is required');
        return;
      }

      const res = await apiFetch('/signals/signals/paper_open/', {
        method: 'POST',
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (data.success) {
        setShowOpenForm(false);
        setFormPrice('');
        setFormQuantity('');
        setFormStopLoss('');
        setFormTakeProfit('');
        await loadData();
      } else {
        setError(data.error || 'Failed to open position');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleClosePosition = async () => {
    if (!closePositionId || !closePrice) return;

    try {
      setSubmitting(true);
      const res = await apiFetch('/signals/signals/paper_close/', {
        method: 'POST',
        body: JSON.stringify({
          position_id: closePositionId,
          exit_price: parseFloat(closePrice),
          reason: closeReason,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setClosePositionId(null);
        setClosePrice('');
        await loadData();
      } else {
        setError(data.error || 'Failed to close position');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = async () => {
    if (!confirm(language === 'fa' ? 'آیا مطمئن هستید؟ تمام پوزیشن‌ها و تاریخچه پاک می‌شود.' : 'Are you sure? All positions and history will be cleared.')) return;
    try {
      await apiFetch('/signals/signals/paper_reset/', {
        method: 'POST',
        body: JSON.stringify({ initial_capital: 10000 }),
      });
      await loadData();
    } catch (e) {
      setError(String(e));
    }
  };

  // ── Color helpers ───────────────────────────────────────────────────

  const pnlColor = (v: number) => v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400';
  const pnlBg = (v: number) => v > 0 ? 'bg-green-500/10 border-green-500/20' : v < 0 ? 'bg-red-500/10 border-red-500/20' : 'bg-gray-500/10 border-gray-500/20';

  // ── Render ──────────────────────────────────────────────────────────

  if (loading && !account) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
        <p className="text-gray-400 mt-3">{language === 'fa' ? 'در حال بارگذاری...' : 'Loading paper trading...'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            📝 {language === 'fa' ? 'ترید کاغذی' : 'Paper Trading'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {language === 'fa'
              ? 'ترید شبیه‌سازی شده با همان پایپلاین واقعی'
              : 'Simulated trading with the same pipeline as live'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowOpenForm(!showOpenForm)}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium flex items-center gap-2"
          >
            + {language === 'fa' ? 'پوزیشن جدید' : 'Open Position'}
          </button>
          <button
            onClick={loadData}
            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
          >
            🔄
          </button>
          <button
            onClick={handleReset}
            className="px-3 py-2 bg-gray-700 hover:bg-red-600/50 text-gray-400 hover:text-red-400 rounded-lg text-sm"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">✕</button>
        </div>
      )}

      {/* Account Overview Cards */}
      {account && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <div className="text-xs text-gray-500">{language === 'fa' ? 'سرمایه' : 'Equity'}</div>
            <div className="text-lg font-bold text-white">${safe.price(account.equity)}</div>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <div className="text-xs text-gray-500">{language === 'fa' ? 'نقد' : 'Cash'}</div>
            <div className="text-lg font-bold text-white">${safe.price(account.cash_balance)}</div>
          </div>
          <div className={`rounded-lg border p-3 ${pnlBg(account.total_return_pct)}`}>
            <div className="text-xs text-gray-500">{language === 'fa' ? 'بازده' : 'Return'}</div>
            <div className={`text-lg font-bold ${pnlColor(account.total_return_pct)}`}>
              {account.total_return_pct >= 0 ? '+' : ''}{safe.pct(account.total_return_pct)}
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <div className="text-xs text-gray-500">{language === 'fa' ? 'پوزیشن‌ها' : 'Positions'}</div>
            <div className="text-lg font-bold text-white">{account.open_positions_count}</div>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <div className="text-xs text-gray-500">{language === 'fa' ? 'برد/باخت' : 'Win/Loss'}</div>
            <div className="text-lg font-bold">
              <span className="text-green-400">{account.winning_trades}</span>
              <span className="text-gray-500"> / </span>
              <span className="text-red-400">{account.losing_trades}</span>
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <div className="text-xs text-gray-500">{language === 'fa' ? 'حد ضرر ماکس' : 'Max Drawdown'}</div>
            <div className="text-lg font-bold text-red-400">-{safe.pct(account.max_drawdown)}</div>
          </div>
        </div>
      )}

      {/* Open Position Form */}
      {showOpenForm && (
        <div className="bg-gray-800 rounded-lg border border-green-700/50 p-4">
          <h3 className="text-sm font-semibold text-white mb-3">
            + {language === 'fa' ? 'باز کردن پوزیشن جدید' : 'Open New Position'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'نماد' : 'Symbol'}</label>
              <select
                value={formSymbol}
                onChange={(e) => setFormSymbol(e.target.value)}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              >
                {['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'سمت' : 'Side'}</label>
              <select
                value={formSide}
                onChange={(e) => setFormSide(e.target.value)}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              >
                <option value="long">{language === 'fa' ? 'LONG (خرید)' : 'LONG (Buy)'}</option>
                <option value="short">{language === 'fa' ? 'SHORT (فروش)' : 'SHORT (Sell)'}</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'قیمت ورود' : 'Entry Price'}</label>
              <input
                type="number"
                value={formPrice}
                onChange={(e) => setFormPrice(e.target.value)}
                placeholder={language === 'fa' ? 'خودکار از بازار' : 'Auto from market'}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'مقدار' : 'Quantity'}</label>
              <input
                type="number"
                value={formQuantity}
                onChange={(e) => setFormQuantity(e.target.value)}
                placeholder={language === 'fa' ? 'خودکار بر اساس ریسک' : 'Auto from risk'}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'حد ضرر' : 'Stop Loss'}</label>
              <input
                type="number"
                value={formStopLoss}
                onChange={(e) => setFormStopLoss(e.target.value)}
                placeholder="Optional"
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'حد سود' : 'Take Profit'}</label>
              <input
                type="number"
                value={formTakeProfit}
                onChange={(e) => setFormTakeProfit(e.target.value)}
                placeholder="Optional"
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">{language === 'fa' ? 'اطمینان سیگنال' : 'Signal Confidence'}</label>
              <input
                type="number"
                value={formConfidence}
                onChange={(e) => setFormConfidence(e.target.value)}
                min="0"
                max="100"
                className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600 mt-1"
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleOpenPosition}
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium disabled:opacity-50"
              >
                {submitting ? '...' : language === 'fa' ? 'باز کردن' : 'Open'}
              </button>
              <button
                onClick={() => setShowOpenForm(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Open Positions */}
      {account && account.open_positions.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            📊 {language === 'fa' ? 'پوزیشن‌های باز' : 'Open Positions'} ({account.open_positions.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-700">
                  <th className="text-left py-2">{language === 'fa' ? 'نماد' : 'Symbol'}</th>
                  <th className="text-left py-2">{language === 'fa' ? 'سمت' : 'Side'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'مقدار' : 'Qty'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'ورود' : 'Entry'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'فعلی' : 'Current'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'PnL' : 'PnL'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'PnL %' : 'PnL %'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'SL' : 'SL'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'TP' : 'TP'}</th>
                  <th className="text-center py-2">{language === 'fa' ? 'عملیات' : 'Action'}</th>
                </tr>
              </thead>
              <tbody>
                {account.open_positions.map((pos) => (
                  <tr key={pos.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-2 font-mono text-white">{pos.symbol}</td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        pos.side === 'long'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {pos.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-300 font-mono">{pos.quantity.toFixed(6)}</td>
                    <td className="py-2 text-right text-gray-300 font-mono">${safe.price(pos.entry_price)}</td>
                    <td className="py-2 text-right text-white font-mono">${safe.price(pos.current_price)}</td>
                    <td className={`py-2 text-right font-mono font-bold ${pnlColor(pos.unrealized_pnl)}`}>
                      {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toFixed(2)}
                    </td>
                    <td className={`py-2 text-right font-mono ${pnlColor(pos.unrealized_pnl_pct)}`}>
                      {pos.unrealized_pnl_pct >= 0 ? '+' : ''}{pos.unrealized_pnl_pct.toFixed(2)}%
                    </td>
                    <td className="py-2 text-right text-red-400/70 font-mono text-xs">
                      {pos.stop_loss ? `$${safe.price(pos.stop_loss)}` : '---'}
                    </td>
                    <td className="py-2 text-right text-green-400/70 font-mono text-xs">
                      {pos.take_profit ? `$${safe.price(pos.take_profit)}` : '---'}
                    </td>
                    <td className="py-2 text-center">
                      {closePositionId === pos.id ? (
                        <div className="flex items-center gap-1">
                          <input
                            type="number"
                            value={closePrice}
                            onChange={(e) => setClosePrice(e.target.value)}
                            placeholder="Price"
                            className="w-20 bg-gray-700 text-white px-2 py-1 rounded text-xs border border-gray-600"
                          />
                          <select
                            value={closeReason}
                            onChange={(e) => setCloseReason(e.target.value)}
                            className="bg-gray-700 text-white px-1 py-1 rounded text-xs border border-gray-600"
                          >
                            <option value="manual">Manual</option>
                            <option value="stop_loss">SL</option>
                            <option value="take_profit">TP</option>
                          </select>
                          <button
                            onClick={handleClosePosition}
                            disabled={submitting || !closePrice}
                            className="px-2 py-1 bg-red-600 text-white rounded text-xs disabled:opacity-50"
                          >
                            ✓
                          </button>
                          <button
                            onClick={() => { setClosePositionId(null); setClosePrice(''); }}
                            className="px-2 py-1 bg-gray-700 text-white rounded text-xs"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setClosePositionId(pos.id);
                            setClosePrice(String(pos.current_price));
                          }}
                          className="px-3 py-1 bg-red-600/20 text-red-400 border border-red-600/30 rounded text-xs hover:bg-red-600/30"
                        >
                          {language === 'fa' ? 'بستن' : 'Close'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty positions */}
      {account && account.open_positions.length === 0 && !showOpenForm && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
          <div className="text-4xl mb-3">📭</div>
          <p className="text-gray-400">
            {language === 'fa' ? 'پوزیشن بازی وجود ندارد' : 'No open positions'}
          </p>
          <button
            onClick={() => setShowOpenForm(true)}
            className="mt-3 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm"
          >
            + {language === 'fa' ? 'اولین پوزیشن را باز کنید' : 'Open Your First Position'}
          </button>
        </div>
      )}

      {/* Performance Metrics */}
      {performance && performance.total_trades > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            📈 {language === 'fa' ? 'عملکرد' : 'Performance Metrics'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">{language === 'fa' ? 'نرخ برد' : 'Win Rate'}</div>
              <div className="text-sm font-bold text-white">{safe.pct(performance.win_rate)}</div>
            </div>
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">{language === 'fa' ? 'فاکتور سود' : 'Profit Factor'}</div>
              <div className={`text-sm font-bold ${performance.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'}`}>
                {performance.profit_factor === Infinity ? '∞' : performance.profit_factor.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">{language === 'fa' ? 'انتظار' : 'Expectancy'}</div>
              <div className={`text-sm font-bold ${pnlColor(performance.expectancy)}`}>
                ${performance.expectancy.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">Sharpe</div>
              <div className="text-sm font-bold text-white">{performance.sharpe_ratio.toFixed(2)}</div>
            </div>
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">{language === 'fa' ? 'میانگین برد' : 'Avg Win'}</div>
              <div className="text-sm font-bold text-green-400">${performance.avg_win.toFixed(2)}</div>
            </div>
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-[10px] text-gray-500">{language === 'fa' ? 'میانگین باخت' : 'Avg Loss'}</div>
              <div className="text-sm font-bold text-red-400">${performance.avg_loss.toFixed(2)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Trade History */}
      {account && account.recent_trades && account.recent_trades.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            📜 {language === 'fa' ? 'تاریخچه تریدها' : 'Trade History'} ({account.total_trades} total)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-700">
                  <th className="text-left py-2">{language === 'fa' ? 'نماد' : 'Symbol'}</th>
                  <th className="text-left py-2">{language === 'fa' ? 'سمت' : 'Side'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'ورود' : 'Entry'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'خروج' : 'Exit'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'PnL' : 'PnL'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'PnL %' : 'PnL %'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'مدت' : 'Duration'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'دلیل' : 'Reason'}</th>
                  <th className="text-right py-2">{language === 'fa' ? 'تاریخ' : 'Date'}</th>
                </tr>
              </thead>
              <tbody>
                {[...account.recent_trades].reverse().map((trade) => (
                  <tr key={trade.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-2 font-mono text-white">{trade.symbol}</td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        trade.side === 'long'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-300 font-mono">${safe.price(trade.entry_price)}</td>
                    <td className="py-2 text-right text-gray-300 font-mono">${safe.price(trade.exit_price)}</td>
                    <td className={`py-2 text-right font-mono font-bold ${pnlColor(trade.pnl)}`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                    </td>
                    <td className={`py-2 text-right font-mono ${pnlColor(trade.pnl_pct)}`}>
                      {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                    </td>
                    <td className="py-2 text-right text-gray-400 text-xs">
                      {safe.duration(trade.holding_period_seconds)}
                    </td>
                    <td className="py-2 text-right">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        trade.close_reason === 'stop_loss' ? 'bg-red-500/20 text-red-400' :
                        trade.close_reason === 'take_profit' ? 'bg-green-500/20 text-green-400' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {trade.close_reason}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-500 text-xs">{safe.date(trade.closed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No trades yet */}
      {account && account.total_trades === 0 && account.open_positions.length === 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
          <div className="text-5xl mb-4">📝</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {language === 'fa' ? 'شروع ترید کاغذی' : 'Start Paper Trading'}
          </h3>
          <p className="text-gray-400 text-sm mb-4 max-w-md mx-auto">
            {language === 'fa'
              ? 'پوزیشن‌های شبیه‌سازی شده باز کنید تا استراتژی خود را بدون ریسک واقعی تست کنید.'
              : 'Open simulated positions to test your strategy without real risk.'}
          </p>
          <button
            onClick={() => setShowOpenForm(true)}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
          >
            + {language === 'fa' ? 'باز کردن اولین پوزیشن' : 'Open First Position'}
          </button>
        </div>
      )}
    </div>
  );
};

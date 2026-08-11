import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface BacktestResult {
  equity: { date: string; value: number }[];
  metrics: {
    totalReturn: number;
    winRate: number;
    profitFactor: number;
    maxDrawdown: number;
    sharpeRatio: number;
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    avgWin: number;
    avgLoss: number;
  };
  trades: {
    id: string;
    entryDate: string;
    exitDate: string;
    side: 'long' | 'short';
    entryPrice: number;
    exitPrice: number;
    pnl: number;
    pnlPercent: number;
  }[];
}

const STRATEGIES = [
  { id: 'sma_cross', label: 'SMA Crossover', description: 'Buy when fast SMA crosses above slow SMA' },
  { id: 'rsi_reversal', label: 'RSI Reversal', description: 'Buy on RSI oversold, sell on overbought' },
  { id: 'bollinger', label: 'Bollinger Bounce', description: 'Buy at lower band, sell at upper band' },
  { id: 'macd', label: 'MACD Crossover', description: 'Buy on MACD signal crossover' },
];

export const Backtester: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState('sma_cross');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  
  const generateBacktestResult = (): BacktestResult => {
    const equity = [];
    let value = initialCapital;
    const trades = [];
    
    // Generate equity curve
    for (let i = 0; i < 365; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const dailyReturn = (Math.random() - 0.45) * 0.03;
      value *= (1 + dailyReturn);
      equity.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: Math.round(value),
      });
    }
    
    // Generate trades
    for (let i = 0; i < 50; i++) {
      const entryDate = new Date(startDate);
      entryDate.setDate(entryDate.getDate() + Math.floor(Math.random() * 300));
      const holdDays = Math.floor(Math.random() * 10) + 1;
      const exitDate = new Date(entryDate);
      exitDate.setDate(exitDate.getDate() + holdDays);
      
      const entryPrice = 60000 + Math.random() * 10000;
      const pnlPercent = (Math.random() - 0.4) * 10;
      const exitPrice = entryPrice * (1 + pnlPercent / 100);
      
      trades.push({
        id: (i + 1).toString(),
        entryDate: entryDate.toLocaleDateString(),
        exitDate: exitDate.toLocaleDateString(),
        side: Math.random() > 0.5 ? 'long' : 'short',
        entryPrice: Math.round(entryPrice),
        exitPrice: Math.round(exitPrice),
        pnl: Math.round((exitPrice - entryPrice) * (Math.random() * 0.1 + 0.01)),
        pnlPercent: Math.round(pnlPercent * 100) / 100,
      });
    }
    
    const winningTrades = trades.filter(t => t.pnl > 0).length;
    
    return {
      equity,
      metrics: {
        totalReturn: ((value - initialCapital) / initialCapital * 100),
        winRate: (winningTrades / trades.length * 100),
        profitFactor: 1.5 + Math.random() * 0.5,
        maxDrawdown: -(5 + Math.random() * 10),
        sharpeRatio: 1 + Math.random() * 0.8,
        totalTrades: trades.length,
        winningTrades,
        losingTrades: trades.length - winningTrades,
        avgWin: 3 + Math.random() * 3,
        avgLoss: -(2 + Math.random() * 2),
      },
      trades: trades.sort((a, b) => new Date(a.entryDate).getTime() - new Date(b.entryDate).getTime()),
    };
  };
  
  const runBacktest = async () => {
    setRunning(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setResult(generateBacktestResult());
    setRunning(false);
  };

  return (
    <div className="bg-[#131722] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-3">
        <h2 className="text-white font-semibold">Strategy Backtester</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Configuration */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Strategy</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full bg-[#1e1e2e] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              {STRATEGIES.map(s => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Initial Capital ($)</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full bg-[#1e1e2e] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-[#1e1e2e] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-[#1e1e2e] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
        
        <button
          onClick={runBacktest}
          disabled={running}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-semibold rounded transition-colors"
        >
          {running ? 'Running Backtest...' : 'Run Backtest'}
        </button>
        
        {/* Results */}
        {result && (
          <div className="space-y-4">
            {/* Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              {[
                { label: 'Total Return', value: `${result.metrics.totalReturn.toFixed(2)}%`, color: result.metrics.totalReturn >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]' },
                { label: 'Win Rate', value: `${result.metrics.winRate.toFixed(1)}%`, color: 'text-white' },
                { label: 'Profit Factor', value: result.metrics.profitFactor.toFixed(2), color: 'text-white' },
                { label: 'Max Drawdown', value: `${result.metrics.maxDrawdown.toFixed(2)}%`, color: 'text-[#ef5350]' },
                { label: 'Sharpe Ratio', value: result.metrics.sharpeRatio.toFixed(2), color: 'text-white' },
              ].map((m, i) => (
                <div key={i} className="bg-[#1e1e2e] rounded p-3">
                  <div className="text-xs text-gray-400">{m.label}</div>
                  <div className={`text-lg font-mono font-semibold ${m.color}`}>{m.value}</div>
                </div>
              ))}
            </div>
            
            {/* Equity curve */}
            <div className="bg-[#1e1e2e] rounded p-4">
              <h3 className="text-sm text-gray-400 mb-3">Equity Curve</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={result.equity}>
                    <CartesianGrid stroke="#2a2a3e" />
                    <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 10 }} interval={30} />
                    <YAxis stroke="#6b7280" tick={{ fontSize: 10 }} domain={['auto', 'auto']} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #2a2a3e', borderRadius: '4px' }}
                      labelStyle={{ color: '#9ca3af' }}
                    />
                    <ReferenceLine y={initialCapital} stroke="#6b7280" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="value" stroke="#2196F3" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            {/* Trade list */}
            <div className="bg-[#1e1e2e] rounded overflow-hidden">
              <div className="px-4 py-2 border-b border-[#2a2a3e]">
                <h3 className="text-sm text-gray-400">Trade History ({result.trades.length} trades)</h3>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-[#131722]">
                    <tr className="text-gray-400 text-xs">
                      <th className="px-4 py-2 text-left">#</th>
                      <th className="px-4 py-2 text-left">Side</th>
                      <th className="px-4 py-2 text-left">Entry</th>
                      <th className="px-4 py-2 text-left">Exit</th>
                      <th className="px-4 py-2 text-right">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.slice(0, 20).map(trade => (
                      <tr key={trade.id} className="border-t border-[#2a2a3e] hover:bg-[#2a2a3e]/30">
                        <td className="px-4 py-2 text-gray-400">{trade.id}</td>
                        <td className={`px-4 py-2 ${trade.side === 'long' ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                          {trade.side.toUpperCase()}
                        </td>
                        <td className="px-4 py-2 text-white font-mono">${trade.entryPrice.toLocaleString()}</td>
                        <td className="px-4 py-2 text-white font-mono">${trade.exitPrice.toLocaleString()}</td>
                        <td className={`px-4 py-2 text-right font-mono ${trade.pnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                          {trade.pnl >= 0 ? '+' : ''}{trade.pnlPercent}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Backtester;

import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface CopyTrade {
  id: string;
  trader: {
    display_name: string;
    win_rate: number;
  };
  symbol: string;
  direction: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  status: string;
  created_at: string;
}

export const CopyTrading: React.FC = () => {
  const [copyTrades, setCopyTrades] = useState<CopyTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'open' | 'closed'>('open');

  useEffect(() => {
    fetchCopyTrades();
  }, []);

  const fetchCopyTrades = async () => {
    try {
      const response = await apiFetch('/social/copy-trades/');
      if (response.ok) {
        setCopyTrades(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch copy trades:', error);
      // Mock data
      setCopyTrades([
        {
          id: '1',
          trader: { display_name: 'CryptoMaster', win_rate: 72.5 },
          symbol: 'BTC-USDT',
          direction: 'buy',
          quantity: 0.1,
          entry_price: 67000,
          current_price: 67500,
          pnl: 50,
          pnl_percent: 0.75,
          status: 'open',
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '2',
          trader: { display_name: 'AlphaTrader', win_rate: 68.3 },
          symbol: 'ETH-USDT',
          direction: 'sell',
          quantity: 2,
          entry_price: 3500,
          current_price: 3450,
          pnl: 100,
          pnl_percent: 1.43,
          status: 'open',
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
        {
          id: '3',
          trader: { display_name: 'CryptoMaster', win_rate: 72.5 },
          symbol: 'SOL-USDT',
          direction: 'buy',
          quantity: 50,
          entry_price: 175,
          current_price: 180,
          pnl: 250,
          pnl_percent: 2.86,
          status: 'closed',
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredTrades = copyTrades.filter(t => t.status === activeTab);
  const totalPnl = copyTrades.reduce((sum, t) => sum + t.pnl, 0);
  const winRate = copyTrades.filter(t => t.pnl > 0).length / copyTrades.length * 100;

  if (loading) {
    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 animate-pulse">
        <div className="h-6 bg-white/20 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-white/10 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-white">📋 Copy Trading</h2>
        <div className="flex space-x-4 text-sm">
          <div className="text-center">
            <div className={`font-semibold ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)}%
            </div>
            <div className="text-purple-200/60">Total P&L</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-white">{winRate.toFixed(1)}%</div>
            <div className="text-purple-200/60">Win Rate</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-white/5 rounded-lg p-1 mb-6">
        {(['open', 'closed'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              activeTab === tab
                ? 'bg-purple-600 text-white'
                : 'text-purple-200/60 hover:text-white'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)} ({copyTrades.filter(t => t.status === tab).length})
          </button>
        ))}
      </div>

      {/* Trades List */}
      <div className="space-y-3">
        {filteredTrades.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-purple-200/60">No {activeTab} copy trades</p>
          </div>
        ) : (
          filteredTrades.map((trade) => (
            <div
              key={trade.id}
              className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all"
            >
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  trade.direction === 'buy' ? 'bg-green-500/20' : 'bg-red-500/20'
                }`}>
                  <span className={`text-lg font-bold ${
                    trade.direction === 'buy' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.direction === 'buy' ? '↑' : '↓'}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-white">{trade.symbol}</div>
                  <div className="text-sm text-purple-200/60">
                    From {trade.trader.display_name}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <div className="text-sm text-white">${trade.entry_price.toLocaleString()}</div>
                  <div className="text-xs text-purple-200/60">Entry</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-white">${trade.current_price.toLocaleString()}</div>
                  <div className="text-xs text-purple-200/60">Current</div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-semibold ${
                    trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.pnl >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                  </div>
                  <div className="text-xs text-purple-200/60">P&L</div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                  trade.status === 'open' 
                    ? 'bg-blue-500/20 text-blue-400' 
                    : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {trade.status}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CopyTrading;

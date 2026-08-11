import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface Position {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  value: number;
}

interface PortfolioStats {
  totalValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  unrealizedPnl: number;
  buyingPower: number;
}

const COLORS = ['#2196F3', '#26a69a', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4'];

export const PortfolioTracker: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [stats, setStats] = useState<PortfolioStats | null>(null);
  const [activeTab, setActiveTab] = useState<'positions' | 'allocation'>('positions');

  useEffect(() => {
    generateMockData();
    const interval = setInterval(generateMockData, 5000);
    return () => clearInterval(interval);
  }, []);

  const generateMockData = () => {
    const mockPositions: Position[] = [
      { symbol: 'BTC-USDT', side: 'long', quantity: 0.5, entryPrice: 65000, currentPrice: 67500 + (Math.random()-0.5)*1000, pnl: 0, pnlPercent: 0, value: 0 },
      { symbol: 'ETH-USDT', side: 'long', quantity: 5, entryPrice: 3200, currentPrice: 3450 + (Math.random()-0.5)*50, pnl: 0, pnlPercent: 0, value: 0 },
      { symbol: 'SOL-USDT', side: 'long', quantity: 50, entryPrice: 150, currentPrice: 180 + (Math.random()-0.5)*5, pnl: 0, pnlPercent: 0, value: 0 },
      { symbol: 'BNB-USDT', side: 'short', quantity: 10, entryPrice: 650, currentPrice: 620 + (Math.random()-0.5)*10, pnl: 0, pnlPercent: 0, value: 0 },
    ];

    const updatedPositions = mockPositions.map(p => {
      const value = p.quantity * p.currentPrice;
      const cost = p.quantity * p.entryPrice;
      const pnl = p.side === 'long' ? value - cost : cost - value;
      const pnlPercent = (pnl / cost) * 100;
      return { ...p, pnl, pnlPercent, value };
    });

    const totalValue = updatedPositions.reduce((sum, p) => sum + p.value, 0);
    const totalPnl = updatedPositions.reduce((sum, p) => sum + p.pnl, 0);
    const totalCost = updatedPositions.reduce((sum, p) => sum + p.quantity * p.entryPrice, 0);

    setPositions(updatedPositions);
    setStats({
      totalValue,
      totalPnl,
      totalPnlPercent: (totalPnl / totalCost) * 100,
      unrealizedPnl: totalPnl,
      buyingPower: 50000 - totalValue,
    });
  };

  const allocationData = positions.map((p, i) => ({
    name: p.symbol.replace('-USDT', ''),
    value: Math.abs(p.value),
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="bg-[#131722] rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-white font-semibold">Portfolio</h2>
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-3">
          <div className="text-xs text-gray-400 mb-1">Total Balance</div>
          <div className="text-2xl font-mono text-white">${stats.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className={`text-sm font-mono mt-1 ${stats.totalPnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
            {stats.totalPnl >= 0 ? '+' : ''}${stats.totalPnl.toFixed(2)} ({stats.totalPnlPercent >= 0 ? '+' : ''}{stats.totalPnlPercent.toFixed(2)}%)
          </div>
          <div className="grid grid-cols-2 gap-4 mt-3">
            <div>
              <div className="text-[10px] text-gray-500">Unrealized P&L</div>
              <div className={`text-sm font-mono ${stats.unrealizedPnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                {stats.unrealizedPnl >= 0 ? '+' : ''}${stats.unrealizedPnl.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500">Buying Power</div>
              <div className="text-sm font-mono text-white">${stats.buyingPower.toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[#2a2a3e]">
        <button
          onClick={() => setActiveTab('positions')}
          className={`flex-1 py-2 text-xs font-medium ${
            activeTab === 'positions' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-white'
          }`}
        >
          Positions ({positions.length})
        </button>
        <button
          onClick={() => setActiveTab('allocation')}
          className={`flex-1 py-2 text-xs font-medium ${
            activeTab === 'allocation' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-white'
          }`}
        >
          Allocation
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'positions' ? (
          <div className="divide-y divide-[#2a2a3e]">
            {positions.map((pos, i) => (
              <div key={pos.symbol} className="px-4 py-3 hover:bg-[#1e1e2e]/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-[#2a2a3e] flex items-center justify-center text-xs font-bold text-white">
                      {pos.symbol.charAt(0)}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{pos.symbol.replace('-USDT', '')}</div>
                      <div className="text-[10px] text-gray-400">
                        {pos.side.toUpperCase()} {pos.quantity}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-mono text-white">${pos.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                    <div className={`text-xs font-mono ${pos.pnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                      {pos.pnl >= 0 ? '+' : ''}{pos.pnlPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
                <div className="flex justify-between mt-2 text-[10px] text-gray-500">
                  <span>Entry: ${pos.entryPrice.toLocaleString()}</span>
                  <span>Current: ${pos.currentPrice.toLocaleString()}</span>
                  <span className={pos.pnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}>
                    P&L: {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4">
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={allocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {allocationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #2a2a3e', borderRadius: '4px' }}
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Value']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-4">
              {allocationData.map((item, i) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-white">{item.name}</span>
                  </div>
                  <span className="text-sm text-gray-400">${item.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioTracker;

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
  source: string;
}

const COLORS = ['#2196F3', '#26a69a', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4'];

const DEFAULT_POSITIONS = [
  { symbol: 'BTCUSDT', side: 'long' as const, quantity: 0.5, entryPrice: 65000 },
  { symbol: 'ETHUSDT', side: 'long' as const, quantity: 5, entryPrice: 3200 },
  { symbol: 'SOLUSDT', side: 'long' as const, quantity: 50, entryPrice: 150 },
  { symbol: 'BNBUSDT', side: 'short' as const, quantity: 10, entryPrice: 650 },
];

export const PortfolioTracker: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [stats, setStats] = useState<PortfolioStats | null>(null);

  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchPrices = async () => {
    let source = 'binance';

    try {
      const symbols = DEFAULT_POSITIONS.map(p => p.symbol);
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      if (response.ok) {
        const data = await response.json();
        const priceMap: Record<string, number> = {};

        data.forEach((t: any) => {
          if (symbols.includes(t.symbol)) {
            priceMap[t.symbol] = parseFloat(t.lastPrice);
          }
        });

        if (Object.keys(priceMap).length > 0) {
          updatePositions(priceMap, source);
          return;
        }
      }
    } catch (e) {}

    try {
      const ids = 'bitcoin,ethereum,solana,binancecoin';
      const response = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd`
      );
      if (response.ok) {
        const data = await response.json();
        const priceMap: Record<string, number> = {
          'BTCUSDT': data.bitcoin?.usd || 0,
          'ETHUSDT': data.ethereum?.usd || 0,
          'SOLUSDT': data.solana?.usd || 0,
          'BNBUSDT': data.binancecoin?.usd || 0,
        };
        source = 'coingecko';
        updatePositions(priceMap, source);
      }
    } catch (e) {}
  };

  const updatePositions = (priceMap: Record<string, number>, source: string) => {
    const updatedPositions = DEFAULT_POSITIONS.map(p => {
      const currentPrice = priceMap[p.symbol] || p.entryPrice;
      const value = p.quantity * currentPrice;
      const cost = p.quantity * p.entryPrice;
      const pnl = p.side === 'long' ? value - cost : cost - value;
      const pnlPercent = (pnl / cost) * 100;
      return { ...p, currentPrice, pnl, pnlPercent, value };
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
      source,
    });
  };

  const allocationData = positions.map((p, i) => ({
    name: p.symbol.replace('USDT', ''),
    value: Math.abs(p.value),
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="bg-[#131722] h-full flex">
      {/* Left: Portfolio Summary */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Stats Header */}
        {stats && (
          <div className="px-4 py-3 border-b border-[#2a2a3e] flex items-center gap-6">
            <div>
              <div className="text-[10px] text-gray-500">Total Balance</div>
              <div className="text-lg font-mono text-white">${stats.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500">P&L</div>
              <div className={`text-lg font-mono ${stats.totalPnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                {stats.totalPnl >= 0 ? '+' : ''}{stats.totalPnlPercent.toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500">Unrealized</div>
              <div className={`text-sm font-mono ${stats.unrealizedPnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                {stats.unrealizedPnl >= 0 ? '+' : ''}${stats.unrealizedPnl.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500">Buying Power</div>
              <div className="text-sm font-mono text-white">${stats.buyingPower.toLocaleString()}</div>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                stats.source === 'binance' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
              }`}>
                {stats.source === 'binance' ? '⚡' : '🦎'} {stats.source}
              </span>
            </div>
          </div>
        )}

        {/* Positions - Horizontal Scroll */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden">
          <div className="flex h-full">
            {positions.map((pos, i) => (
              <div key={pos.symbol} className="flex-shrink-0 w-48 px-4 py-3 border-r border-[#2a2a3e] hover:bg-[#1e1e2e]/50 flex flex-col justify-center">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white" style={{ backgroundColor: COLORS[i % COLORS.length] }}>
                    {pos.symbol.charAt(0)}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{pos.symbol.replace('USDT', '')}</div>
                    <div className="text-[10px] text-gray-500">{pos.side.toUpperCase()} {pos.quantity}</div>
                  </div>
                </div>
                <div className="flex justify-between items-end mt-1">
                  <div>
                    <div className="text-xs text-gray-400">Value</div>
                    <div className="text-sm font-mono text-white">${pos.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-400">P&L</div>
                    <div className={`text-sm font-mono ${pos.pnl >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                      {pos.pnl >= 0 ? '+' : ''}{pos.pnlPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Allocation Chart */}
      <div className="w-64 border-l border-[#2a2a3e] flex flex-col">
        <div className="px-3 py-2 border-b border-[#2a2a3e]">
          <span className="text-xs font-medium text-gray-400">Allocation</span>
        </div>
        <div className="flex-1 flex items-center justify-center p-2">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={allocationData}
                cx="50%"
                cy="50%"
                innerRadius={30}
                outerRadius={55}
                paddingAngle={2}
                dataKey="value"
              >
                {allocationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #2a2a3e', borderRadius: '4px', fontSize: '11px' }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Value']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Legend */}
        <div className="px-3 py-2 border-t border-[#2a2a3e] space-y-1">
          {allocationData.map((item) => (
            <div key={item.name} className="flex items-center justify-between text-[10px]">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded" style={{ backgroundColor: item.color }} />
                <span className="text-gray-300">{item.name}</span>
              </div>
              <span className="text-gray-500">${item.value.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PortfolioTracker;

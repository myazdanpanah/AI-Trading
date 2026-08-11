import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LearningInsights } from '../feedback/LearningInsights';
import { SignalsPanel } from './SignalsPanel';
import { AnalysisPanel } from './AnalysisPanel';
import { OrderBook } from '../trading/OrderBook';
import { Watchlist } from '../trading/Watchlist';
import { TradingViewChart } from '../trading/TradingViewChart';
import { Backtester } from '../trading/Backtester';
import { PortfolioTracker } from '../trading/PortfolioTracker';
import { APISettings } from '../settings/APISettings';
import { apiFetch } from '../../utils/api';

interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface DashboardProps {
  onLogout?: () => void;
  mockMode?: boolean;
  onToggleMock?: () => void;
}

const generateCandlestickData = () => {
  const data = [];
  let basePrice = 67500;
  const now = new Date();
  
  for (let i = 99; i >= 0; i--) {
    const date = new Date(now);
    date.setMinutes(date.getMinutes() - i * 15);
    
    const volatility = 0.003 + Math.random() * 0.005;
    const open = basePrice;
    const change = (Math.random() - 0.48) * volatility * basePrice;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * volatility * basePrice * 0.3;
    const low = Math.min(open, close) - Math.random() * volatility * basePrice * 0.3;
    const volume = 500000000 + Math.random() * 1000000000;
    
    data.push({
      date: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume: Math.round(volume),
    });
    
    basePrice = close;
  }
  return data;
};

export const Dashboard: React.FC<DashboardProps> = ({ onLogout, mockMode, onToggleMock }) => {
  const [activeTab, setActiveTab] = useState<'trading' | 'signals' | 'feedback' | 'analysis' | 'backtest' | 'settings'>('trading');
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC-USDT');
  
  const candlestickData = useMemo(() => generateCandlestickData(), []);

  useEffect(() => {
    setTimeout(() => setLoading(false), 500);
  }, []);

  const tabs = [
    { id: 'trading' as const, label: 'Trading', icon: '📈' },
    { id: 'signals' as const, label: 'Signals', icon: '🎯' },
    { id: 'feedback' as const, label: 'Feedback', icon: '🧠' },
    { id: 'analysis' as const, label: 'Analysis', icon: '📊' },
    { id: 'backtest' as const, label: 'Backtest', icon: '🔬' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="h-screen flex flex-col bg-[#131722]">
      {/* Header */}
      <header className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">C</span>
            </div>
            <span className="text-white font-semibold hidden sm:block">CryptoAI</span>
          </div>
          
          {/* Tabs */}
          <nav className="flex items-center gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  activeTab === tab.id
                    ? 'bg-[#2a2a3e] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-[#2a2a3e]/50'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                <span className="hidden md:inline">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-[#26a69a] rounded-full animate-pulse" />
            <span className="text-gray-400">Live</span>
          </div>
          {mockMode && (
            <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">
              Demo
            </span>
          )}
          <button
            onClick={onToggleMock}
            className="px-3 py-1 text-xs bg-[#2a2a3e] text-gray-300 rounded hover:bg-[#3a3a4e]"
          >
            {mockMode ? 'Connect' : 'Demo'}
          </button>
          <button
            onClick={onLogout}
            className="px-3 py-1 text-xs text-gray-400 hover:text-white"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 min-h-0 overflow-hidden">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
          </div>
        ) : (
          <>
            {/* Trading Tab */}
            {activeTab === 'trading' && (
              <div className="h-full flex">
                {/* Left: Watchlist */}
                <div className="w-64 flex-shrink-0 border-r border-[#2a2a3e]">
                  <Watchlist 
                    onSelectSymbol={setSelectedSymbol}
                    selectedSymbol={selectedSymbol}
                  />
                </div>
                
                {/* Center: Chart */}
                <div className="flex-1 min-w-0">
                  <TradingViewChart data={candlestickData} />
                </div>
                
                {/* Right: Order Book + Portfolio */}
                <div className="w-72 flex-shrink-0 border-l border-[#2a2a3e] flex flex-col">
                  <div className="flex-1 min-h-0 overflow-y-auto border-b border-[#2a2a3e]">
                    <OrderBook symbol={selectedSymbol} />
                  </div>
                  <div className="h-80 flex-shrink-0">
                    <PortfolioTracker />
                  </div>
                </div>
              </div>
            )}

            {/* Backtest Tab */}
            {activeTab === 'backtest' && (
              <div className="h-full p-4">
                <Backtester />
              </div>
            )}

            {/* Other Tabs */}
            {activeTab === 'signals' && (
              <div className="h-full p-4">
                <SignalsPanel />
              </div>
            )}
            {activeTab === 'feedback' && (
              <div className="h-full p-4">
                <LearningInsights />
              </div>
            )}
            {activeTab === 'analysis' && (
              <div className="h-full p-4">
                <AnalysisPanel />
              </div>
            )}
            {activeTab === 'settings' && (
              <div className="h-full p-4">
                <APISettings />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

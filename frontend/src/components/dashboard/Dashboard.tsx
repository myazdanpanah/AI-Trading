import React, { useState, useEffect, useRef } from 'react';
import { LearningInsights } from '../feedback/LearningInsights';
import { SignalsPanel } from './SignalsPanel';
import { AnalysisPanel } from './AnalysisPanel';
import { OrderBook } from '../trading/OrderBook';
import { Watchlist } from '../trading/Watchlist';
import { TradingViewChart } from '../trading/TradingViewChart';
import { Backtester } from '../trading/Backtester';
import { PortfolioTracker } from '../trading/PortfolioTracker';
import { APISettings } from '../settings/APISettings';
import { UserSettings } from '../settings/UserSettings';
import { NewsSettings } from '../settings/NewsSettings';
import { SignalDashboard } from './SignalDashboard';
import { JournalPanel } from '../journal/JournalPanel';
import { ForecastPanel } from '../forecast/ForecastPanel';
import { useWatchlist } from '../../contexts/WatchlistContext';

interface DashboardProps {
  onLogout?: () => void;
}

// Ticker Tape component
const TickerTape: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const idRef = useRef('tv-ticker-tape');

  useEffect(() => {
    if (!containerRef.current) return;

    const timer = setTimeout(() => {
      if (typeof (window as any).TradingView === 'undefined') return;
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '';

      new (window as any).TradingView.TickerTape({
        container_id: idRef.current,
        symbols: [
          { proName: 'BINANCE:BTCUSDT', title: 'Bitcoin' },
          { proName: 'BINANCE:ETHUSDT', title: 'Ethereum' },
          { proName: 'BINANCE:SOLUSDT', title: 'Solana' },
          { proName: 'BINANCE:BNBUSDT', title: 'BNB' },
          { proName: 'BINANCE:XRPUSDT', title: 'XRP' },
          { proName: 'BINANCE:ADAUSDT', title: 'ADA' },
          { proName: 'BINANCE:DOGEUSDT', title: 'DOGE' },
          { proName: 'BINANCE:DOTUSDT', title: 'DOT' },
          { proName: 'BINANCE:AVAXUSDT', title: 'AVAX' },
          { proName: 'BINANCE:LINKUSDT', title: 'LINK' },
        ],
        colorTheme: 'dark',
        isTransparent: false,
        showSymbolLogo: true,
        locale: 'en',
      });
    }, 300);

    return () => clearTimeout(timer);
  }, []);

  return <div id={idRef.current} ref={containerRef} className="w-full" />;
};

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState<'trading' | 'signals' | 'journal' | 'feedback' | 'analysis' | 'forecast' | 'backtest' | 'settings' | 'news-settings' | 'user-settings'>('trading');
  const [loading, setLoading] = useState(true);
  const [showPortfolio, setShowPortfolio] = useState(true);
  const { selectedSymbol, setSelectedSymbol } = useWatchlist();

  useEffect(() => {
    if (!document.getElementById('tv-script')) {
      const script = document.createElement('script');
      script.id = 'tv-script';
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      document.head.appendChild(script);
    }

    setTimeout(() => setLoading(false), 500);
  }, []);

  const tabs = [
    { id: 'trading' as const, label: 'Trading', icon: '📈' },
    { id: 'signals' as const, label: 'Signals', icon: '🎯' },
    { id: 'journal' as const, label: 'Journal', icon: '📝' },
    { id: 'feedback' as const, label: 'Feedback', icon: '🧠' },
    { id: 'analysis' as const, label: 'Analysis', icon: '📊' },
    { id: 'forecast' as const, label: 'Forecast', icon: '🔮' },
    { id: 'backtest' as const, label: 'Backtest', icon: '🔬' },
    { id: 'news-settings' as const, label: 'News', icon: '📰' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
    { id: 'user-settings' as const, label: 'Profile', icon: '👤' },
  ];

  return (
    <div className="h-screen flex flex-col bg-[#131722]">
      {/* Ticker Tape */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] flex-shrink-0" style={{ height: 44 }}>
        {loading ? null : <TickerTape />}
      </div>

      {/* Header */}
      <header className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">C</span>
            </div>
            <span className="text-white font-semibold hidden sm:block">CryptoAI</span>
          </div>

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
          <button onClick={onLogout} className="px-3 py-1 text-xs text-gray-400 hover:text-white">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 min-h-0 overflow-hidden">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto" />
              <p className="text-gray-400 text-sm mt-2">Loading TradingView...</p>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'trading' && (
              <div className="h-full flex flex-col">
                {/* Top: Watchlist + Chart + OrderBook */}
                <div className="flex-1 min-h-0 flex">
                  {/* Left: Watchlist */}
                  <div className="w-72 flex-shrink-0 border-r border-[#2a2a3e]">
                    <Watchlist onSelectSymbol={setSelectedSymbol} selectedSymbol={selectedSymbol} />
                  </div>
                  
                  {/* Center: Chart */}
                  <div className="flex-1 min-w-0">
                    <TradingViewChart symbol={selectedSymbol} />
                  </div>
                  
                  {/* Right: OrderBook */}
                  <div className="w-80 flex-shrink-0 border-l border-[#2a2a3e]">
                    <OrderBook symbol={selectedSymbol} />
                  </div>
                </div>
                
                {/* Bottom: Portfolio (collapsible) */}
                <div className="flex-shrink-0 border-t border-[#2a2a3e]">
                  <button
                    onClick={() => setShowPortfolio(!showPortfolio)}
                    className="w-full px-4 py-2 bg-[#1e1e2e] flex items-center justify-between hover:bg-[#2a2a3e] transition-colors"
                  >
                    <span className="text-sm font-medium text-white">💼 Portfolio</span>
                    <span className="text-gray-400 text-xs">
                      {showPortfolio ? '▼ Hide' : '▶ Show'}
                    </span>
                  </button>
                  {showPortfolio && (
                    <div className="h-64">
                      <PortfolioTracker />
                    </div>
                  )}
                </div>
              </div>
            )}
            {activeTab === 'backtest' && (
              <div className="h-full p-4"><Backtester /></div>
            )}
            {activeTab === 'signals' && (
              <div className="h-full"><SignalDashboard /></div>
            )}
            {activeTab === 'journal' && (
              <div className="h-full"><JournalPanel /></div>
            )}
            {activeTab === 'feedback' && (
              <div className="h-full p-4"><LearningInsights /></div>
            )}
            {activeTab === 'analysis' && (
              <div className="h-full p-4"><AnalysisPanel /></div>
            )}
            {activeTab === 'forecast' && (
              <div className="h-full"><ForecastPanel /></div>
            )}
            {activeTab === 'news-settings' && (
              <div className="h-full p-4"><NewsSettings /></div>
            )}
            {activeTab === 'settings' && (
              <div className="h-full p-4"><APISettings /></div>
            )}
            {activeTab === 'user-settings' && (
              <div className="h-full p-4"><UserSettings /></div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

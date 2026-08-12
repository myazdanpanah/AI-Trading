import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { LanguageSwitcher } from '../common/LanguageSwitcher';
import { TradingViewChart } from '../trading/TradingViewChart';
import { OrderBook } from '../trading/OrderBook';
import { WatchlistManager } from '../trading/WatchlistManager';
import { PortfolioTracker } from '../trading/PortfolioTracker';
import { SignalDashboard } from './SignalDashboard';
import { AnalysisPanel } from './AnalysisPanel';
import JournalPanel from '../journal/JournalPanel';
import SettingsPanel from '../settings/SettingsPanel';
import { ChatBot } from '../trading/ChatBot';

type TabType = 'trading' | 'signals' | 'analysis' | 'journal' | 'settings';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const { selectedSymbol, setSelectedSymbol } = useWatchlist();
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<TabType>('trading');

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'trading', label: t('nav.trading'), icon: '📈' },
    { id: 'signals', label: t('nav.signals'), icon: '🔔' },
    { id: 'analysis', label: t('nav.analysis'), icon: '📊' },
    { id: 'journal', label: t('nav.journal'), icon: '📝' },
    { id: 'settings', label: t('nav.settings'), icon: '⚙️' },
  ];

  return (
    <div className={`min-h-screen bg-gray-900 text-white ${language === 'fa' ? 'rtl' : 'ltr'}`}>
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-blue-400">🤖 Crypto AI</h1>
            <nav className="flex gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <span className="text-sm text-gray-400">
              {user?.username || 'User'}
            </span>
            <button
              onClick={logout}
              className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 transition-colors"
            >
              {t('nav.logout')}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-4">
        {activeTab === 'trading' && (
          <div className="flex flex-col h-[calc(100vh-80px)]">
            {/* Trading Layout */}
            <div className="flex gap-4 flex-1 min-h-0">
              {/* Left Sidebar - Watchlist */}
              <div className="w-72 flex-shrink-0">
                <WatchlistManager
                  selectedSymbol={selectedSymbol}
                  onSelectSymbol={setSelectedSymbol}
                />
              </div>

              {/* Center - Chart */}
              <div className="flex-1 min-w-0">
                <TradingViewChart symbol={selectedSymbol} />
              </div>

              {/* Right Sidebar - Order Book */}
              <div className="w-80 flex-shrink-0">
                <OrderBook symbol={selectedSymbol} />
              </div>
            </div>

            {/* Bottom - Portfolio */}
            <div className="mt-4">
              <PortfolioTracker />
            </div>
          </div>
        )}

        {activeTab === 'signals' && <SignalDashboard />}
        {activeTab === 'analysis' && <AnalysisPanel />}
        {activeTab === 'journal' && <JournalPanel />}
        {activeTab === 'settings' && <SettingsPanel />}
      </main>

      {/* Floating ChatBot */}
      <ChatBot />
    </div>
  );
};

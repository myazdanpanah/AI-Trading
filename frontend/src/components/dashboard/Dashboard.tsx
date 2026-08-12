import React, { useState, Component, ErrorInfo, ReactNode } from 'react';
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

// Error Boundary Component
class ErrorBoundary extends Component<{ children: ReactNode; tabName: string }, { hasError: boolean; error: string }> {
  constructor(props: { children: ReactNode; tabName: string }) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Error in ${this.props.tabName}:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-white mb-2">Something went wrong</h3>
          <p className="text-gray-400 text-sm mb-4">{this.state.error}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: '' })}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

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

  const renderTabContent = () => {
    switch (activeTab) {
      case 'trading':
        return (
          <div className="flex flex-col h-[calc(100vh-80px)]">
            <div className="flex gap-4 flex-1 min-h-0">
              <div className="w-72 flex-shrink-0">
                <WatchlistManager
                  selectedSymbol={selectedSymbol}
                  onSelectSymbol={setSelectedSymbol}
                />
              </div>
              <div className="flex-1 min-w-0">
                <TradingViewChart symbol={selectedSymbol} />
              </div>
              <div className="w-80 flex-shrink-0">
                <OrderBook symbol={selectedSymbol} />
              </div>
            </div>
            <div className="mt-4">
              <PortfolioTracker />
            </div>
          </div>
        );
      case 'signals':
        return (
          <ErrorBoundary tabName="Signals">
            <SignalDashboard />
          </ErrorBoundary>
        );
      case 'analysis':
        return (
          <ErrorBoundary tabName="Analysis">
            <AnalysisPanel />
          </ErrorBoundary>
        );
      case 'journal':
        return (
          <ErrorBoundary tabName="Journal">
            <JournalPanel />
          </ErrorBoundary>
        );
      case 'settings':
        return (
          <ErrorBoundary tabName="Settings">
            <SettingsPanel />
          </ErrorBoundary>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`min-h-screen bg-gray-900 text-white flex flex-col ${language === 'fa' ? 'rtl' : 'ltr'}`}>
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex-shrink-0">
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
      <main className="flex-1 p-4 overflow-auto">
        {renderTabContent()}
      </main>

      {/* Floating ChatBot */}
      <ChatBot />
    </div>
  );
};

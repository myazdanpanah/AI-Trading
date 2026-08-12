import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import APISettings from './APISettings';
import UserSettings from './UserSettings';
import NewsSettings from './NewsSettings';
import AlertManager from './AlertManager';

type SettingsTab = 'api' | 'user' | 'news' | 'social' | 'alerts';

export const SettingsPanel: React.FC = () => {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<SettingsTab>('api');

  const tabs = [
    { id: 'api' as SettingsTab, label: t('settings.apiKeys'), icon: '🔑' },
    { id: 'user' as SettingsTab, label: t('settings.profile'), icon: '👤' },
    { id: 'news' as SettingsTab, label: '📰 News Sources', icon: '📰' },
    { id: 'social' as SettingsTab, label: '💬 Social Media', icon: '💬' },
    { id: 'alerts' as SettingsTab, label: '🔔 Alerts', icon: '🔔' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h2 className="text-lg font-semibold mb-4">{t('settings.title')}</h2>
      
      {/* Tab Navigation */}
      <div className="flex gap-2 mb-4 border-b border-gray-700 pb-2 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === 'api' && <APISettings />}
        {activeTab === 'user' && <UserSettings />}
        {(activeTab === 'news' || activeTab === 'social') && (
          <NewsSettings initialSection={activeTab === 'social' ? 'social' : 'news'} />
        )}
        {activeTab === 'alerts' && <AlertManager />}
      </div>
    </div>
  );
};

export default SettingsPanel;

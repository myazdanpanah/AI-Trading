import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import APISettings from './APISettings';
import UserSettings from './UserSettings';
import NewsSettings from './NewsSettings';

type SettingsTab = 'api' | 'user' | 'news';

export const SettingsPanel: React.FC = () => {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<SettingsTab>('api');

  const tabs = [
    { id: 'api' as SettingsTab, label: t('settings.apiKeys'), icon: '🔑' },
    { id: 'user' as SettingsTab, label: t('settings.profile'), icon: '👤' },
    { id: 'news' as SettingsTab, label: t('settings.notifications'), icon: '📰' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h2 className="text-lg font-semibold mb-4">{t('settings.title')}</h2>
      
      {/* Tab Navigation */}
      <div className="flex gap-2 mb-4 border-b border-gray-700 pb-2">
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
        {activeTab === 'news' && <NewsSettings />}
      </div>
    </div>
  );
};

export default SettingsPanel;

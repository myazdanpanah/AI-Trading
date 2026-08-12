import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
      <button
        onClick={() => setLanguage('en')}
        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
          language === 'en'
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('fa')}
        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
          language === 'fa'
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        FA
      </button>
    </div>
  );
};

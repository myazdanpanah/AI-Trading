import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
      <button
        onClick={() => setLanguage('en')}
        className={`px-2 py-1 text-xs rounded transition-all ${
          language === 'en'
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('fa')}
        className={`px-2 py-1 text-xs rounded transition-all ${
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

export default LanguageSwitcher;

import { useLanguage } from '../contexts/LanguageContext';

/**
 * Custom hook to get translations for the current language
 * Usage: const { t } = useTranslation();
 *        <span>{t('nav.trading')}</span>
 */
export function useTranslation() {
  const { t, language } = useLanguage();
  return { t, language };
}

export default useTranslation;

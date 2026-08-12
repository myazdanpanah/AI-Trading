import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';

interface NewsSource {
  id: string;
  name: string;
  url: string;
  source_type: string;
  category: string;
  icon: string;
  reliability_score: number;
  is_active: boolean;
  is_primary: boolean;
  tags: string[];
  last_fetched: string | null;
  fetch_count: number;
}

const SOURCE_TYPES = [
  { value: 'rss', label: 'RSS Feed', icon: '📡' },
  { value: 'api', label: 'API', icon: '🔌' },
  { value: 'web', label: 'Website', icon: '🌐' },
  { value: 'twitter', label: 'Twitter/X', icon: '🐦' },
  { value: 'reddit', label: 'Reddit', icon: '📰' },
  { value: 'telegram', label: 'Telegram', icon: '💬' },
  { value: 'discord', label: 'Discord', icon: '🎮' },
  { value: 'youtube', label: 'YouTube', icon: '📺' },
];

const NEWS_CATEGORIES = [
  { value: 'crypto_news', label: 'Crypto News', icon: '📰' },
  { value: 'market_data', label: 'Market Data', icon: '📊' },
  { value: 'politics', label: 'Politics & Regulation', icon: '⚖️' },
  { value: 'economics', label: 'Economics & Finance', icon: '🏦' },
  { value: 'geopolitics', label: 'Geopolitics', icon: '🌍' },
  { value: 'conflict', label: 'Conflict & Tensions', icon: '⚔️' },
  { value: 'energy', label: 'Energy & Oil', icon: '⛽' },
  { value: 'technology', label: 'Technology', icon: '💻' },
  { value: 'on_chain', label: 'On-Chain Data', icon: '⛓️' },
  { value: 'regulation', label: 'Regulatory', icon: '📜' },
  { value: 'central_banks', label: 'Central Banks & Fed', icon: '🏛️' },
  { value: 'commodities', label: 'Commodities & Gold', icon: '🥇' },
];

const SOCIAL_CATEGORIES = [
  { value: 'social', label: 'Social Sentiment', icon: '💬' },
  { value: 'twitter', label: 'Twitter/X Analysts', icon: '🐦' },
  { value: 'twitter_news', label: 'Twitter/X News', icon: '🐦' },
  { value: 'twitter_geopolitics', label: 'Twitter/X Geopolitics', icon: '🌍' },
  { value: 'reddit', label: 'Reddit', icon: '📰' },
  { value: 'telegram', label: 'Telegram', icon: '💬' },
  { value: 'youtube', label: 'YouTube', icon: '📺' },
];

const CATEGORY_COLORS: Record<string, string> = {
  crypto_news: 'bg-blue-500/20 text-blue-400',
  market_data: 'bg-green-500/20 text-green-400',
  politics: 'bg-red-500/20 text-red-400',
  economics: 'bg-yellow-500/20 text-yellow-400',
  geopolitics: 'bg-orange-500/20 text-orange-400',
  conflict: 'bg-red-600/20 text-red-300',
  energy: 'bg-amber-500/20 text-amber-400',
  technology: 'bg-purple-500/20 text-purple-400',
  social: 'bg-indigo-500/20 text-indigo-400',
  on_chain: 'bg-cyan-500/20 text-cyan-400',
  regulation: 'bg-pink-500/20 text-pink-400',
  central_banks: 'bg-emerald-500/20 text-emerald-400',
  commodities: 'bg-yellow-600/20 text-yellow-300',
  twitter: 'bg-sky-500/20 text-sky-400',
  twitter_news: 'bg-sky-400/20 text-sky-300',
  twitter_geopolitics: 'bg-orange-400/20 text-orange-300',
  reddit: 'bg-orange-500/20 text-orange-400',
  telegram: 'bg-blue-400/20 text-blue-300',
  discord: 'bg-indigo-400/20 text-indigo-300',
  youtube: 'bg-red-500/20 text-red-400',
};

// ═══════════════════════════════════════════════════════════════
// TRUSTED NEWS SOURCES - Comprehensive coverage
// ═══════════════════════════════════════════════════════════════
const TRUSTED_DEFAULTS = [
  // ── Crypto News ──
  { name: 'CoinDesk', url: 'https://www.coindesk.com/arc/outboundfeeds/rss/', category: 'crypto_news', icon: '📰', reliability: 85 },
  { name: 'CoinTelegraph', url: 'https://cointelegraph.com/rss', category: 'crypto_news', icon: '📰', reliability: 80 },
  { name: 'The Block', url: 'https://www.theblock.co/rss.xml', category: 'crypto_news', icon: '📰', reliability: 85 },
  { name: 'Decrypt', url: 'https://decrypt.co/feed', category: 'crypto_news', icon: '📰', reliability: 75 },
  { name: 'Bitcoin Magazine', url: 'https://bitcoinmagazine.com/.rss/full/', category: 'crypto_news', icon: '₿', reliability: 80 },
  { name: 'DL News', url: 'https://www.dlnews.com/rss/', category: 'crypto_news', icon: '📰', reliability: 75 },

  // ── Economics & Finance ──
  { name: 'Reuters Business', url: 'https://www.reutersagency.com/feed/', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Bloomberg Markets', url: 'https://feeds.bloomberg.com/markets/news.rss', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Financial Times', url: 'https://www.ft.com/rss/home', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Wall Street Journal', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'CNBC Markets', url: 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258', category: 'economics', icon: '🏦', reliability: 90 },
  { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/', category: 'economics', icon: '🏦', reliability: 85 },

  // ── Politics & Regulation ──
  { name: 'Politico', url: 'https://rss.politico.com/economy.xml', category: 'politics', icon: '⚖️', reliability: 90 },
  { name: 'Reuters Politics', url: 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best', category: 'politics', icon: '⚖️', reliability: 95 },
  { name: 'Coinbase Blog', url: 'https://blog.coinbase.com/feed', category: 'regulation', icon: '📜', reliability: 80 },
  { name: 'SEC.gov', url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&dateb=&owner=include&count=40&search_text=&action=getcompany', category: 'regulation', icon: '📜', reliability: 95 },
  { name: 'CFTC Press Releases', url: 'https://www.cftc.gov/PressRoom/PressReleases', category: 'regulation', icon: '📜', reliability: 90 },

  // ── Geopolitics ──
  { name: 'BBC World', url: 'http://feeds.bbci.co.uk/news/world/rss.xml', category: 'geopolitics', icon: '🌍', reliability: 90 },
  { name: 'Al Jazeera', url: 'https://www.aljazeera.com/xml/rss/all.xml', category: 'geopolitics', icon: '🌍', reliability: 85 },
  { name: 'Reuters World', url: 'https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best', category: 'geopolitics', icon: '🌍', reliability: 95 },
  { name: 'AP News World', url: 'https://rsshub.app/apnews/topics/world-news', category: 'geopolitics', icon: '🌍', reliability: 90 },
  { name: 'The Guardian World', url: 'https://www.theguardian.com/world/rss', category: 'geopolitics', icon: '🌍', reliability: 88 },
  { name: 'Foreign Policy', url: 'https://foreignpolicy.com/feed/', category: 'geopolitics', icon: '🌍', reliability: 85 },
  { name: 'The Diplomat', url: 'https://thediplomat.com/feed/', category: 'geopolitics', icon: '🌍', reliability: 80 },

  // ── Conflict & Tensions ──
  { name: 'War on the Rocks', url: 'https://warontherocks.com/feed/', category: 'conflict', icon: '⚔️', reliability: 85 },
  { name: 'Crisis Group', url: 'https://www.crisisgroup.org/rss.xml', category: 'conflict', icon: '⚔️', reliability: 90 },
  { name: 'ACLED Data', url: 'https://acleddata.com/feed/', category: 'conflict', icon: '⚔️', reliability: 85 },
  { name: 'Jane\'s Defence', url: 'https://www.janes.com/feeds/news', category: 'conflict', icon: '⚔️', reliability: 88 },
  { name: 'OSINTdefender (X)', url: 'https://nitter.net/OSINTdefender', category: 'conflict', icon: '🐦', reliability: 70 },
  { name: 'Iran International', url: 'https://www.iranintl.com/en/rss', category: 'conflict', icon: '🇮🇷', reliability: 80 },

  // ── Energy & Oil ──
  { name: 'Reuters Energy', url: 'https://www.reutersagency.com/feed/?best-topics=energy', category: 'energy', icon: '⛽', reliability: 95 },
  { name: 'OilPrice.com', url: 'https://oilprice.com/rss/main', category: 'energy', icon: '⛽', reliability: 85 },
  { name: 'Rigzone', url: 'https://www.rigzone.com/news/rss/rigzone_latest.aspx', category: 'energy', icon: '⛽', reliability: 80 },
  { name: 'EIA.gov', url: 'https://www.eia.gov/rss/todayinenergy.xml', category: 'energy', icon: '⛽', reliability: 95 },
  { name: 'OPEC News', url: 'https://www.opec.org/opec_web/en/press_room.rss', category: 'energy', icon: '⛽', reliability: 85 },
  { name: 'Natural Gas Intelligence', url: 'https://www.naturalgasintel.com/rss/', category: 'energy', icon: '⛽', reliability: 80 },

  // ── Central Banks & Fed ──
  { name: 'Federal Reserve', url: 'https://www.federalreserve.gov/feeds/press_all.xml', category: 'central_banks', icon: '🏛️', reliability: 95 },
  { name: 'ECB Press', url: 'https://www.ecb.europa.eu/rss/press.html', category: 'central_banks', icon: '🏛️', reliability: 95 },
  { name: 'BIS Speeches', url: 'https://www.bis.org/doclist/cbspeeches.rss', category: 'central_banks', icon: '🏛️', reliability: 90 },
  { name: 'IMF Blog', url: 'https://www.imf.org/en/News/rss', category: 'central_banks', icon: '🏛️', reliability: 90 },

  // ── Commodities & Gold ──
  { name: 'Kitco Gold News', url: 'https://www.kitco.com/rss/gold.xml', category: 'commodities', icon: '🥇', reliability: 85 },
  { name: 'Metals Daily', url: 'https://www.metalsdaily.com/rss/feed.xml', category: 'commodities', icon: '🥇', reliability: 80 },

  // ── Technology ──
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/', category: 'technology', icon: '💻', reliability: 85 },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index', category: 'technology', icon: '💻', reliability: 85 },
];

// ═══════════════════════════════════════════════════════════════
// SOCIAL MEDIA & X ACCOUNTS - Key analysts & news feeds
// ═══════════════════════════════════════════════════════════════
const SOCIAL_DEFAULTS = [
  // ── X/Twitter - Crypto Analysts ──
  { name: '@CryptoCapo_', url: 'https://x.com/CryptoCapo_', category: 'twitter', icon: '🐦', reliability: 70, source_type: 'twitter' },
  { name: '@elaboratebull', url: 'https://x.com/100trillionUSD', category: 'twitter', icon: '🐦', reliability: 75, source_type: 'twitter' },
  { name: '@PlanB_', url: 'https://x.com/100trillionUSD', category: 'twitter', icon: '₿', reliability: 75, source_type: 'twitter' },
  { name: '@WillyWoo', url: 'https://x.com/woonomic', category: 'twitter', icon: '📊', reliability: 75, source_type: 'twitter' },
  { name: '@CryptoHayes', url: 'https://x.com/CryptoHayes', category: 'twitter', icon: '🐦', reliability: 70, source_type: 'twitter' },
  { name: '@cobie', url: 'https://x.com/caborneto', category: 'twitter', icon: '🐦', reliability: 70, source_type: 'twitter' },
  { name: '@inversebrah', url: 'https://x.com/inversebrah', category: 'twitter', icon: '🐦', reliability: 65, source_type: 'twitter' },
  { name: '@ Pentosh1', url: 'https://x.com/Pentosh1', category: 'twitter', icon: '📈', reliability: 70, source_type: 'twitter' },
  { name: '@BluntzCapital', url: 'https://x.com/Bluntz_Capital', category: 'twitter', icon: '🐦', reliability: 70, source_type: 'twitter' },
  { name: '@CryptoISO', url: 'https://x.com/CryptoISO', category: 'twitter', icon: '🐦', reliability: 65, source_type: 'twitter' },

  // ── X/Twitter - News & Breaking ──
  { name: '@WatcherGuru', url: 'https://x.com/WatcherGuru', category: 'twitter_news', icon: '📢', reliability: 80, source_type: 'twitter' },
  { name: '@BitcoinMagazine', url: 'https://x.com/BitcoinMagazine', category: 'twitter_news', icon: '📰', reliability: 85, source_type: 'twitter' },
  { name: '@coindesk', url: 'https://x.com/coindesk', category: 'twitter_news', icon: '📰', reliability: 85, source_type: 'twitter' },
  { name: '@Cointelegraph', url: 'https://x.com/Cointelegraph', category: 'twitter_news', icon: '📰', reliability: 80, source_type: 'twitter' },
  { name: '@tier10k', url: 'https://x.com/tier10k', category: 'twitter_news', icon: '⚡', reliability: 75, source_type: 'twitter' },
  { name: '@WhaleAlert', url: 'https://x.com/WhaleAlert', category: 'twitter_news', icon: '🐋', reliability: 80, source_type: 'twitter' },
  { name: '@unusual_whales', url: 'https://x.com/unusual_whales', category: 'twitter_news', icon: '🐟', reliability: 75, source_type: 'twitter' },

  // ── X/Twitter - Geopolitics & Conflict ──
  { name: '@sentdefender', url: 'https://x.com/sentdefender', category: 'twitter_geopolitics', icon: '⚔️', reliability: 80, source_type: 'twitter' },
  { name: '@OSINTdefender', url: 'https://x.com/OSINTdefender', category: 'twitter_geopolitics', icon: '🔍', reliability: 75, source_type: 'twitter' },
  { name: '@spectaborindex', url: 'https://x.com/spectaborindex', category: 'twitter_geopolitics', icon: '📊', reliability: 70, source_type: 'twitter' },
  { name: '@spectatorindex', url: 'https://x.com/spectatorindex', category: 'twitter_geopolitics', icon: '📰', reliability: 75, source_type: 'twitter' },
  { name: '@BNONews', url: 'https://x.com/BNONews', category: 'twitter_geopolitics', icon: '📢', reliability: 80, source_type: 'twitter' },
  { name: '@LiveSquawk', url: 'https://x.com/LiveSquawk', category: 'twitter_geopolitics', icon: '📡', reliability: 80, source_type: 'twitter' },
  { name: '@firstsquawk', url: 'https://x.com/firstsquawk', category: 'twitter_geopolitics', icon: '⚡', reliability: 75, source_type: 'twitter' },
  { name: '@FinancialJuice', url: 'https://x.com/Financialjuice1', category: 'twitter_geopolitics', icon: '📰', reliability: 75, source_type: 'twitter' },
  { name: '@disclosetv', url: 'https://x.com/disclosetv', category: 'twitter_geopolitics', icon: '📺', reliability: 70, source_type: 'twitter' },
  { name: '@IranIntl', url: 'https://x.com/IranIntl', category: 'twitter_geopolitics', icon: '🇮🇷', reliability: 80, source_type: 'twitter' },
  { name: '@IranIntl_En', url: 'https://x.com/IranIntl_En', category: 'twitter_geopolitics', icon: '🇮🇷', reliability: 80, source_type: 'twitter' },

  // ── X/Twitter - Macro & Oil ──
  { name: '@zaborsky_petr', url: 'https://x.com/zaborsky_petr', category: 'twitter_geopolitics', icon: '🌍', reliability: 70, source_type: 'twitter' },
  { name: '@GoldTelegraph_', url: 'https://x.com/GoldTelegraph_', category: 'twitter_geopolitics', icon: '🥇', reliability: 70, source_type: 'twitter' },
  { name: '@SantiagoAuFund', url: 'https://x.com/SantiagoAuFund', category: 'twitter_geopolitics', icon: '🥇', reliability: 70, source_type: 'twitter' },

  // ── Reddit ──
  { name: 'r/cryptocurrency', url: 'https://www.reddit.com/r/cryptocurrency/.rss', category: 'reddit', icon: '📰', reliability: 65, source_type: 'reddit' },
  { name: 'r/bitcoin', url: 'https://www.reddit.com/r/bitcoin/.rss', category: 'reddit', icon: '📰', reliability: 70, source_type: 'reddit' },
  { name: 'r/CryptoMarkets', url: 'https://www.reddit.com/r/CryptoMarkets/.rss', category: 'reddit', icon: '📊', reliability: 60, source_type: 'reddit' },
  { name: 'r/SecurityAnalysis', url: 'https://www.reddit.com/r/SecurityAnalysis/.rss', category: 'reddit', icon: '📊', reliability: 65, source_type: 'reddit' },

  // ── Telegram ──
  { name: 'Crypto Telegram Groups', url: 'https://t.me/s/cryptocurrencynews', category: 'telegram', icon: '💬', reliability: 55, source_type: 'telegram' },
  { name: 'DeFi Telegram', url: 'https://t.me/s/defi_news', category: 'telegram', icon: '💬', reliability: 55, source_type: 'telegram' },

  // ── YouTube ──
  { name: 'Coin Bureau', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCqqJQcXSS1SCa_pjTggmeZQ', category: 'youtube', icon: '📺', reliability: 80, source_type: 'youtube' },
  { name: 'Coffeezilla', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCFbMTIlLUj5N6v3yztqitmw', category: 'youtube', icon: '📺', reliability: 75, source_type: 'youtube' },
  { name: 'Ivan on Tech', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_cKlfpE530YZ2uppiQt3ng', category: 'youtube', icon: '📺', reliability: 70, source_type: 'youtube' },
  { name: 'Real Vision', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCN4mY17MU8Axj1eEIb17h6g', category: 'youtube', icon: '📺', reliability: 80, source_type: 'youtube' },
  { name: 'Macro Voices', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCgSSmGcCnU8NzU5q9t9a9Bg', category: 'youtube', icon: '📺', reliability: 75, source_type: 'youtube' },
];

interface ModalState {
  show: boolean;
  mode: 'add' | 'edit';
  source: Partial<NewsSource>;
}

interface NewsSettingsProps {
  initialSection?: 'news' | 'social';
}

export const NewsSettings: React.FC<NewsSettingsProps> = ({ initialSection = 'news' }) => {
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<ModalState>({ show: false, mode: 'add', source: {} });
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [activeSection, setActiveSection] = useState<'news' | 'social'>(initialSection);
  const [seeding, setSeeding] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchSources = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/journal/sources/');
      if (response.ok) {
        const data = await response.json();
        setSources(data.results || data);
      }
    } catch (err) {
      console.error('Failed to fetch sources');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSources(); }, [fetchSources]);

  const seedDefaults = async (section: 'news' | 'social') => {
    setSeeding(true);
    const defaults = section === 'news' ? TRUSTED_DEFAULTS : SOCIAL_DEFAULTS;
    for (const def of defaults) {
      try {
        await apiFetch('/journal/sources/', {
          method: 'POST',
          body: JSON.stringify({
            name: def.name,
            url: def.url,
            source_type: (def as any).source_type || 'rss',
            category: def.category,
            icon: def.icon,
            reliability_score: def.reliability,
            is_active: true,
            tags: [],
          }),
        });
      } catch (err) { /* skip duplicates */ }
    }
    fetchSources();
    setSeeding(false);
  };

  const addSource = async () => {
    try {
      const response = await apiFetch('/journal/sources/', {
        method: 'POST',
        body: JSON.stringify(modal.source),
      });
      if (response.ok) {
        setModal({ show: false, mode: 'add', source: {} });
        fetchSources();
      }
    } catch (err) { console.error('Failed to add source'); }
  };

  const updateSource = async () => {
    if (!modal.source.id) return;
    try {
      const response = await apiFetch(`/journal/sources/${modal.source.id}/`, {
        method: 'PATCH',
        body: JSON.stringify(modal.source),
      });
      if (response.ok) {
        setModal({ show: false, mode: 'add', source: {} });
        fetchSources();
      }
    } catch (err) { console.error('Failed to update source'); }
  };

  const toggleSource = async (source: NewsSource) => {
    try {
      await apiFetch(`/journal/sources/${source.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !source.is_active }),
      });
      fetchSources();
    } catch (err) { console.error('Failed to toggle source'); }
  };

  const deleteSource = async (id: string) => {
    if (!confirm('Delete this source?')) return;
    try {
      await apiFetch(`/journal/sources/${id}/`, { method: 'DELETE' });
      fetchSources();
    } catch (err) { console.error('Failed to delete source'); }
  };

  const openEditModal = (source: NewsSource) => {
    setModal({ show: true, mode: 'edit', source: { ...source } });
  };

  const openAddModal = () => {
    setModal({
      show: true,
      mode: 'add',
      source: {
        name: '',
        url: '',
        source_type: 'rss',
        category: activeSection === 'news' ? 'crypto_news' : 'twitter',
        icon: activeSection === 'news' ? '📰' : '🐦',
        reliability_score: 70,
        is_active: true,
        is_primary: false,
        tags: [],
      },
    });
  };

  const categories = activeSection === 'news' ? NEWS_CATEGORIES : SOCIAL_CATEGORIES;
  const allCategories = [...NEWS_CATEGORIES, ...SOCIAL_CATEGORIES];

  const sectionSources = sources.filter(s => {
    if (activeSection === 'news') {
      return NEWS_CATEGORIES.some(c => c.value === s.category);
    }
    return SOCIAL_CATEGORIES.some(c => c.value === s.category);
  });

  const filteredSources = sectionSources.filter(s => {
    const matchesCategory = filterCategory === 'all' || s.category === filterCategory;
    const matchesSearch = !searchQuery || s.name.toLowerCase().includes(searchQuery.toLowerCase()) || s.url.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const categoryStats = categories.map(cat => ({
    ...cat,
    count: sectionSources.filter(s => s.category === cat.value).length,
    active: sectionSources.filter(s => s.category === cat.value && s.is_active).length,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            {activeSection === 'news' ? '📰 News Sources' : '💬 Social & X Accounts'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {activeSection === 'news'
              ? 'Trusted sources for geopolitical, economic, conflict, and market analysis'
              : 'X/Twitter analysts, breaking news, geopolitics, and crypto accounts'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => seedDefaults(activeSection)}
            disabled={seeding}
            className="px-4 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 text-sm disabled:opacity-50"
          >
            {seeding ? 'Loading...' : 'Load Defaults'}
          </button>
          <button
            onClick={openAddModal}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            + Add Source
          </button>
        </div>
      </div>

      {/* Section Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => { setActiveSection('news'); setFilterCategory('all'); }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeSection === 'news' ? 'bg-blue-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          📰 News ({sources.filter(s => NEWS_CATEGORIES.some(c => c.value === s.category)).length})
        </button>
        <button
          onClick={() => { setActiveSection('social'); setFilterCategory('all'); }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeSection === 'social' ? 'bg-indigo-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          💬 Social & X ({sources.filter(s => SOCIAL_CATEGORIES.some(c => c.value === s.category)).length})
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search sources..."
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm placeholder-gray-500"
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">✕</button>
        )}
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilterCategory('all')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            filterCategory === 'all' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          All ({sectionSources.length})
        </button>
        {categoryStats.filter(c => c.count > 0).map(cat => (
          <button
            key={cat.value}
            onClick={() => setFilterCategory(filterCategory === cat.value ? 'all' : cat.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              filterCategory === cat.value ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            {cat.icon} {cat.label} ({cat.active}/{cat.count})
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white/5 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-white">{sectionSources.length}</div>
          <div className="text-xs text-gray-400">Total Sources</div>
        </div>
        <div className="bg-green-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{sectionSources.filter(s => s.is_active).length}</div>
          <div className="text-xs text-gray-400">Active</div>
        </div>
        <div className="bg-blue-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{sectionSources.filter(s => s.reliability_score >= 80).length}</div>
          <div className="text-xs text-gray-400">High Trust (80+)</div>
        </div>
        <div className="bg-purple-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-400">{new Set(sectionSources.map(s => s.category)).size}</div>
          <div className="text-xs text-gray-400">Categories</div>
        </div>
      </div>

      {/* Source List */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
        </div>
      ) : filteredSources.length === 0 ? (
        <div className="bg-white/5 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">{activeSection === 'news' ? '📰' : '🐦'}</div>
          <p className="text-gray-400 mb-4">
            {sectionSources.length === 0 ? `No ${activeSection === 'news' ? 'news' : 'social'} sources configured` : 'No sources match your filter'}
          </p>
          <button onClick={() => seedDefaults(activeSection)} className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            Load Default Sources
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredSources.map((source) => (
            <div
              key={source.id}
              className={`bg-white/5 rounded-lg p-4 flex items-center gap-4 transition-all ${
                source.is_active ? 'border border-white/10' : 'border border-white/5 opacity-50'
              }`}
            >
              <span className="text-2xl">{source.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">{source.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[source.category] || 'bg-gray-500/20 text-gray-400'}`}>
                    {allCategories.find(c => c.value === source.category)?.label || source.category}
                  </span>
                  <span className="text-xs text-gray-500">{source.source_type.toUpperCase()}</span>
                  {source.is_primary && <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400">PRIMARY</span>}
                </div>
                <div className="text-xs text-gray-500 truncate mt-1">{source.url}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-300">
                  Trust: <span className={`font-bold ${
                    source.reliability_score >= 80 ? 'text-green-400' :
                    source.reliability_score >= 60 ? 'text-yellow-400' : 'text-red-400'
                  }`}>{source.reliability_score}</span>/100
                </div>
                <div className="text-xs text-gray-500">{source.fetch_count || 0} fetches</div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => openEditModal(source)} className="text-gray-500 hover:text-blue-400 text-sm px-2" title="Edit">✏️</button>
                <button
                  onClick={() => toggleSource(source)}
                  className={`w-10 h-6 rounded-full transition-all ${source.is_active ? 'bg-green-500' : 'bg-gray-600'}`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white transition-all ${source.is_active ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
                <button onClick={() => deleteSource(source.id)} className="text-gray-500 hover:text-red-400 text-sm px-2" title="Delete">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Impact Weights */}
      {activeSection === 'news' && (
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">📊 Impact Weights by Category</h3>
          <p className="text-xs text-gray-400 mb-3">How different categories affect market analysis and signals:</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { category: 'Geopolitics & Conflict', weight: '25%', impact: 'High', color: 'text-red-400', desc: 'Wars, sanctions, tensions' },
              { category: 'Central Banks & Fed', weight: '20%', impact: 'High', color: 'text-emerald-400', desc: 'Interest rates, QE/QT' },
              { category: 'Energy & Oil Prices', weight: '15%', impact: 'High', color: 'text-amber-400', desc: 'OPEC, supply shocks' },
              { category: 'Economics & Finance', weight: '15%', impact: 'High', color: 'text-yellow-400', desc: 'GDP, inflation, jobs' },
              { category: 'Crypto News', weight: '10%', impact: 'Medium', color: 'text-blue-400', desc: 'Adoption, ETFs, hacks' },
              { category: 'Regulation', weight: '10%', impact: 'Medium', color: 'text-pink-400', desc: 'SEC, CFTC, global regs' },
              { category: 'Social Sentiment', weight: '5%', impact: 'Low', color: 'text-indigo-400', desc: 'X/Twitter mood' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-white/5 rounded">
                <div>
                  <span className="text-sm text-gray-300">{item.category}</span>
                  <div className="text-[10px] text-gray-500">{item.desc}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs ${item.color}`}>{item.weight}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    item.impact === 'High' ? 'bg-red-500/20 text-red-400' :
                    item.impact === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>{item.impact}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Social Media Tips */}
      {activeSection === 'social' && (
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">💡 X/Twitter Coverage Guide</h3>
          <div className="space-y-2 text-sm text-gray-400">
            <p>• <span className="text-sky-400 font-medium">Crypto Analysts</span> — Technical analysis, trade ideas, market calls</p>
            <p>• <span className="text-sky-300 font-medium">News Accounts</span> — Breaking crypto news, whale alerts, exchange issues</p>
            <p>• <span className="text-orange-300 font-medium">Geopolitics</span> — Breaking conflict news, sanctions, military movements, tensions</p>
            <p>• <span className="text-yellow-400 font-medium">Macro</span> — Gold, oil, commodities, central bank actions</p>
            <p>• <span className="text-red-400 font-medium">Conflict</span> — War updates, OSINT, defense analysis, risk events</p>
            <p className="mt-2 text-xs text-gray-500">⚠ Reliability scores affect how much weight each source gets in analysis. Higher = more trusted.</p>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {modal.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e1e2e] rounded-xl p-6 w-full max-w-md border border-white/20">
            <h3 className="text-lg font-bold text-white mb-4">
              {modal.mode === 'add' ? 'Add Source' : 'Edit Source'}
            </h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400">Name</label>
                <input type="text" value={modal.source.name || ''} onChange={(e) => setModal({ ...modal, source: { ...modal.source, name: e.target.value } })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1" placeholder="Reuters" />
              </div>
              <div>
                <label className="text-sm text-gray-400">URL</label>
                <input type="url" value={modal.source.url || ''} onChange={(e) => setModal({ ...modal, source: { ...modal.source, url: e.target.value } })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1" placeholder="https://..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-gray-400">Type</label>
                  <select value={modal.source.source_type || 'rss'} onChange={(e) => setModal({ ...modal, source: { ...modal.source, source_type: e.target.value } })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1">
                    {SOURCE_TYPES.map(t => <option key={t.value} value={t.value} className="bg-slate-800">{t.icon} {t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Category</label>
                  <select value={modal.source.category || 'crypto_news'} onChange={(e) => setModal({ ...modal, source: { ...modal.source, category: e.target.value } })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1">
                    {[...NEWS_CATEGORIES, ...SOCIAL_CATEGORIES].map(c => <option key={c.value} value={c.value} className="bg-slate-800">{c.icon} {c.label}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-400">Reliability: {modal.source.reliability_score || 70}/100</label>
                <input type="range" min="0" max="100" value={modal.source.reliability_score || 70}
                  onChange={(e) => setModal({ ...modal, source: { ...modal.source, reliability_score: parseInt(e.target.value) } })} className="w-full mt-1" />
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <input type="checkbox" checked={modal.source.is_primary || false}
                    onChange={(e) => setModal({ ...modal, source: { ...modal.source, is_primary: e.target.checked } })} className="rounded" />
                  Primary source (always included)
                </label>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={() => setModal({ show: false, mode: 'add', source: {} })} className="flex-1 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20">Cancel</button>
              <button onClick={modal.mode === 'add' ? addSource : updateSource} disabled={!modal.source.name || !modal.source.url}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50">
                {modal.mode === 'add' ? 'Add Source' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsSettings;

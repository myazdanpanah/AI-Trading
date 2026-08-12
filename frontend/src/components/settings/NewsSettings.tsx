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
  { value: 'technology', label: 'Technology', icon: '💻' },
  { value: 'energy', label: 'Energy & Mining', icon: '⚡' },
  { value: 'on_chain', label: 'On-Chain Data', icon: '⛓️' },
  { value: 'regulation', label: 'Regulatory', icon: '📜' },
];

const SOCIAL_CATEGORIES = [
  { value: 'social', label: 'Social Sentiment', icon: '💬' },
  { value: 'twitter', label: 'Twitter/X', icon: '🐦' },
  { value: 'reddit', label: 'Reddit', icon: '📰' },
  { value: 'telegram', label: 'Telegram', icon: '💬' },
  { value: 'discord', label: 'Discord', icon: '🎮' },
  { value: 'youtube', label: 'YouTube', icon: '📺' },
  { value: 'tiktok', label: 'TikTok', icon: '🎵' },
];

const CATEGORY_COLORS: Record<string, string> = {
  crypto_news: 'bg-blue-500/20 text-blue-400',
  market_data: 'bg-green-500/20 text-green-400',
  politics: 'bg-red-500/20 text-red-400',
  economics: 'bg-yellow-500/20 text-yellow-400',
  geopolitics: 'bg-orange-500/20 text-orange-400',
  technology: 'bg-purple-500/20 text-purple-400',
  energy: 'bg-amber-500/20 text-amber-400',
  social: 'bg-indigo-500/20 text-indigo-400',
  on_chain: 'bg-cyan-500/20 text-cyan-400',
  regulation: 'bg-pink-500/20 text-pink-400',
  twitter: 'bg-sky-500/20 text-sky-400',
  reddit: 'bg-orange-500/20 text-orange-400',
  telegram: 'bg-blue-400/20 text-blue-300',
  discord: 'bg-indigo-400/20 text-indigo-300',
  youtube: 'bg-red-500/20 text-red-400',
  tiktok: 'bg-pink-400/20 text-pink-300',
};

const TRUSTED_DEFAULTS = [
  // Crypto News
  { name: 'CoinDesk', url: 'https://www.coindesk.com/arc/outboundfeeds/rss/', category: 'crypto_news', icon: '📰', reliability: 85 },
  { name: 'CoinTelegraph', url: 'https://cointelegraph.com/rss', category: 'crypto_news', icon: '📰', reliability: 80 },
  { name: 'The Block', url: 'https://www.theblock.co/rss.xml', category: 'crypto_news', icon: '📰', reliability: 85 },
  { name: 'Decrypt', url: 'https://decrypt.co/feed', category: 'crypto_news', icon: '📰', reliability: 75 },
  // Economics & Finance
  { name: 'Reuters Business', url: 'https://www.reutersagency.com/feed/', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Bloomberg Markets', url: 'https://feeds.bloomberg.com/markets/news.rss', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Financial Times', url: 'https://www.ft.com/rss/home', category: 'economics', icon: '🏦', reliability: 95 },
  { name: 'Wall Street Journal', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', category: 'economics', icon: '🏦', reliability: 95 },
  // Politics & Regulation
  { name: 'Politico', url: 'https://rss.politico.com/economy.xml', category: 'politics', icon: '⚖️', reliability: 90 },
  { name: 'Reuters Politics', url: 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best', category: 'politics', icon: '⚖️', reliability: 95 },
  { name: 'Coinbase Blog', url: 'https://blog.coinbase.com/feed', category: 'regulation', icon: '📜', reliability: 80 },
  // Geopolitics
  { name: 'BBC World', url: 'http://feeds.bbci.co.uk/news/world/rss.xml', category: 'geopolitics', icon: '🌍', reliability: 90 },
  { name: 'Al Jazeera', url: 'https://www.aljazeera.com/xml/rss/all.xml', category: 'geopolitics', icon: '🌍', reliability: 85 },
  // Technology
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/', category: 'technology', icon: '💻', reliability: 85 },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index', category: 'technology', icon: '💻', reliability: 85 },
  // Energy
  { name: 'Reuters Energy', url: 'https://www.reutersagency.com/feed/?best-topics=energy', category: 'energy', icon: '⚡', reliability: 90 },
];

const SOCIAL_DEFAULTS = [
  { name: 'Crypto Twitter Trending', url: 'https://nitter.net/search?q=crypto', category: 'twitter', icon: '🐦', reliability: 60, source_type: 'twitter' },
  { name: 'r/cryptocurrency', url: 'https://www.reddit.com/r/cryptocurrency/.rss', category: 'reddit', icon: '📰', reliability: 65, source_type: 'reddit' },
  { name: 'r/bitcoin', url: 'https://www.reddit.com/r/bitcoin/.rss', category: 'reddit', icon: '📰', reliability: 70, source_type: 'reddit' },
  { name: 'Crypto Telegram Groups', url: 'https://t.me/s/cryptocurrencynews', category: 'telegram', icon: '💬', reliability: 55, source_type: 'telegram' },
  { name: 'Coin Bureau (YouTube)', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCqqJQcXSS1SCa_pjTggmeZQ', category: 'youtube', icon: '📺', reliability: 80, source_type: 'youtube' },
  { name: 'Coffeezilla (YouTube)', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCFbMTIlLUj5N6v3yztqitmw', category: 'youtube', icon: '📺', reliability: 75, source_type: 'youtube' },
  { name: 'Ivan on Tech', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_cKlfpE530YZ2uppiQt3ng', category: 'youtube', icon: '📺', reliability: 70, source_type: 'youtube' },
  { name: 'BitBoy Crypto', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCjemXLfYXaLQNMqiWgRIM3g', category: 'youtube', icon: '📺', reliability: 60, source_type: 'youtube' },
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
    } catch (err) {
      console.error('Failed to add source');
    }
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
    } catch (err) {
      console.error('Failed to update source');
    }
  };

  const toggleSource = async (source: NewsSource) => {
    try {
      await apiFetch(`/journal/sources/${source.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !source.is_active }),
      });
      fetchSources();
    } catch (err) {
      console.error('Failed to toggle source');
    }
  };

  const deleteSource = async (id: string) => {
    if (!confirm('Delete this source?')) return;
    try {
      await apiFetch(`/journal/sources/${id}/`, { method: 'DELETE' });
      fetchSources();
    } catch (err) {
      console.error('Failed to delete source');
    }
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
        category: activeSection === 'news' ? 'crypto_news' : 'social',
        icon: activeSection === 'news' ? '📰' : '💬',
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
            {activeSection === 'news' ? '📰 News Sources' : '💬 Social Media Sources'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {activeSection === 'news'
              ? 'Configure trusted news sources for political, economic, and market analysis'
              : 'Configure social media sources for sentiment analysis and trend detection'}
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
            activeSection === 'news'
              ? 'bg-blue-600 text-white'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          📰 News Sources ({sources.filter(s => NEWS_CATEGORIES.some(c => c.value === s.category)).length})
        </button>
        <button
          onClick={() => { setActiveSection('social'); setFilterCategory('all'); }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeSection === 'social'
              ? 'bg-indigo-600 text-white'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          💬 Social Media ({sources.filter(s => SOCIAL_CATEGORIES.some(c => c.value === s.category)).length})
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search sources by name or URL..."
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm placeholder-gray-500"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
          >
            ✕
          </button>
        )}
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilterCategory('all')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            filterCategory === 'all'
              ? 'bg-purple-600 text-white'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          All ({sectionSources.length})
        </button>
        {categoryStats.filter(c => c.count > 0).map(cat => (
          <button
            key={cat.value}
            onClick={() => setFilterCategory(filterCategory === cat.value ? 'all' : cat.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              filterCategory === cat.value
                ? 'bg-purple-600 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
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
          <div className="text-2xl font-bold text-purple-400">{sectionSources.filter(s => s.is_primary).length}</div>
          <div className="text-xs text-gray-400">Primary Sources</div>
        </div>
      </div>

      {/* Source List */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
        </div>
      ) : filteredSources.length === 0 ? (
        <div className="bg-white/5 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">{activeSection === 'news' ? '📰' : '💬'}</div>
          <p className="text-gray-400 mb-4">
            {sectionSources.length === 0
              ? `No ${activeSection === 'news' ? 'news' : 'social media'} sources configured`
              : 'No sources match your filter'}
          </p>
          <button
            onClick={() => seedDefaults(activeSection)}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
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
                  {source.is_primary && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400">PRIMARY</span>
                  )}
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
                <div className="text-xs text-gray-500">
                  {source.fetch_count || 0} fetches
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => openEditModal(source)}
                  className="text-gray-500 hover:text-blue-400 text-sm px-2"
                  title="Edit source"
                >
                  ✏️
                </button>
                <button
                  onClick={() => toggleSource(source)}
                  className={`w-10 h-6 rounded-full transition-all ${
                    source.is_active ? 'bg-green-500' : 'bg-gray-600'
                  }`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white transition-all ${
                    source.is_active ? 'translate-x-5' : 'translate-x-1'
                  }`} />
                </button>
                <button
                  onClick={() => deleteSource(source.id)}
                  className="text-gray-500 hover:text-red-400 text-sm px-2"
                  title="Delete source"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Impact Weights */}
      {activeSection === 'news' && (
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">📊 News Impact Weights</h3>
          <p className="text-xs text-gray-400 mb-3">How different news categories affect signal generation:</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { category: 'Politics & Regulation', weight: '25%', impact: 'High', color: 'text-red-400' },
              { category: 'Economics & Finance', weight: '25%', impact: 'High', color: 'text-yellow-400' },
              { category: 'Crypto News', weight: '20%', impact: 'Medium', color: 'text-blue-400' },
              { category: 'Geopolitics', weight: '15%', impact: 'Medium', color: 'text-orange-400' },
              { category: 'Technology', weight: '10%', impact: 'Low', color: 'text-purple-400' },
              { category: 'Social Sentiment', weight: '5%', impact: 'Low', color: 'text-indigo-400' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-white/5 rounded">
                <span className="text-sm text-gray-300">{item.category}</span>
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
          <h3 className="text-white font-medium mb-3">💡 Social Media Analysis Tips</h3>
          <div className="space-y-2 text-sm text-gray-400">
            <p>• <span className="text-blue-400">Twitter/X</span> — Track crypto influencer sentiment and trending topics</p>
            <p>• <span className="text-orange-400">Reddit</span> — Monitor r/cryptocurrency and r/bitcoin for community mood</p>
            <p>• <span className="text-blue-300">Telegram</span> — Follow official project channels for announcements</p>
            <p>• <span className="text-red-400">YouTube</span> — Track crypto analyst channels for market outlook</p>
            <p>• Reliability scores affect how much weight each source gets in analysis</p>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {modal.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e1e2e] rounded-xl p-6 w-full max-w-md border border-white/20">
            <h3 className="text-lg font-bold text-white mb-4">
              {modal.mode === 'add' ? 'Add News Source' : 'Edit Source'}
            </h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400">Name</label>
                <input
                  type="text"
                  value={modal.source.name || ''}
                  onChange={(e) => setModal({ ...modal, source: { ...modal.source, name: e.target.value } })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="Reuters"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">URL (RSS feed, API endpoint, or website)</label>
                <input
                  type="url"
                  value={modal.source.url || ''}
                  onChange={(e) => setModal({ ...modal, source: { ...modal.source, url: e.target.value } })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="https://example.com/rss"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-gray-400">Type</label>
                  <select
                    value={modal.source.source_type || 'rss'}
                    onChange={(e) => setModal({ ...modal, source: { ...modal.source, source_type: e.target.value } })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  >
                    {SOURCE_TYPES.map(t => (
                      <option key={t.value} value={t.value} className="bg-slate-800">{t.icon} {t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Category</label>
                  <select
                    value={modal.source.category || 'crypto_news'}
                    onChange={(e) => setModal({ ...modal, source: { ...modal.source, category: e.target.value } })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  >
                    {[...NEWS_CATEGORIES, ...SOCIAL_CATEGORIES].map(c => (
                      <option key={c.value} value={c.value} className="bg-slate-800">{c.icon} {c.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-400">Icon (emoji)</label>
                <input
                  type="text"
                  value={modal.source.icon || '📰'}
                  onChange={(e) => setModal({ ...modal, source: { ...modal.source, icon: e.target.value } })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="📰"
                  maxLength={4}
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">Reliability Score: {modal.source.reliability_score || 70}/100</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={modal.source.reliability_score || 70}
                  onChange={(e) => setModal({ ...modal, source: { ...modal.source, reliability_score: parseInt(e.target.value) } })}
                  className="w-full mt-1"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Low Trust</span>
                  <span>High Trust</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <input
                    type="checkbox"
                    checked={modal.source.is_primary || false}
                    onChange={(e) => setModal({ ...modal, source: { ...modal.source, is_primary: e.target.checked } })}
                    className="rounded"
                  />
                  Primary source (always included)
                </label>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setModal({ show: false, mode: 'add', source: {} })}
                className="flex-1 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20"
              >
                Cancel
              </button>
              <button
                onClick={modal.mode === 'add' ? addSource : updateSource}
                disabled={!modal.source.name || !modal.source.url}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
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

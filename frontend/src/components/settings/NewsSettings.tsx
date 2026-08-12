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
];

const CATEGORIES = [
  { value: 'crypto_news', label: 'Crypto News', icon: '📰', description: 'Cryptocurrency-specific news' },
  { value: 'market_data', label: 'Market Data', icon: '📊', description: 'Real-time market data' },
  { value: 'politics', label: 'Politics & Regulation', icon: '⚖️', description: 'Political events affecting markets' },
  { value: 'economics', label: 'Economics & Finance', icon: '🏦', description: 'Macroeconomic indicators' },
  { value: 'geopolitics', label: 'Geopolitics', icon: '🌍', description: 'Global political events' },
  { value: 'technology', label: 'Technology', icon: '💻', description: 'Tech industry news' },
  { value: 'energy', label: 'Energy & Mining', icon: '⚡', description: 'Energy prices, mining difficulty' },
  { value: 'social', label: 'Social Sentiment', icon: '💬', description: 'Social media sentiment' },
  { value: 'on_chain', label: 'On-Chain Data', icon: '⛓️', description: 'Blockchain analytics' },
  { value: 'regulation', label: 'Regulatory', icon: '📜', description: 'Government regulations' },
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
};

// Default trusted sources
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
  
  // Social Sentiment
  { name: 'Crypto Twitter Trending', url: 'https://nitter.net/search?q=crypto', category: 'social', icon: '💬', reliability: 60 },
];

export const NewsSettings: React.FC = () => {
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSource, setNewSource] = useState({
    name: '', url: '', source_type: 'rss', category: 'crypto_news',
    icon: '📰', reliability_score: 70, tags: [] as string[],
  });
  const [seeding, setSeeding] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('all');

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

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const seedDefaults = async () => {
    setSeeding(true);
    try {
      // First try backend endpoint
      const response = await apiFetch('/journal/sources/seed_defaults/', { method: 'POST' });
      if (response.ok) {
        fetchSources();
        setSeeding(false);
        return;
      }
    } catch (err) {
      // Backend might not support this, use local defaults
    }
    
    // Use local defaults if backend fails
    setSources(TRUSTED_DEFAULTS.map((s, i) => ({
      id: `default-${i}`,
      name: s.name,
      url: s.url,
      source_type: 'rss',
      category: s.category,
      icon: s.icon,
      reliability_score: s.reliability,
      is_active: true,
      tags: [],
      last_fetched: null,
      fetch_count: 0,
    })));
    setSeeding(false);
  };

  const addSource = async () => {
    try {
      const response = await apiFetch('/journal/sources/', {
        method: 'POST',
        body: JSON.stringify(newSource),
      });
      if (response.ok) {
        setShowAddModal(false);
        setNewSource({ name: '', url: '', source_type: 'rss', category: 'crypto_news', icon: '📰', reliability_score: 70, tags: [] });
        fetchSources();
      }
    } catch (err) {
      console.error('Failed to add source');
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
    try {
      await apiFetch(`/journal/sources/${id}/`, { method: 'DELETE' });
      fetchSources();
    } catch (err) {
      console.error('Failed to delete source');
    }
  };

  const filteredSources = filterCategory === 'all' 
    ? sources 
    : sources.filter(s => s.category === filterCategory);

  const categoryStats = CATEGORIES.map(cat => ({
    ...cat,
    count: sources.filter(s => s.category === cat.value).length,
    active: sources.filter(s => s.category === cat.value && s.is_active).length,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">News & Data Sources</h2>
          <p className="text-gray-400 text-sm mt-1">Configure trusted sources for political, economic, and market analysis</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={seedDefaults}
            disabled={seeding}
            className="px-4 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 text-sm disabled:opacity-50"
          >
            {seeding ? 'Loading...' : 'Load Trusted Sources'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            + Add Source
          </button>
        </div>
      </div>

      {/* Category Stats */}
      <div className="grid grid-cols-5 gap-2">
        {categoryStats.map(cat => (
          <button
            key={cat.value}
            onClick={() => setFilterCategory(filterCategory === cat.value ? 'all' : cat.value)}
            className={`p-2 rounded-lg text-center transition-all ${
              filterCategory === cat.value
                ? 'bg-purple-600/30 border border-purple-500'
                : 'bg-white/5 border border-white/10 hover:bg-white/10'
            }`}
          >
            <div className="text-lg">{cat.icon}</div>
            <div className="text-xs text-gray-400 mt-1">{cat.label}</div>
            <div className="text-sm font-bold text-white">{cat.active}/{cat.count}</div>
          </button>
        ))}
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white/5 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-white">{sources.length}</div>
          <div className="text-xs text-gray-400">Total Sources</div>
        </div>
        <div className="bg-green-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{sources.filter(s => s.is_active).length}</div>
          <div className="text-xs text-gray-400">Active</div>
        </div>
        <div className="bg-blue-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">
            {sources.filter(s => s.reliability_score >= 80).length}
          </div>
          <div className="text-xs text-gray-400">High Trust (80+)</div>
        </div>
        <div className="bg-purple-500/10 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-400">{new Set(sources.map(s => s.category)).size}</div>
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
          <div className="text-4xl mb-4">📰</div>
          <p className="text-gray-400 mb-4">
            {sources.length === 0 
              ? 'No news sources configured'
              : `No sources in this category`}
          </p>
          <button
            onClick={seedDefaults}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Load Trusted Sources
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
                    {CATEGORIES.find(c => c.value === source.category)?.label || source.category}
                  </span>
                  <span className="text-xs text-gray-500">{source.source_type.toUpperCase()}</span>
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
                  className="text-gray-500 hover:text-red-400 text-sm"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Impact Weights Info */}
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

      {/* Add Source Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e1e2e] rounded-xl p-6 w-full max-w-md border border-white/20">
            <h3 className="text-lg font-bold text-white mb-4">Add News Source</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400">Name</label>
                <input
                  type="text"
                  value={newSource.name}
                  onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="Reuters"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">URL (RSS feed or website)</label>
                <input
                  type="url"
                  value={newSource.url}
                  onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="https://example.com/rss"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-gray-400">Type</label>
                  <select
                    value={newSource.source_type}
                    onChange={(e) => setNewSource({ ...newSource, source_type: e.target.value })}
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
                    value={newSource.category}
                    onChange={(e) => setNewSource({ ...newSource, category: e.target.value })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  >
                    {CATEGORIES.map(c => (
                      <option key={c.value} value={c.value} className="bg-slate-800">{c.icon} {c.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-400">Icon (emoji)</label>
                <input
                  type="text"
                  value={newSource.icon}
                  onChange={(e) => setNewSource({ ...newSource, icon: e.target.value })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm mt-1"
                  placeholder="📰"
                  maxLength={4}
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">Reliability Score: {newSource.reliability_score}/100</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={newSource.reliability_score}
                  onChange={(e) => setNewSource({ ...newSource, reliability_score: parseInt(e.target.value) })}
                  className="w-full mt-1"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Low Trust</span>
                  <span>High Trust</span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20"
              >
                Cancel
              </button>
              <button
                onClick={addSource}
                disabled={!newSource.name || !newSource.url}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                Add Source
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsSettings;

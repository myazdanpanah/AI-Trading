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
];

const CATEGORIES = [
  { value: 'crypto_news', label: 'Crypto News', icon: '📰' },
  { value: 'market_data', label: 'Market Data', icon: '📊' },
  { value: 'defi', label: 'DeFi', icon: '🏦' },
  { value: 'nft', label: 'NFT', icon: '🎨' },
  { value: 'regulation', label: 'Regulation', icon: '⚖️' },
  { value: 'macro', label: 'Macro Economics', icon: '🌍' },
  { value: 'on_chain', label: 'On-Chain Data', icon: '⛓️' },
  { value: 'social', label: 'Social Media', icon: '💬' },
];

const CATEGORY_COLORS: Record<string, string> = {
  crypto_news: 'bg-blue-500/20 text-blue-400',
  market_data: 'bg-green-500/20 text-green-400',
  defi: 'bg-purple-500/20 text-purple-400',
  nft: 'bg-pink-500/20 text-pink-400',
  regulation: 'bg-yellow-500/20 text-yellow-400',
  macro: 'bg-orange-500/20 text-orange-400',
  on_chain: 'bg-cyan-500/20 text-cyan-400',
  social: 'bg-indigo-500/20 text-indigo-400',
};

export const NewsSettings: React.FC = () => {
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSource, setNewSource] = useState({
    name: '', url: '', source_type: 'rss', category: 'crypto_news',
    icon: '📰', reliability_score: 70, tags: [] as string[],
  });
  const [seeding, setSeeding] = useState(false);

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
      const response = await apiFetch('/journal/sources/seed_defaults/', { method: 'POST' });
      if (response.ok) {
        fetchSources();
      }
    } catch (err) {
      console.error('Failed to seed defaults');
    } finally {
      setSeeding(false);
    }
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">News & Social Sources</h2>
          <p className="text-gray-400 text-sm mt-1">Configure where the AI reads news and market data</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={seedDefaults}
            disabled={seeding}
            className="px-4 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 text-sm disabled:opacity-50"
          >
            {seeding ? 'Seeding...' : 'Load Defaults'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            + Add Source
          </button>
        </div>
      </div>

      {/* Stats */}
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
          <div className="text-2xl font-bold text-blue-400">{sources.filter(s => s.source_type === 'rss').length}</div>
          <div className="text-xs text-gray-400">RSS Feeds</div>
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
      ) : sources.length === 0 ? (
        <div className="bg-white/5 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">📰</div>
          <p className="text-gray-400 mb-4">No news sources configured</p>
          <button
            onClick={seedDefaults}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Load Default Sources
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((source) => (
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
                  Reliability: <span className="text-white font-bold">{source.reliability_score}</span>/100
                </div>
                <div className="text-xs text-gray-500">
                  {source.fetch_count} fetches
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
                  placeholder="CoinDesk"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400">URL</label>
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

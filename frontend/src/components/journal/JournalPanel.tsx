import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';

interface JournalEntry {
  id: string;
  entry_type: string;
  title: string;
  content: string;
  summary: string;
  symbols_analyzed: string[];
  market_sentiment: string;
  composite_score: number;
  data_sources: string[];
  news_count: number;
  indicators_used: string[];
  ai_model: string;
  ai_confidence: number;
  key_findings: string[];
  risks_identified: string[];
  opportunities: string[];
  tags: string[];
  created_at: string;
  market_context?: {
    btc_price: number;
    fear_greed_index: number;
    fear_greed_label: string;
    btc_trend: string;
    btc_rsi: number;
    top_news_headlines: Array<{ title: string; source: string }>;
  };
}

const ENTRY_TYPES = [
  { value: 'market_analysis', label: 'Market Analysis', icon: '📊' },
  { value: 'signal_review', label: 'Signal Review', icon: '🎯' },
  { value: 'news_digest', label: 'News Digest', icon: '📰' },
  { value: 'technical_review', label: 'Technical Review', icon: '📈' },
  { value: 'daily_summary', label: 'Daily Summary', icon: '📋' },
  { value: 'lessons_learned', label: 'Lessons Learned', icon: '🧠' },
];

const SENTIMENT_COLORS: Record<string, string> = {
  very_bullish: '#10b981',
  bullish: '#34d399',
  neutral: '#f59e0b',
  bearish: '#f87171',
  very_bearish: '#ef4444',
};

export const JournalPanel: React.FC = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState('market_analysis');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/journal/entries/');
      if (response.ok) {
        const data = await response.json();
        setEntries(data.results || data);
      }
    } catch (err) {
      setError('Failed to load journal entries');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const generateEntry = async () => {
    setGenerating(true);
    setError(null);
    try {
      const response = await apiFetch('/journal/entries/generate/', {
        method: 'POST',
        body: JSON.stringify({
          entry_type: selectedType,
          symbol: selectedSymbol,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedEntry(data.entry);
        fetchEntries(); // Refresh list
      } else {
        const err = await response.json();
        setError(err.error || 'Failed to generate entry');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  const renderMarkdown = (content: string) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('# ')) return <h1 key={i} className="text-xl font-bold text-white mt-4 mb-2">{line.slice(2)}</h1>;
      if (line.startsWith('## ')) return <h2 key={i} className="text-lg font-semibold text-purple-300 mt-3 mb-1">{line.slice(3)}</h2>;
      if (line.startsWith('### ')) return <h3 key={i} className="text-md font-medium text-blue-300 mt-2">{line.slice(4)}</h3>;
      if (line.startsWith('- ') || line.startsWith('* ')) return <li key={i} className="text-gray-300 ml-4">{line.slice(2)}</li>;
      if (line.trim() === '') return <br key={i} />;
      return <p key={i} className="text-gray-300">{line}</p>;
    });
  };

  if (loading && entries.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Sidebar - Entry List */}
      <div className="w-80 border-r border-[#2a2a3e] flex flex-col">
        <div className="p-4 border-b border-[#2a2a3e]">
          <h2 className="text-lg font-bold text-white mb-3">AI Journal</h2>

          {/* Generate Controls */}
          <div className="space-y-2">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm"
            >
              {ENTRY_TYPES.map((t) => (
                <option key={t.value} value={t.value} className="bg-slate-800">
                  {t.icon} {t.label}
                </option>
              ))}
            </select>

            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm"
            >
              {['BTC', 'ETH', 'SOL', 'BNB', 'XRP'].map((s) => (
                <option key={s} value={s} className="bg-slate-800">{s}</option>
              ))}
            </select>

            <button
              onClick={generateEntry}
              disabled={generating}
              className="w-full py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 text-sm font-medium transition-all"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Generating...
                </span>
              ) : (
                'Generate Entry'
              )}
            </button>
          </div>

          {error && (
            <div className="mt-2 p-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-xs">
              {error}
            </div>
          )}
        </div>

        {/* Entry List */}
        <div className="flex-1 overflow-y-auto">
          {entries.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No journal entries yet.<br />Click "Generate Entry" to create one.
            </div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                onClick={() => setSelectedEntry(entry)}
                className={`p-3 border-b border-[#2a2a3e] cursor-pointer transition-all hover:bg-white/5 ${
                  selectedEntry?.id === entry.id ? 'bg-purple-500/10 border-l-2 border-l-purple-500' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm">
                    {ENTRY_TYPES.find((t) => t.value === entry.entry_type)?.icon || '📝'}
                  </span>
                  <span className="text-xs text-gray-400">{formatDate(entry.created_at)}</span>
                </div>
                <div className="text-sm text-white font-medium truncate">{entry.title}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: (SENTIMENT_COLORS[entry.market_sentiment] || '#666') + '20',
                      color: SENTIMENT_COLORS[entry.market_sentiment] || '#999',
                    }}
                  >
                    {entry.market_sentiment.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500">{entry.symbols_analyzed.join(', ')}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {selectedEntry ? (
          <div className="max-w-4xl">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">
                  {ENTRY_TYPES.find((t) => t.value === selectedEntry.entry_type)?.icon || '📝'}
                </span>
                <h1 className="text-2xl font-bold text-white">{selectedEntry.title}</h1>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                <span>{formatDate(selectedEntry.created_at)}</span>
                <span>Model: {selectedEntry.ai_model}</span>
                <span>Confidence: {(selectedEntry.ai_confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Market Context Bar */}
            {selectedEntry.market_context && (
              <div className="grid grid-cols-4 gap-3 mb-6">
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400">BTC Price</div>
                  <div className="text-lg font-bold text-white">
                    ${selectedEntry.market_context.btc_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400">Fear & Greed</div>
                  <div className="text-lg font-bold" style={{ color: selectedEntry.market_context.fear_greed_index > 60 ? '#10b981' : selectedEntry.market_context.fear_greed_index < 40 ? '#ef4444' : '#f59e0b' }}>
                    {selectedEntry.market_context.fear_greed_index}/100
                  </div>
                  <div className="text-xs text-gray-500">{selectedEntry.market_context.fear_greed_label}</div>
                </div>
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400">RSI</div>
                  <div className="text-lg font-bold text-white">{selectedEntry.market_context.btc_rsi}</div>
                </div>
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400">Trend</div>
                  <div className="text-lg font-bold text-white">{selectedEntry.market_context.btc_trend}</div>
                </div>
              </div>
            )}

            {/* Content */}
            <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
              <div className="prose prose-invert max-w-none">
                {renderMarkdown(selectedEntry.content)}
              </div>
            </div>

            {/* Key Findings / Risks / Opportunities */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {selectedEntry.key_findings.length > 0 && (
                <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
                  <h3 className="text-sm font-semibold text-blue-400 mb-2">Key Findings</h3>
                  <ul className="space-y-1">
                    {selectedEntry.key_findings.map((f, i) => (
                      <li key={i} className="text-xs text-gray-300">• {f}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedEntry.risks_identified.length > 0 && (
                <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/20">
                  <h3 className="text-sm font-semibold text-red-400 mb-2">Risks</h3>
                  <ul className="space-y-1">
                    {selectedEntry.risks_identified.map((r, i) => (
                      <li key={i} className="text-xs text-gray-300">• {r}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedEntry.opportunities.length > 0 && (
                <div className="bg-green-500/10 rounded-xl p-4 border border-green-500/20">
                  <h3 className="text-sm font-semibold text-green-400 mb-2">Opportunities</h3>
                  <ul className="space-y-1">
                    {selectedEntry.opportunities.map((o, i) => (
                      <li key={i} className="text-xs text-gray-300">• {o}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* News Headlines */}
            {selectedEntry.market_context?.top_news_headlines && selectedEntry.market_context.top_news_headlines.length > 0 && (
              <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Recent News</h3>
                <div className="space-y-1">
                  {selectedEntry.market_context.top_news_headlines.map((n, i) => (
                    <div key={i} className="text-xs text-gray-300">
                      <span className="text-purple-400">[{n.source}]</span> {n.title}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-4">📝</div>
              <p className="text-lg">Select a journal entry or generate a new one</p>
              <p className="text-sm mt-2">The AI will analyze market data and write an entry for you</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JournalPanel;

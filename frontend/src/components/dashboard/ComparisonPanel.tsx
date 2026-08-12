import React, { useState, useEffect, useCallback } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiFetch } from '../../utils/api';

interface SymbolData {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
  signal: string;
  confidence: number;
  technicalScore: number;
  sentimentScore: number;
  compositeScore: number;
  rsi: number;
  macd: string;
  regime: string;
  pattern: string;
  loading: boolean;
  error: string | null;
}

const QUICK_SYMBOLS = [
  { symbol: 'BTCUSDT', name: 'Bitcoin', icon: '₿' },
  { symbol: 'ETHUSDT', name: 'Ethereum', icon: 'Ξ' },
  { symbol: 'SOLUSDT', name: 'Solana', icon: '◎' },
  { symbol: 'BNBUSDT', name: 'BNB', icon: '◆' },
  { symbol: 'XRPUSDT', name: 'XRP', icon: '✕' },
  { symbol: 'ADAUSDT', name: 'Cardano', icon: '₳' },
  { symbol: 'DOGEUSDT', name: 'Dogecoin', icon: 'Ð' },
  { symbol: 'AVAXUSDT', name: 'Avalanche', icon: '▲' },
  { symbol: 'DOTUSDT', name: 'Polkadot', icon: '●' },
  { symbol: 'LINKUSDT', name: 'Chainlink', icon: '⬡' },
];

const getSignalColor = (signal: string) => {
  const s = signal?.toLowerCase() || '';
  if (s.includes('strong_buy') || s.includes('strong buy')) return 'text-green-400 bg-green-500/20';
  if (s.includes('buy')) return 'text-green-400 bg-green-500/10';
  if (s.includes('strong_sell') || s.includes('strong sell')) return 'text-red-400 bg-red-500/20';
  if (s.includes('sell')) return 'text-red-400 bg-red-500/10';
  return 'text-yellow-400 bg-yellow-500/10';
};

const getScoreColor = (score: number) => {
  if (score >= 70) return 'text-green-400';
  if (score >= 50) return 'text-yellow-400';
  if (score >= 30) return 'text-orange-400';
  return 'text-red-400';
};

export const ComparisonPanel: React.FC = () => {
  const { watchlist } = useWatchlist();
  const { t, language } = useLanguage();
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'SOLUSDT']);
  const [symbolsData, setSymbolsData] = useState<Map<string, SymbolData>>(new Map());
  const [sortBy, setSortBy] = useState<'confidence' | 'technical' | 'sentiment' | 'composite' | 'change'>('composite');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchSymbolData = useCallback(async (symbol: string) => {
    setSymbolsData(prev => {
      const next = new Map(prev);
      next.set(symbol, { ...next.get(symbol), symbol, loading: true, error: null } as SymbolData);
      return next;
    });

    try {
      // Fetch analysis
      const analysisRes = await apiFetch(`/signals/analysis/full/?symbol=${symbol}`);
      const analysis = analysisRes.ok ? await analysisRes.json() : null;

      // Fetch ticker
      const tickerRes = await apiFetch(`/market/data/ticker/?symbol=${symbol}`);
      const ticker = tickerRes.ok ? await tickerRes.json() : null;

      const price = ticker?.price || analysis?.entry_price || 0;
      const change24h = ticker?.change_24h || 0;
      const volume = ticker?.volume || 0;

      setSymbolsData(prev => {
        const next = new Map(prev);
        next.set(symbol, {
          symbol,
          price,
          change24h,
          volume,
          signal: analysis?.direction || analysis?.final_verdict || 'HOLD',
          confidence: analysis?.confidence || analysis?.composite_score || 50,
          technicalScore: analysis?.technical_score || analysis?.factors?.technical || 48,
          sentimentScore: analysis?.sentiment_score || analysis?.factors?.sentiment || 50,
          compositeScore: analysis?.composite_score || analysis?.final_score || 50,
          rsi: analysis?.rsi || analysis?.indicators?.rsi || 50,
          macd: analysis?.macd_signal || analysis?.indicators?.macd?.trend || 'neutral',
          regime: analysis?.regime || 'unknown',
          pattern: analysis?.pattern || 'none',
          loading: false,
          error: null,
        });
        return next;
      });
    } catch (err) {
      setSymbolsData(prev => {
        const next = new Map(prev);
        next.set(symbol, {
          symbol,
          price: 0,
          change24h: 0,
          volume: 0,
          signal: 'HOLD',
          confidence: 50,
          technicalScore: 48,
          sentimentScore: 50,
          compositeScore: 50,
          rsi: 50,
          macd: 'neutral',
          regime: 'unknown',
          pattern: 'none',
          loading: false,
          error: 'Failed to load',
        });
        return next;
      });
    }
  }, []);

  const fetchAll = useCallback(() => {
    selectedSymbols.forEach(s => fetchSymbolData(s));
  }, [selectedSymbols, fetchSymbolData]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAll]);

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols(prev =>
      prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol]
    );
  };

  const dataArray = Array.from(symbolsData.values()).filter(d => !d.loading || d.price > 0);

  const sortedData = [...dataArray].sort((a, b) => {
    const multiplier = sortDir === 'desc' ? -1 : 1;
    switch (sortBy) {
      case 'confidence': return (a.confidence - b.confidence) * multiplier;
      case 'technical': return (a.technicalScore - b.technicalScore) * multiplier;
      case 'sentiment': return (a.sentimentScore - b.sentimentScore) * multiplier;
      case 'composite': return (a.compositeScore - b.compositeScore) * multiplier;
      case 'change': return (a.change24h - b.change24h) * multiplier;
      default: return 0;
    }
  });

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortDir(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            {language === 'fa' ? '📊 مقایسه نمادها' : '📊 Symbol Comparison'}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {language === 'fa' ? 'مقایسه سیگنال‌ها و تحلیل‌ها برای چندین نماد' : 'Compare signals and analysis across multiple symbols'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              autoRefresh ? 'bg-green-600 text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'
            }`}
          >
            {autoRefresh ? '🟢 Live' : '⏸ Paused'}
          </button>
          <button
            onClick={fetchAll}
            className="px-3 py-1.5 bg-white/10 text-gray-400 rounded-lg hover:bg-white/20 text-sm"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Symbol Selector */}
      <div className="bg-white/5 rounded-lg p-3">
        <p className="text-xs text-gray-500 mb-2">{language === 'fa' ? 'انتخاب نمادها:' : 'Select symbols to compare:'}</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_SYMBOLS.map(item => (
            <button
              key={item.symbol}
              onClick={() => toggleSymbol(item.symbol)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                selectedSymbols.includes(item.symbol)
                  ? 'bg-purple-600 text-white border border-purple-500'
                  : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
              }`}
            >
              {item.icon} {item.name}
            </button>
          ))}
          {/* Add from watchlist */}
          {watchlist?.filter(w => !QUICK_SYMBOLS.find(q => q.symbol === w.symbol)).map(w => (
            <button
              key={w.symbol}
              onClick={() => toggleSymbol(w.symbol)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                selectedSymbols.includes(w.symbol)
                  ? 'bg-blue-600 text-white border border-blue-500'
                  : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
              }`}
            >
              ⭐ {w.symbol.replace('USDT', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 items-center">
        <span className="text-xs text-gray-500">{language === 'fa' ? 'مرتب‌سازی:' : 'Sort by:'}</span>
        {[
          { key: 'composite' as const, label: language === 'fa' ? 'ترکیبی' : 'Composite' },
          { key: 'confidence' as const, label: language === 'fa' ? 'اطمینان' : 'Confidence' },
          { key: 'technical' as const, label: language === 'fa' ? 'technical' : 'Technical' },
          { key: 'sentiment' as const, label: language === 'fa' ? 'احساسات' : 'Sentiment' },
          { key: 'change' as const, label: language === 'fa' ? 'تغییرات' : '24h Change' },
        ].map(item => (
          <button
            key={item.key}
            onClick={() => handleSort(item.key)}
            className={`px-2 py-1 rounded text-xs transition-all ${
              sortBy === item.key
                ? 'bg-purple-600/30 text-purple-400 border border-purple-500/50'
                : 'bg-white/5 text-gray-500 hover:bg-white/10'
            }`}
          >
            {item.label} {sortBy === item.key ? (sortDir === 'desc' ? '↓' : '↑') : ''}
          </button>
        ))}
      </div>

      {/* Comparison Grid */}
      {selectedSymbols.length === 0 ? (
        <div className="bg-white/5 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-gray-400">{language === 'fa' ? 'نمادی انتخاب نشده' : 'No symbols selected'}</p>
          <p className="text-gray-500 text-sm mt-1">{language === 'fa' ? 'از بالا نمادها را انتخاب کنید' : 'Select symbols from above to compare'}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'نماد' : 'Symbol'}</th>
                <th className="text-right p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'قیمت' : 'Price'}</th>
                <th className="text-right p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? '۲۴ ساعت' : '24h'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'سیگنال' : 'Signal'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'اطمینان' : 'Confidence'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'ترکیبی' : 'Composite'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'technical' : 'Technical'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'احساسات' : 'Sentiment'}</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">RSI</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">MACD</th>
                <th className="text-center p-3 text-xs text-gray-500 font-medium">{language === 'fa' ? 'رژیم' : 'Regime'}</th>
              </tr>
            </thead>
            <tbody>
              {sortedData.map(data => (
                <tr key={data.symbol} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{QUICK_SYMBOLS.find(q => q.symbol === data.symbol)?.icon || '●'}</span>
                      <div>
                        <span className="text-white font-medium">{data.symbol.replace('USDT', '')}</span>
                        <span className="text-gray-500 text-xs ml-1">/USDT</span>
                        <div className="text-xs text-gray-500">{QUICK_SYMBOLS.find(q => q.symbol === data.symbol)?.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-white font-mono">${data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </td>
                  <td className="p-3 text-right">
                    <span className={`font-medium ${data.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {data.change24h >= 0 ? '+' : ''}{data.change24h.toFixed(2)}%
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${getSignalColor(data.signal)}`}>
                      {data.signal}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            data.confidence >= 70 ? 'bg-green-500' :
                            data.confidence >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(100, data.confidence)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{data.confidence.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <span className={`text-lg font-bold ${getScoreColor(data.compositeScore)}`}>
                      {data.compositeScore.toFixed(0)}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-12 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            data.technicalScore >= 60 ? 'bg-blue-500' :
                            data.technicalScore >= 40 ? 'bg-gray-500' : 'bg-orange-500'
                          }`}
                          style={{ width: `${data.technicalScore}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{data.technicalScore.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-12 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            data.sentimentScore >= 60 ? 'bg-purple-500' :
                            data.sentimentScore >= 40 ? 'bg-gray-500' : 'bg-orange-500'
                          }`}
                          style={{ width: `${data.sentimentScore}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{data.sentimentScore.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <span className={`text-sm font-mono ${
                      data.rsi >= 70 ? 'text-red-400' :
                      data.rsi <= 30 ? 'text-green-400' : 'text-gray-400'
                    }`}>
                      {data.rsi.toFixed(0)}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      data.macd?.toLowerCase().includes('bull') ? 'bg-green-500/20 text-green-400' :
                      data.macd?.toLowerCase().includes('bear') ? 'bg-red-500/20 text-red-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {data.macd || 'neutral'}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-400">
                      {data.regime || '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Loading states */}
      {selectedSymbols.some(s => symbolsData.get(s)?.loading) && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-500 border-t-transparent" />
          <span className="ml-2 text-gray-400 text-sm">{language === 'fa' ? 'بارگذاری...' : 'Loading...'}</span>
        </div>
      )}

      {/* Summary Cards */}
      {sortedData.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="bg-green-500/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-400">
              {sortedData.filter(d => d.signal?.toLowerCase().includes('buy')).length}
            </div>
            <div className="text-xs text-gray-400">{language === 'fa' ? 'سیگنال خرید' : 'Buy Signals'}</div>
          </div>
          <div className="bg-yellow-500/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">
              {sortedData.filter(d => d.signal?.toLowerCase() === 'hold').length}
            </div>
            <div className="text-xs text-gray-400">{language === 'fa' ? 'سیگنال نگه‌داری' : 'Hold Signals'}</div>
          </div>
          <div className="bg-red-500/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-400">
              {sortedData.filter(d => d.signal?.toLowerCase().includes('sell')).length}
            </div>
            <div className="text-xs text-gray-400">{language === 'fa' ? 'سیگنال فروش' : 'Sell Signals'}</div>
          </div>
        </div>
      )}

      {/* Best Opportunities */}
      {sortedData.length > 1 && (
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">
            {language === 'fa' ? '🏆 بهترین فرصت‌ها' : '🏆 Best Opportunities'}
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {/* Best composite score */}
            {(() => {
              const best = [...sortedData].sort((a, b) => b.compositeScore - a.compositeScore)[0];
              return best ? (
                <div className="bg-white/5 rounded p-3">
                  <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'بهترین امتیاز ترکیبی' : 'Best Composite Score'}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{QUICK_SYMBOLS.find(q => q.symbol === best.symbol)?.icon || '●'}</span>
                    <span className="text-white font-medium">{best.symbol.replace('USDT', '')}</span>
                    <span className={`font-bold ${getScoreColor(best.compositeScore)}`}>{best.compositeScore.toFixed(0)}</span>
                  </div>
                </div>
              ) : null;
            })()}
            {/* Most oversold */}
            {(() => {
              const oversold = [...sortedData].sort((a, b) => a.rsi - b.rsi)[0];
              return oversold && oversold.rsi < 40 ? (
                <div className="bg-white/5 rounded p-3">
                  <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'بیش‌فروش' : 'Most Oversold (RSI)'}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{QUICK_SYMBOLS.find(q => q.symbol === oversold.symbol)?.icon || '●'}</span>
                    <span className="text-white font-medium">{oversold.symbol.replace('USDT', '')}</span>
                    <span className="text-green-400 font-bold">{oversold.rsi.toFixed(0)}</span>
                  </div>
                </div>
              ) : null;
            })()}
            {/* Best 24h performer */}
            {(() => {
              const best = [...sortedData].sort((a, b) => b.change24h - a.change24h)[0];
              return best ? (
                <div className="bg-white/5 rounded p-3">
                  <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'بهترین عملکرد ۲۴ ساعت' : 'Best 24h Performer'}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{QUICK_SYMBOLS.find(q => q.symbol === best.symbol)?.icon || '●'}</span>
                    <span className="text-white font-medium">{best.symbol.replace('USDT', '')}</span>
                    <span className="text-green-400 font-bold">+{best.change24h.toFixed(2)}%</span>
                  </div>
                </div>
              ) : null;
            })()}
            {/* Highest confidence */}
            {(() => {
              const best = [...sortedData].sort((a, b) => b.confidence - a.confidence)[0];
              return best ? (
                <div className="bg-white/5 rounded p-3">
                  <div className="text-xs text-gray-500 mb-1">{language === 'fa' ? 'بیشترین اطمینان' : 'Highest Confidence'}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{QUICK_SYMBOLS.find(q => q.symbol === best.symbol)?.icon || '●'}</span>
                    <span className="text-white font-medium">{best.symbol.replace('USDT', '')}</span>
                    <span className="text-blue-400 font-bold">{best.confidence.toFixed(0)}%</span>
                  </div>
                </div>
              ) : null;
            })()}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparisonPanel;

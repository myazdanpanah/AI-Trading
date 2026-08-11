import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface MarketPair {
  symbol: string;
  price: string;
  change_24h: string;
  volume: string;
}

interface WatchlistItem {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
  isFavorite: boolean;
}

interface WatchlistProps {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

const DEFAULT_SYMBOLS = [
  'BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'BNB-USDT', 'XRP-USDT',
  'ADA-USDT', 'DOGE-USDT', 'DOT-USDT', 'AVAX-USDT', 'LINK-USDT'
];

export const Watchlist: React.FC<WatchlistProps> = ({ onSelectSymbol, selectedSymbol }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [sortBy, setSortBy] = useState<'change' | 'volume'>('change');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMarketData = async () => {
    try {
      const response = await apiFetch('/market/pairs/?is_active=true');
      if (response.ok) {
        const data = await response.json();
        const items: WatchlistItem[] = data.results?.map((pair: any) => ({
          symbol: pair.symbol,
          price: parseFloat(pair.last_price || '0'),
          change_24h: parseFloat(pair.price_change_24h || '0'),
          volume: parseFloat(pair.volume_24h || '0'),
          isFavorite: DEFAULT_SYMBOLS.slice(0, 3).includes(pair.symbol),
        })) || [];

        if (items.length > 0) {
          setWatchlist(items);
          setLoading(false);
        } else {
          // Fallback to default symbols if no data in DB
          fetchFromExchange();
        }
      } else {
        fetchFromExchange();
      }
    } catch (error) {
      console.error('Failed to fetch market data:', error);
      fetchFromExchange();
    }
  };

  const fetchFromExchange = async () => {
    // Try to get prices from exchange API directly
    try {
      const symbols = DEFAULT_SYMBOLS.map(s => s.replace('-', '')).join(',');
      const response = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbols=[${DEFAULT_SYMBOLS.map(s => `"${s.replace('-', '')}"`).join(',')}]`);
      if (response.ok) {
        const data = await response.json();
        const items: WatchlistItem[] = data.map((ticker: any) => ({
          symbol: ticker.symbol.replace('USDT', '-USDT'),
          price: parseFloat(ticker.lastPrice || '0'),
          change_24h: parseFloat(ticker.priceChangePercent || '0'),
          volume: parseFloat(ticker.quoteVolume || '0'),
          isFavorite: DEFAULT_SYMBOLS.slice(0, 3).includes(ticker.symbol.replace('USDT', '-USDT')),
        }));
        setWatchlist(items);
      }
    } catch (error) {
      console.error('Failed to fetch from exchange:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setWatchlist(prev => prev.map(item =>
      item.symbol === symbol ? { ...item, isFavorite: !item.isFavorite } : item
    ));
  };

  const sortedList = [...watchlist]
    .sort((a, b) => {
      const multiplier = sortOrder === 'asc' ? 1 : -1;
      if (sortBy === 'change') return multiplier * (a.change_24h - b.change_24h);
      return multiplier * (a.volume - b.volume);
    });

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1000000000) return `${(vol / 1000000000).toFixed(1)}B`;
    if (vol >= 1000000) return `${(vol / 1000000).toFixed(1)}M`;
    return `${(vol / 1000).toFixed(1)}K`;
  };

  if (loading) {
    return (
      <div className="bg-[#1e1e2e] rounded-lg overflow-hidden h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  return (
    <div className="bg-[#1e1e2e] rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#2a2a3e]">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-white">Watchlist</span>
          <span className="text-xs text-gray-400">{watchlist.length} pairs</span>
        </div>

        {/* Sort buttons */}
        <div className="flex gap-1 mt-2">
          <button
            onClick={() => { setSortBy('change'); setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc'); }}
            className={`px-2 py-0.5 text-xs rounded ${sortBy === 'change' ? 'bg-blue-600 text-white' : 'bg-[#2a2a3e] text-gray-400 hover:text-white'}`}
          >
            % Change {sortBy === 'change' && (sortOrder === 'desc' ? '↓' : '↑')}
          </button>
          <button
            onClick={() => { setSortBy('volume'); setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc'); }}
            className={`px-2 py-0.5 text-xs rounded ${sortBy === 'volume' ? 'bg-blue-600 text-white' : 'bg-[#2a2a3e] text-gray-400 hover:text-white'}`}
          >
            Volume {sortBy === 'volume' && (sortOrder === 'desc' ? '↓' : '↑')}
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {sortedList.map((item) => (
          <div
            key={item.symbol}
            onClick={() => onSelectSymbol?.(item.symbol)}
            className={`px-3 py-2 cursor-pointer transition-colors border-l-2 ${selectedSymbol === item.symbol ? 'bg-[#2a2a3e] border-l-blue-500' : 'border-l-transparent hover:bg-[#2a2a3e]/50'}`}
          >
            <div className="flex items-center justify-between">
              {/* Left: Star + Symbol */}
              <div className="flex items-center gap-2 min-w-0">
                <button
                  onClick={(e) => toggleFavorite(item.symbol, e)}
                  className={`text-sm flex-shrink-0 ${item.isFavorite ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'}`}
                >
                  {item.isFavorite ? '★' : '☆'}
                </button>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {item.symbol.replace('-USDT', '')}/USDT
                  </div>
                </div>
              </div>

              {/* Right: Price + Change */}
              <div className="text-right flex-shrink-0 ml-2">
                <div className="text-sm font-mono text-white">${formatPrice(item.price)}</div>
                <div className={`text-xs font-mono ${item.change_24h >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                  {item.change_24h >= 0 ? '+' : ''}{item.change_24h.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Volume bar */}
            <div className="mt-1 flex items-center gap-2">
              <div className="flex-1 h-1 bg-[#131722] rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500/30 rounded-full"
                  style={{ width: `${Math.min((item.volume / 50000000000) * 100, 100)}%` }}
                />
              </div>
              <span className="text-[10px] text-gray-500 w-10 text-right">${formatVolume(item.volume)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Stats footer */}
      <div className="px-3 py-2 border-t border-[#2a2a3e] flex justify-between text-xs">
        <span className="text-gray-400">
          <span className="text-[#26a69a]">{watchlist.filter(i => i.change_24h > 0).length}</span> /
          <span className="text-[#ef5350]"> {watchlist.filter(i => i.change_24h < 0).length}</span>
        </span>
        <span className="text-gray-400">24h</span>
      </div>
    </div>
  );
};

export default Watchlist;

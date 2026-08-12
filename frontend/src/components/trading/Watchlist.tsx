import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';
import { WatchlistManager } from './WatchlistManager';

interface WatchlistItem {
  id?: string;
  symbol: string;
  display_name: string;
  coin_id: string;
  order: number;
  is_favorite: boolean;
}

interface WatchlistProps {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

// Default watchlist for new users
const DEFAULT_WATCHLIST: WatchlistItem[] = [
  { symbol: 'BTCUSDT', display_name: 'Bitcoin', coin_id: 'bitcoin', order: 0, is_favorite: true },
  { symbol: 'ETHUSDT', display_name: 'Ethereum', coin_id: 'ethereum', order: 1, is_favorite: true },
  { symbol: 'SOLUSDT', display_name: 'Solana', coin_id: 'solana', order: 2, is_favorite: true },
  { symbol: 'BNBUSDT', display_name: 'BNB', coin_id: 'binancecoin', order: 3, is_favorite: false },
  { symbol: 'XRPUSDT', display_name: 'XRP', coin_id: 'ripple', order: 4, is_favorite: false },
  { symbol: 'ADAUSDT', display_name: 'Cardano', coin_id: 'cardano', order: 5, is_favorite: false },
  { symbol: 'DOGEUSDT', display_name: 'Dogecoin', coin_id: 'dogecoin', order: 6, is_favorite: false },
  { symbol: 'DOTUSDT', display_name: 'Polkadot', coin_id: 'polkadot', order: 7, is_favorite: false },
  { symbol: 'AVAXUSDT', display_name: 'Avalanche', coin_id: 'avalanche-2', order: 8, is_favorite: false },
  { symbol: 'LINKUSDT', display_name: 'Chainlink', coin_id: 'chainlink', order: 9, is_favorite: false },
];

// CoinGecko price fetching
const COINGECKO_IDS: Record<string, string> = {
  'BTCUSDT': 'bitcoin', 'ETHUSDT': 'ethereum', 'SOLUSDT': 'solana',
  'BNBUSDT': 'binancecoin', 'XRPUSDT': 'ripple', 'ADAUSDT': 'cardano',
  'DOGEUSDT': 'dogecoin', 'DOTUSDT': 'polkadot', 'AVAXUSDT': 'avalanche-2',
  'LINKUSDT': 'chainlink', 'MATICUSDT': 'matic-network', 'UNIUSDT': 'uniswap',
  'ATOMUSDT': 'cosmos', 'LTCUSDT': 'litecoin', 'FILUSDT': 'filecoin',
  'NEARUSDT': 'near', 'APTUSDT': 'aptos', 'ARBUSDT': 'arbitrum',
  'OPUSDT': 'optimism', 'SUIUSDT': 'sui',
};

interface PriceData {
  [symbol: string]: { price: number; change: number; volume: number };
}

export const Watchlist: React.FC<WatchlistProps> = ({ onSelectSymbol, selectedSymbol }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [prices, setPrices] = useState<PriceData>({});
  const [loading, setLoading] = useState(true);
  const [showManager, setShowManager] = useState(false);
  const [sortBy, setSortBy] = useState<'change' | 'volume' | 'default'>('default');

  // Load watchlist from backend
  useEffect(() => {
    loadWatchlist();
  }, []);

  // Fetch prices periodically
  useEffect(() => {
    if (watchlist.length === 0) return;
    fetchPrices();
    const interval = setInterval(fetchPrices, 15000);
    return () => clearInterval(interval);
  }, [watchlist]);

  const loadWatchlist = async () => {
    try {
      const response = await apiFetch('/users/watchlist/');
      if (response.ok) {
        const data = await response.json();
        const items = data.results || data;
        if (items.length > 0) {
          setWatchlist(items);
        } else {
          // Use defaults for new users
          setWatchlist(DEFAULT_WATCHLIST);
        }
      } else {
        setWatchlist(DEFAULT_WATCHLIST);
      }
    } catch (error) {
      setWatchlist(DEFAULT_WATCHLIST);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrices = async () => {
    try {
      // Try Binance first (needs VPN in Iran)
      let binanceSuccess = false;
      try {
        const binanceSymbols = watchlist.map(w => w.symbol).filter(s => s.endsWith('USDT'));
        if (binanceSymbols.length > 0) {
          // Fetch all 24hr tickers from Binance in one call
          const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
          if (response.ok) {
            const data = await response.json();
            const newPrices: PriceData = {};
            
            data.forEach((t: any) => {
              const symbol = t.symbol;
              if (binanceSymbols.includes(symbol)) {
                newPrices[symbol] = {
                  price: parseFloat(t.lastPrice) || 0,
                  change: parseFloat(t.priceChangePercent) || 0,
                  volume: parseFloat(t.quoteVolume) || 0,
                };
              }
            });
            
            if (Object.keys(newPrices).length > 0) {
              setPrices(newPrices);
              binanceSuccess = true;
            }
          }
        }
      } catch (e) {
        // Binance blocked, fallback to CoinGecko
      }

      // Fallback to CoinGecko if Binance failed
      if (!binanceSuccess) {
        const ids = watchlist
          .map(w => w.coin_id || COINGECKO_IDS[w.symbol])
          .filter(Boolean)
          .join(',');

        if (!ids) return;

        const response = await fetch(
          `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${ids}&price_change_percentage=24h`
        );

        if (response.ok) {
          const data = await response.json();
          const newPrices: PriceData = {};
          const idToSymbol: Record<string, string> = {};
          watchlist.forEach(w => {
            const cid = w.coin_id || COINGECKO_IDS[w.symbol];
            if (cid) idToSymbol[cid] = w.symbol;
          });

          data.forEach((coin: any) => {
            const symbol = idToSymbol[coin.id];
            if (symbol) {
              newPrices[symbol] = {
                price: coin.current_price || 0,
                change: coin.price_change_percentage_24h || 0,
                volume: coin.total_volume || 0,
              };
            }
          });

          setPrices(newPrices);
        }
      }
    } catch (error) {
      console.error('Failed to fetch prices:', error);
    }
  };

  const handleWatchlistUpdate = (items: WatchlistItem[]) => {
    setWatchlist(items);
    setShowManager(false);
  };

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(1)}B`;
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(1)}M`;
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(1)}K`;
    return '0';
  };

  const sortedList = [...watchlist].sort((a, b) => {
    if (sortBy === 'change') {
      return (prices[b.symbol]?.change || 0) - (prices[a.symbol]?.change || 0);
    }
    if (sortBy === 'volume') {
      return (prices[b.symbol]?.volume || 0) - (prices[a.symbol]?.volume || 0);
    }
    return a.order - b.order;
  });

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
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{watchlist.length}</span>
            <button
              onClick={() => setShowManager(true)}
              className="text-xs text-blue-400 hover:text-blue-300"
              title="Manage Watchlist"
            >⚙️</button>
          </div>
        </div>

        {/* Sort buttons */}
        <div className="flex gap-1 mt-2">
          {[
            { key: 'default' as const, label: 'Default' },
            { key: 'change' as const, label: '% Change' },
            { key: 'volume' as const, label: 'Volume' },
          ].map(s => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key)}
              className={`px-2 py-0.5 text-xs rounded ${sortBy === s.key ? 'bg-blue-600 text-white' : 'bg-[#2a2a3e] text-gray-400 hover:text-white'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {sortedList.map((item) => {
          const p = prices[item.symbol];
          return (
            <div
              key={item.symbol}
              onClick={() => onSelectSymbol?.(item.symbol)}
              className={`px-3 py-2 cursor-pointer transition-colors border-l-2 ${
                selectedSymbol === item.symbol
                  ? 'bg-[#2a2a3e] border-l-blue-500'
                  : 'border-l-transparent hover:bg-[#2a2a3e]/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  {item.is_favorite && <span className="text-yellow-400 text-xs">★</span>}
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {item.display_name || item.symbol.replace('USDT', '')}
                    </div>
                    <div className="text-[10px] text-gray-500">{item.symbol}</div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <div className="text-sm font-mono text-white">
                    {p ? `$${formatPrice(p.price)}` : '...'}
                  </div>
                  {p && (
                    <div className={`text-xs font-mono ${p.change >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
                      {p.change >= 0 ? '+' : ''}{p.change.toFixed(2)}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-[#2a2a3e] flex items-center justify-between text-xs">
        <span className="text-gray-400">
          <span className="text-[#26a69a]">
            {Object.values(prices).filter(p => p.change > 0).length}
          </span> /{' '}
          <span className="text-[#ef5350]">
            {Object.values(prices).filter(p => p.change < 0).length}
          </span>
        </span>
        <button
          onClick={() => setShowManager(true)}
          className="text-blue-400 hover:text-blue-300"
        >+ Manage</button>
      </div>

    {/* Watchlist Manager Modal */}
    {showManager && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-4 w-96">
          <WatchlistManager
            selectedSymbol={selectedSymbol || 'BTCUSDT'}
            onSelectSymbol={(s) => { onSelectSymbol?.(s); setShowManager(false); }}
          />
          <button onClick={() => setShowManager(false)} className="mt-2 text-gray-400 text-sm">Close</button>
        </div>
      </div>
    )}
    </div>
  );
};

export default Watchlist;

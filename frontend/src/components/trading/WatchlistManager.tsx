import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useWatchlist, WatchlistItem } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface BinanceSymbol {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  status: string;
}

interface PriceData {
  [symbol: string]: {
    price: number;
    change24h: number;
    volume: number;
  };
}

interface WatchlistManagerProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

// CoinGecko ID mapping for fallback
const COINGECKO_IDS: Record<string, string> = {
  'BTCUSDT': 'bitcoin',
  'ETHUSDT': 'ethereum',
  'SOLUSDT': 'solana',
  'BNBUSDT': 'binancecoin',
  'XRPUSDT': 'ripple',
  'ADAUSDT': 'cardano',
  'DOGEUSDT': 'dogecoin',
  'DOTUSDT': 'polkadot',
  'AVAXUSDT': 'avalanche-2',
  'LINKUSDT': 'chainlink',
  'MATICUSDT': 'matic-network',
  'UNIUSDT': 'uniswap',
  'ATOMUSDT': 'cosmos',
  'LTCUSDT': 'litecoin',
  'FILUSDT': 'filecoin',
  'NEARUSDT': 'near',
  'APTUSDT': 'aptos',
  'ARBUSDT': 'arbitrum',
  'OPUSDT': 'optimism',
  'SUIUSDT': 'sui',
};

export const WatchlistManager: React.FC<WatchlistManagerProps> = ({
  selectedSymbol,
  onSelectSymbol,
}) => {
  const { watchlist, addToWatchlist, removeFromWatchlist } = useWatchlist();
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [allSymbols, setAllSymbols] = useState<BinanceSymbol[]>([]);
  const [filteredSymbols, setFilteredSymbols] = useState<BinanceSymbol[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [prices, setPrices] = useState<PriceData>({});
  const [priceSource, setPriceSource] = useState<'binance' | 'coingecko' | null>(null);

  // Fetch live prices for watchlist items
  const fetchPrices = useCallback(async () => {
    if (watchlist.length === 0) return;

    const symbols = watchlist.map(w => w.symbol);

    // Try Binance first
    try {
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      if (response.ok) {
        const data = await response.json();
        const newPrices: PriceData = {};

        data.forEach((ticker: any) => {
          if (symbols.includes(ticker.symbol)) {
            newPrices[ticker.symbol] = {
              price: parseFloat(ticker.lastPrice) || 0,
              change24h: parseFloat(ticker.priceChangePercent) || 0,
              volume: parseFloat(ticker.quoteVolume) || 0,
            };
          }
        });

        if (Object.keys(newPrices).length > 0) {
          setPrices(newPrices);
          setPriceSource('binance');
          return;
        }
      }
    } catch (e) {
      // Binance blocked, try CoinGecko
    }

    // Fallback to CoinGecko
    try {
      const coinIds = symbols
        .map(s => COINGECKO_IDS[s])
        .filter(Boolean)
        .join(',');

      if (!coinIds) return;

      const response = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${coinIds}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true`
      );

      if (response.ok) {
        const data = await response.json();
        const newPrices: PriceData = {};

        symbols.forEach(symbol => {
          const coinId = COINGECKO_IDS[symbol];
          if (coinId && data[coinId]) {
            newPrices[symbol] = {
              price: data[coinId].usd || 0,
              change24h: data[coinId].usd_24h_change || 0,
              volume: data[coinId].usd_24h_vol || 0,
            };
          }
        });

        setPrices(newPrices);
        setPriceSource('coingecko');
      }
    } catch (e) {
      console.error('Failed to fetch prices:', e);
    }
  }, [watchlist]);

  // WebSocket for live prices
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const connectWs = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/prices/');
        wsRef.current = ws;

        ws.onopen = () => {
          ws.send(JSON.stringify({ action: 'update_symbols', symbols: watchlist.map(w => w.symbol.replace('USDT', '')) }));
        };

        ws.onmessage = (event) => {
          if (cancelled) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'prices_batch' && data.prices) {
              const newPrices: PriceData = {};
              for (const p of data.prices) {
                newPrices[p.symbol + 'USDT'] = { price: p.price, change24h: p.change_24h, volume: p.volume_24h };
              }
              setPrices(prev => ({ ...prev, ...newPrices }));
              setPriceSource('coingecko');
            } else if (data.type === 'price_update') {
              setPrices(prev => ({
                ...prev,
                [data.symbol + 'USDT']: { price: data.price, change24h: data.change_24h, volume: data.volume_24h },
              }));
              setPriceSource('coingecko');
            }
          } catch {}
        };

        ws.onclose = () => {
          if (!cancelled) reconnectRef.current = setTimeout(connectWs, 3000);
        };
        ws.onerror = () => { ws.close(); };
      } catch {
        if (!cancelled) reconnectRef.current = setTimeout(connectWs, 5000);
      }
    };

    connectWs();
    return () => {
      cancelled = true;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    };
  }, [watchlist.map(w => w.symbol).join(',')]);

  useEffect(() => {
    fetchBinanceSymbols();
  }, []);

  useEffect(() => {
    if (searchQuery) {
      const query = searchQuery.toUpperCase();
      const filtered = allSymbols.filter(
        (s) =>
          s.symbol.includes(query) ||
          s.baseAsset.includes(query) ||
          s.quoteAsset.includes(query)
      );
      setFilteredSymbols(filtered.slice(0, 20));
    } else {
      setFilteredSymbols([]);
    }
  }, [searchQuery, allSymbols]);

  const fetchBinanceSymbols = async () => {
    try {
      setLoading(true);
      const response = await fetch('https://api.binance.com/api/v3/exchangeInfo');
      const data = await response.json();
      
      const usdtPairs = data.symbols
        .filter((s: any) => 
          s.quoteAsset === 'USDT' && 
          s.status === 'TRADING' &&
          s.isSpotTradingAllowed
        )
        .map((s: any) => ({
          symbol: s.symbol,
          baseAsset: s.baseAsset,
          quoteAsset: s.quoteAsset,
          status: s.status,
        }));
      
      setAllSymbols(usdtPairs);
    } catch (error) {
      console.error('Failed to fetch Binance symbols:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymbol = async (symbol: BinanceSymbol) => {
    await addToWatchlist(symbol.symbol);
    setShowSearch(false);
    setSearchQuery('');
  };

  const formatPrice = (price: number) => {
    if (!price) return '---';
    if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(6);
  };

  const formatVolume = (vol: number) => {
    if (!vol) return '';
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(1)}B`;
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(1)}M`;
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(1)}K`;
    return vol.toFixed(0);
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-300">{t('trading.watchlist')}</h3>
            {priceSource && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                priceSource === 'binance' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
              }`}>
                {priceSource === 'binance' ? '⚡' : '🦎'}
              </span>
            )}
          </div>
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            {showSearch ? t('common.cancel') : `+ ${t('trading.addSymbol')}`}
          </button>
        </div>
      </div>

      {/* Search */}
      {showSearch && (
        <div className="p-3 border-b border-gray-700">
          <input
            type="text"
            placeholder={t('trading.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            autoFocus
          />
          
          {filteredSymbols.length > 0 && (
            <div className="mt-2 max-h-48 overflow-y-auto">
              {filteredSymbols.map((symbol) => (
                <button
                  key={symbol.symbol}
                  onClick={() => handleAddSymbol(symbol)}
                  className="w-full text-left px-3 py-2 hover:bg-gray-700 rounded text-sm flex items-center justify-between"
                >
                  <span className="font-medium">{symbol.baseAsset}</span>
                  <span className="text-gray-400">{symbol.symbol}</span>
                </button>
              ))}
            </div>
          )}
          
          {loading && (
            <div className="mt-2 text-center text-gray-400 text-sm">
              {t('common.loading')}
            </div>
          )}
        </div>
      )}

      {/* Column Headers */}
      <div className="px-3 py-2 text-[10px] text-gray-500 flex justify-between border-b border-gray-700">
        <span>Symbol</span>
        <div className="flex gap-4">
          <span>Price</span>
          <span>24h%</span>
        </div>
      </div>

      {/* Watchlist */}
      <div className="flex-1 overflow-y-auto">
        {watchlist.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            {t('trading.noPositions')}
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {watchlist.map((item) => {
              const priceData = prices[item.symbol];
              const isSelected = selectedSymbol === item.symbol;
              
              return (
                <button
                  key={item.symbol}
                  onClick={() => onSelectSymbol(item.symbol)}
                  className={`w-full text-left px-3 py-2 hover:bg-gray-700 transition-colors ${
                    isSelected ? 'bg-gray-700 border-l-2 border-l-blue-500' : 'border-l-2 border-l-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">{item.symbol.replace('USDT', '')}</div>
                      <div className="text-[10px] text-gray-500">
                        {item.display_name || item.symbol}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-mono text-white">
                        {priceData ? `$${formatPrice(priceData.price)}` : '---'}
                      </div>
                      <div className="flex items-center justify-end gap-2">
                        <span
                          className={`text-xs font-mono ${
                            (priceData?.change24h || 0) >= 0
                              ? 'text-green-400'
                              : 'text-red-400'
                          }`}
                        >
                          {priceData ? (
                            <>
                              {(priceData.change24h || 0) >= 0 ? '+' : ''}
                              {priceData.change24h.toFixed(2)}%
                            </>
                          ) : (
                            '---'
                          )}
                        </span>
                      </div>
                      {priceData?.volume > 0 && (
                        <div className="text-[10px] text-gray-500">
                          Vol: ${formatVolume(priceData.volume)}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      {watchlist.length > 0 && (
        <div className="px-3 py-2 border-t border-gray-700 flex items-center justify-between text-xs">
          <span className="text-gray-500">
            {watchlist.length} symbols
          </span>
          <div className="flex gap-2">
            <span className="text-green-400">
              {Object.values(prices).filter(p => p.change24h > 0).length} ↑
            </span>
            <span className="text-red-400">
              {Object.values(prices).filter(p => p.change24h < 0).length} ↓
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

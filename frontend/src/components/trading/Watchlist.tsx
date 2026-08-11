import React, { useState, useEffect, useRef } from 'react';
import { connectPriceStream, disconnectAllStreams, getWsUrl } from '../../utils/websocket';
import { isMockDataEnabled } from '../../utils/api';

interface WatchlistItem {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
  high_24h: number;
  low_24h: number;
  isFavorite: boolean;
}

interface WatchlistProps {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

const defaultSymbols = [
  { symbol: 'BTC-USDT', name: 'Bitcoin' },
  { symbol: 'ETH-USDT', name: 'Ethereum' },
  { symbol: 'SOL-USDT', name: 'Solana' },
  { symbol: 'BNB-USDT', name: 'BNB' },
  { symbol: 'XRP-USDT', name: 'XRP' },
  { symbol: 'ADA-USDT', name: 'Cardano' },
  { symbol: 'DOGE-USDT', name: 'Dogecoin' },
  { symbol: 'DOT-USDT', name: 'Polkadot' },
  { symbol: 'AVAX-USDT', name: 'Avalanche' },
  { symbol: 'LINK-USDT', name: 'Chainlink' },
];

export const Watchlist: React.FC<WatchlistProps> = ({ onSelectSymbol, selectedSymbol }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [sortBy, setSortBy] = useState<'change' | 'volume'>('change');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const wsConnections = useRef<Map<string, WebSocket>>(new Map());

  useEffect(() => {
    // Try WebSocket first, fall back to mock data
    const useWebSocket = !isMockDataEnabled();
    
    if (useWebSocket) {
      // Connect to WebSocket for each symbol
      defaultSymbols.forEach(({ symbol }) => {
        const ws = connectPriceStream(symbol, (data) => {
          if (data.type === 'price_update') {
            setWatchlist(prev => prev.map(item => 
              item.symbol === symbol.replace('/', '-') 
                ? {
                    ...item,
                    price: data.price,
                    change_24h: data.change_24h,
                    volume: data.volume,
                  }
                : item
            ));
          }
        });
        wsConnections.current.set(symbol, ws);
      });
      
      // Initialize with default data
      generateMockWatchlist();
      
      return () => {
        disconnectAllStreams();
        wsConnections.current.clear();
      };
    } else {
      // Mock data fallback
      generateMockWatchlist();
      const interval = setInterval(generateMockWatchlist, 3000);
      return () => clearInterval(interval);
    }
  }, []);

  const generateMockWatchlist = () => {
    const items: WatchlistItem[] = defaultSymbols.map(({ symbol, name }) => {
      const basePrice = symbol === 'BTC-USDT' ? 67500 : 
                        symbol === 'ETH-USDT' ? 3450 :
                        symbol === 'SOL-USDT' ? 180 :
                        symbol === 'BNB-USDT' ? 620 :
                        symbol === 'XRP-USDT' ? 0.62 :
                        symbol === 'ADA-USDT' ? 0.45 :
                        symbol === 'DOGE-USDT' ? 0.12 :
                        symbol === 'DOT-USDT' ? 7.5 :
                        symbol === 'AVAX-USDT' ? 38 :
                        15;
      
      const change = (Math.random() - 0.45) * 10;
      const volume = (1 + Math.random() * 50) * 1000000000;
      
      return {
        symbol,
        price: basePrice + (Math.random() - 0.5) * basePrice * 0.02,
        change_24h: change,
        volume,
        high_24h: basePrice * (1 + Math.abs(change) / 100 + 0.01),
        low_24h: basePrice * (1 - Math.abs(change) / 100 - 0.01),
        isFavorite: ['BTC-USDT', 'ETH-USDT', 'SOL-USDT'].includes(symbol),
      };
    });
    
    setWatchlist(items);
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
            className={`px-2 py-0.5 text-xs rounded ${
              sortBy === 'change' ? 'bg-blue-600 text-white' : 'bg-[#2a2a3e] text-gray-400 hover:text-white'
            }`}
          >
            % Change {sortBy === 'change' && (sortOrder === 'desc' ? '↓' : '↑')}
          </button>
          <button
            onClick={() => { setSortBy('volume'); setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc'); }}
            className={`px-2 py-0.5 text-xs rounded ${
              sortBy === 'volume' ? 'bg-blue-600 text-white' : 'bg-[#2a2a3e] text-gray-400 hover:text-white'
            }`}
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
            className={`px-3 py-2 cursor-pointer transition-colors border-l-2 ${
              selectedSymbol === item.symbol 
                ? 'bg-[#2a2a3e] border-l-blue-500' 
                : 'border-l-transparent hover:bg-[#2a2a3e]/50'
            }`}
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
                <div className={`text-xs font-mono ${
                  item.change_24h >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'
                }`}>
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

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { apiFetch } from '../utils/api';

interface WatchlistItem {
  id?: string;
  symbol: string;
  display_name: string;
  coin_id: string;
  order: number;
  is_favorite: boolean;
}

interface WatchlistContextType {
  watchlist: WatchlistItem[];
  symbols: string[];           // Just the symbol strings ['BTCUSDT', 'ETHUSDT', ...]
  baseSymbols: string[];       // Base assets ['BTC', 'ETH', 'SOL', ...]
  selectedSymbol: string;      // Currently selected symbol in trading view
  setSelectedSymbol: (symbol: string) => void;
  loading: boolean;
  refreshWatchlist: () => Promise<void>;
}

const WatchlistContext = createContext<WatchlistContextType | undefined>(undefined);

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

export const WatchlistProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [loading, setLoading] = useState(true);

  // Derived values
  const symbols = watchlist.map(w => w.symbol);
  const baseSymbols = watchlist.map(w => w.symbol.replace('USDT', ''));

  const refreshWatchlist = useCallback(async () => {
    try {
      const response = await apiFetch('/users/watchlist/');
      if (response.ok) {
        const data = await response.json();
        const items = data.results || data;
        if (items.length > 0) {
          setWatchlist(items);
        } else {
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
  }, []);

  useEffect(() => {
    refreshWatchlist();
  }, [refreshWatchlist]);

  return (
    <WatchlistContext.Provider value={{
      watchlist,
      symbols,
      baseSymbols,
      selectedSymbol,
      setSelectedSymbol,
      loading,
      refreshWatchlist,
    }}>
      {children}
    </WatchlistContext.Provider>
  );
};

export const useWatchlist = (): WatchlistContextType => {
  const context = useContext(WatchlistContext);
  if (!context) {
    throw new Error('useWatchlist must be used within a WatchlistProvider');
  }
  return context;
};

export type { WatchlistItem };

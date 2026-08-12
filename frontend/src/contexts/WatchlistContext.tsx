import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { apiFetch } from '../utils/api';

export interface WatchlistItem {
  id?: string;
  symbol: string;
  display_name: string;
  coin_id: string;
  order: number;
  is_favorite: boolean;
  current_price?: number;
  price_change_percent?: number;
}

interface WatchlistContextType {
  watchlist: WatchlistItem[];
  symbols: string[];
  baseSymbols: string[];
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
  addToWatchlist: (symbol: string) => Promise<void>;
  removeFromWatchlist: (symbol: string) => Promise<void>;
  toggleFavorite: (symbol: string) => void;
  isFavorite: (symbol: string) => boolean;
  loading: boolean;
  refreshWatchlist: () => Promise<void>;
}

const WatchlistContext = createContext<WatchlistContextType | undefined>(undefined);

const FAVORITES_KEY = 'watchlist_favorites';

// All supported crypto symbols for search
export const ALL_CRYPTO_SYMBOLS: Array<{ symbol: string; name: string }> = [
  { symbol: 'BTC', name: 'Bitcoin' },
  { symbol: 'ETH', name: 'Ethereum' },
  { symbol: 'SOL', name: 'Solana' },
  { symbol: 'BNB', name: 'BNB' },
  { symbol: 'XRP', name: 'XRP' },
  { symbol: 'ADA', name: 'Cardano' },
  { symbol: 'DOGE', name: 'Dogecoin' },
  { symbol: 'DOT', name: 'Polkadot' },
  { symbol: 'AVAX', name: 'Avalanche' },
  { symbol: 'LINK', name: 'Chainlink' },
  { symbol: 'MATIC', name: 'Polygon' },
  { symbol: 'UNI', name: 'Uniswap' },
  { symbol: 'ATOM', name: 'Cosmos' },
  { symbol: 'LTC', name: 'Litecoin' },
  { symbol: 'FIL', name: 'Filecoin' },
  { symbol: 'NEAR', name: 'NEAR Protocol' },
  { symbol: 'APT', name: 'Aptos' },
  { symbol: 'ARB', name: 'Arbitrum' },
  { symbol: 'OP', name: 'Optimism' },
  { symbol: 'SUI', name: 'Sui' },
  { symbol: 'PEPE', name: 'Pepe' },
  { symbol: 'SHIB', name: 'Shiba Inu' },
  { symbol: 'FET', name: 'Fetch.ai' },
  { symbol: 'RENDER', name: 'Render' },
  { symbol: 'INJ', name: 'Injective' },
  { symbol: 'TIA', name: 'Celestia' },
  { symbol: 'SEI', name: 'Sei' },
  { symbol: 'SAND', name: 'The Sandbox' },
  { symbol: 'MANA', name: 'Decentraland' },
  { symbol: 'AAVE', name: 'Aave' },
  { symbol: 'ETC', name: 'Ethereum Classic' },
  { symbol: 'XLM', name: 'Stellar' },
  { symbol: 'VET', name: 'VeChain' },
  { symbol: 'ALGO', name: 'Algorand' },
  { symbol: 'FTM', name: 'Fantom' },
  { symbol: 'GRT', name: 'The Graph' },
  { symbol: 'IMX', name: 'Immutable' },
  { symbol: 'APE', name: 'ApeCoin' },
  { symbol: 'CRV', name: 'Curve' },
  { symbol: 'MKR', name: 'Maker' },
  { symbol: 'SNX', name: 'Synthetix' },
  { symbol: 'COMP', name: 'Compound' },
  { symbol: 'ENS', name: 'Ethereum Name Service' },
  { symbol: 'LDO', name: 'Lido DAO' },
  { symbol: 'RPL', name: 'Rocket Pool' },
  { symbol: 'DYDX', name: 'dYdX' },
  { symbol: 'GMX', name: 'GMX' },
  { symbol: 'STX', name: 'Stacks' },
  { symbol: 'RUNE', name: 'THORChain' },
  { symbol: 'KAVA', name: 'Kava' },
  { symbol: 'MANTA', name: 'Manta Network' },
  { symbol: 'JUP', name: 'Jupiter' },
  { symbol: 'WIF', name: 'dogwifhat' },
  { symbol: 'BONK', name: 'Bonk' },
  { symbol: 'FLOKI', name: 'Floki' },
  { symbol: 'CRO', name: 'Cronos' },
  { symbol: 'HBAR', name: 'Hedera' },
  { symbol: 'ICP', name: 'Internet Computer' },
  { symbol: 'IOTA', name: 'IOTA' },
  { symbol: 'EOS', name: 'EOS' },
  { symbol: 'XTZ', name: 'Tezos' },
  { symbol: 'THETA', name: 'Theta' },
  { symbol: 'AXS', name: 'Axie Infinity' },
  { symbol: 'SAND', name: 'Sandbox' },
  { symbol: 'MASK', name: 'Mask Network' },
  { symbol: '1INCH', name: '1inch' },
  { symbol: 'ENS', name: 'ENS' },
  { symbol: 'CHZ', name: 'Chiliz' },
  { symbol: 'MINA', name: 'Mina Protocol' },
  { symbol: 'FLOW', name: 'Flow' },
  { symbol: 'CFX', name: 'Conflux' },
  { symbol: 'ORDI', name: 'Ordinals' },
  { symbol: 'PYTH', name: 'Pyth Network' },
  { symbol: 'JTO', name: 'Jito' },
  { symbol: 'BOME', name: 'BOOK OF MEME' },
  { symbol: 'ETHFI', name: 'Ether.fi' },
  { symbol: 'ONDO', name: 'Ondo Finance' },
  { symbol: 'PENDLE', name: 'Pendle' },
  { symbol: 'ENA', name: 'Ethena' },
  { symbol: 'WLD', name: 'Worldcoin' },
  { symbol: 'STRK', name: 'Starknet' },
  { symbol: 'ZRO', name: 'LayerZero' },
  { symbol: 'NOT', name: 'Notcoin' },
  { symbol: 'TON', name: 'Toncoin' },
  { symbol: 'TRX', name: 'TRON' },
  { symbol: 'SHIB', name: 'Shiba Inu' },
  { symbol: 'SUI', name: 'Sui' },
  { symbol: 'SEI', name: 'Sei' },
  { symbol: 'KAS', name: 'Kaspa' },
  { symbol: 'PI', name: 'Pi Network' },
  { symbol: 'BCH', name: 'Bitcoin Cash' },
  { symbol: 'BSV', name: 'Bitcoin SV' },
  { symbol: 'XMR', name: 'Monero' },
  { symbol: 'ZEC', name: 'Zcash' },
];

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

// Load favorites from localStorage
const loadFavorites = (): Set<string> => {
  try {
    const saved = localStorage.getItem(FAVORITES_KEY);
    if (saved) return new Set(JSON.parse(saved));
  } catch {}
  return new Set(['BTC', 'ETH', 'SOL']); // defaults
};

const saveFavorites = (favorites: Set<string>) => {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favorites]));
};

export const WatchlistProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<Set<string>>(loadFavorites);

  const symbols = watchlist.map(w => w.symbol);
  const baseSymbols = watchlist.map(w => w.symbol.replace('USDT', ''));

  const refreshWatchlist = useCallback(async () => {
    try {
      const response = await apiFetch('/users/watchlist/');
      if (response.ok) {
        const data = await response.json();
        const items = data.results || data;
        if (items.length > 0) {
          // Merge localStorage favorites with API data
          const merged = items.map((item: WatchlistItem) => ({
            ...item,
            is_favorite: favorites.has(item.symbol.replace('USDT', ''))
          }));
          setWatchlist(merged);
        } else {
          // Use defaults with localStorage favorites
          const merged = DEFAULT_WATCHLIST.map(item => ({
            ...item,
            is_favorite: favorites.has(item.symbol.replace('USDT', ''))
          }));
          setWatchlist(merged);
        }
      } else {
        const merged = DEFAULT_WATCHLIST.map(item => ({
          ...item,
          is_favorite: favorites.has(item.symbol.replace('USDT', ''))
        }));
        setWatchlist(merged);
      }
    } catch (error) {
      const merged = DEFAULT_WATCHLIST.map(item => ({
        ...item,
        is_favorite: favorites.has(item.symbol.replace('USDT', ''))
      }));
      setWatchlist(merged);
    } finally {
      setLoading(false);
    }
  }, [favorites]);

  useEffect(() => {
    refreshWatchlist();
  }, [refreshWatchlist]);

  // Toggle favorite (localStorage only - no API needed)
  const toggleFavorite = useCallback((symbol: string) => {
    setFavorites(prev => {
      const next = new Set(prev);
      const base = symbol.replace('USDT', '');
      if (next.has(base)) {
        next.delete(base);
      } else {
        next.add(base);
      }
      saveFavorites(next);

      // Update watchlist in-memory immediately
      setWatchlist(wl =>
        wl.map(item => ({
          ...item,
          is_favorite: next.has(item.symbol.replace('USDT', ''))
        }))
      );

      return next;
    });
  }, []);

  const isFavorite = useCallback((symbol: string) => {
    const base = symbol.replace('USDT', '');
    return favorites.has(base);
  }, [favorites]);

  const addToWatchlist = useCallback(async (symbol: string) => {
    try {
      const response = await apiFetch('/users/watchlist/', {
        method: 'POST',
        body: JSON.stringify({ symbol }),
      });
      if (response.ok) {
        await refreshWatchlist();
      }
    } catch (error) {
      // Add locally if API fails
      const base = symbol.replace('USDT', '');
      const newItem: WatchlistItem = {
        symbol: symbol.includes('USDT') ? symbol : `${symbol}USDT`,
        display_name: base,
        coin_id: base.toLowerCase(),
        order: watchlist.length,
        is_favorite: favorites.has(base),
      };
      setWatchlist(prev => [...prev, newItem]);
    }
  }, [refreshWatchlist, watchlist.length, favorites]);

  const removeFromWatchlist = useCallback(async (symbol: string) => {
    try {
      const response = await apiFetch(`/users/watchlist/${symbol}/`, {
        method: 'DELETE',
      });
      if (response.ok) {
        await refreshWatchlist();
      }
    } catch (error) {
      setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
    }
  }, [refreshWatchlist]);

  return (
    <WatchlistContext.Provider value={{
      watchlist,
      symbols,
      baseSymbols,
      selectedSymbol,
      setSelectedSymbol,
      addToWatchlist,
      removeFromWatchlist,
      toggleFavorite,
      isFavorite,
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

export type { WatchlistContextType };

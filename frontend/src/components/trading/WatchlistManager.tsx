import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/api';

interface WatchlistItem {
  id?: string;
  symbol: string;
  display_name: string;
  coin_id: string;
  order: number;
  is_favorite: boolean;
}

interface BinanceSymbol {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  status: string;
}

interface Props {
  watchlist: WatchlistItem[];
  onUpdate: (items: WatchlistItem[]) => void;
  onClose: () => void;
}

// CoinGecko ID mapping for common coins
const COINGECKO_MAP: Record<string, string> = {
  'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'BNB': 'binancecoin',
  'XRP': 'ripple', 'ADA': 'cardano', 'DOGE': 'dogecoin', 'DOT': 'polkadot',
  'AVAX': 'avalanche-2', 'LINK': 'chainlink', 'MATIC': 'matic-network',
  'UNI': 'uniswap', 'ATOM': 'cosmos', 'LTC': 'litecoin', 'FIL': 'filecoin',
  'NEAR': 'near', 'APT': 'aptos', 'ARB': 'arbitrum', 'OP': 'optimism',
  'SUI': 'sui', 'SHIB': 'shiba-inu', 'PEPE': 'pepe', 'FLOKI': 'floki',
  'AAVE': 'aave', 'MKR': 'maker', 'CRV': 'curve-dao-token',
  'GRT': 'the-graph', 'INJ': 'injective-protocol', 'SAND': 'the-sandbox',
  'MANA': 'decentraland', 'AXS': 'axie-infinity', 'IMX': 'immutable-x',
  'FTM': 'fantom', 'ALGO': 'algorand', 'VET': 'vechain',
  'HBAR': 'hedera-hashgraph', 'ICP': 'internet-computer', 'EGLD': 'elrond-erd-2',
  'XTZ': 'tezos', 'RUNE': 'thorchain', 'ENJ': 'enjincoin',
  'CHZ': 'chiliz', 'BAT': 'basic-attention-token', 'COMP': 'compound-governance-token',
  'ZRX': '0x', 'SNX': 'havven', 'YFI': 'yearn-finance',
  '1INCH': '1inch', 'SUSHI': 'sushi', 'BAL': 'balancer',
  'KNC': 'kyber-network-crystal', 'UMA': 'uma', 'ANKR': 'ankr',
  'COTI': 'coti', 'CELO': 'celo', 'OCEAN': 'ocean-protocol',
  'NKN': 'nkn', 'IOTA': 'iota', 'THETA': 'theta-token',
  'STX': 'blockstack', 'KAVA': 'kava', 'ZIL': 'zilliqa',
  'ONE': 'harmony', 'SXP': 'swipe', 'REEF': 'reef-finance',
  'LUNA': 'terra-luna-2', 'USTC': 'terrausd', 'MIR': 'mirror-protocol',
};

// Generate display name from symbol
const symbolToName = (baseAsset: string): string => {
  const nameMap: Record<string, string> = {
    'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'SOL': 'Solana', 'BNB': 'BNB',
    'XRP': 'XRP', 'ADA': 'Cardano', 'DOGE': 'Dogecoin', 'DOT': 'Polkadot',
    'AVAX': 'Avalanche', 'LINK': 'Chainlink', 'MATIC': 'Polygon',
    'UNI': 'Uniswap', 'ATOM': 'Cosmos', 'LTC': 'Litecoin', 'FIL': 'Filecoin',
    'NEAR': 'NEAR Protocol', 'APT': 'Aptos', 'ARB': 'Arbitrum',
    'OP': 'Optimism', 'SUI': 'Sui', 'SHIB': 'Shiba Inu', 'PEPE': 'Pepe',
    'AAVE': 'Aave', 'MKR': 'Maker', 'CRV': 'Curve', 'GRT': 'The Graph',
    'INJ': 'Injective', 'SAND': 'Sandbox', 'MANA': 'Decentraland',
    'FTM': 'Fantom', 'ALGO': 'Algorand', 'VET': 'VeChain',
    'HBAR': 'Hedera', 'ICP': 'Internet Computer', 'XTZ': 'Tezos',
    'RUNE': 'THORChain', 'ENJ': 'Enjin', 'CHZ': 'Chiliz',
    'COMP': 'Compound', 'SNX': 'Synthetix', 'YFI': 'Yearn Finance',
    'ANKR': 'Ankr', 'COTI': 'COTI', 'IOTA': 'IOTA', 'THETA': 'Theta',
    'STX': 'Stacks', 'KAVA': 'Kava', 'ZIL': 'Zilliqa',
    'LUNA': 'Terra', 'BONK': 'Bonk', 'WIF': 'dogwifhat',
    'JUP': 'Jupiter', 'TIA': 'Celestia', 'SEI': 'Sei',
    'CELO': 'Celo', 'OCEAN': 'Ocean', 'NKN': 'NKN',
    'ZRX': '0x', 'BAL': 'Balancer', 'KNC': 'Kyber',
    'UMA': 'UMA', '1INCH': '1inch', 'SUSHI': 'Sushi',
  };
  return nameMap[baseAsset] || baseAsset;
};

export const WatchlistManager: React.FC<Props> = ({ watchlist, onUpdate, onClose }) => {
  const [items, setItems] = useState<WatchlistItem[]>(watchlist);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [binanceSymbols, setBinanceSymbols] = useState<BinanceSymbol[]>([]);
  const [loadingSymbols, setLoadingSymbols] = useState(true);
  const [dataSource, setDataSource] = useState<'binance' | 'static'>('static');

  // Fetch all Binance trading pairs on mount
  useEffect(() => {
    fetchBinanceSymbols();
  }, []);

  const fetchBinanceSymbols = async () => {
    setLoadingSymbols(true);
    try {
      // Try Binance API first
      const response = await fetch('https://api.binance.com/api/v3/exchangeInfo');
      if (response.ok) {
        const data = await response.json();
        const usdtPairs = data.symbols
          .filter((s: any) => s.quoteAsset === 'USDT' && s.status === 'TRADING')
          .map((s: any) => ({
            symbol: s.symbol,
            baseAsset: s.baseAsset,
            quoteAsset: s.quoteAsset,
            status: s.status,
          }));
        setBinanceSymbols(usdtPairs);
        setDataSource('binance');
      } else {
        throw new Error('Binance not available');
      }
    } catch (e) {
      // Fallback: use a comprehensive static list
      console.warn('Binance API not available, using static list');
      setDataSource('static');
      setBinanceSymbols(generateStaticSymbols());
    } finally {
      setLoadingSymbols(false);
    }
  };

  const generateStaticSymbols = (): BinanceSymbol[] => {
    const bases = [
      'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LINK',
      'MATIC', 'UNI', 'ATOM', 'LTC', 'FIL', 'NEAR', 'APT', 'ARB', 'OP', 'SUI',
      'SHIB', 'PEPE', 'FLOKI', 'AAVE', 'MKR', 'CRV', 'GRT', 'INJ', 'SAND', 'MANA',
      'FTM', 'ALGO', 'VET', 'HBAR', 'ICP', 'EGLD', 'XTZ', 'RUNE', 'ENJ', 'CHZ',
      'BAT', 'COMP', 'ZRX', 'SNX', 'YFI', '1INCH', 'SUSHI', 'BAL', 'KNC', 'UMA',
      'ANKR', 'COTI', 'CELO', 'OCEAN', 'NKN', 'IOTA', 'THETA', 'STX', 'KAVA', 'ZIL',
      'ONE', 'SXP', 'REEF', 'LUNA', 'BONK', 'WIF', 'JUP', 'TIA', 'SEI', 'IMX',
      'AXS', 'GALA', 'MASK', 'LDO', 'RPL', 'GMX', 'PENDLE', 'WLD', 'PYTH', 'ONDO',
      'JTO', 'STRK', 'MANTA', 'ALT', 'DYM', 'PORTAL', 'ETHFI', 'ENA', 'TNSR', 'SAGA',
    ];
    return bases.map(b => ({
      symbol: `${b}USDT`,
      baseAsset: b,
      quoteAsset: 'USDT',
      status: 'TRADING',
    }));
  };

  const isInWatchlist = (symbol: string) => items.some(i => i.symbol === symbol);

  const addSymbol = (symbol: string, baseAsset: string) => {
    if (isInWatchlist(symbol)) return;
    setItems(prev => [...prev, {
      symbol,
      display_name: symbolToName(baseAsset),
      coin_id: COINGECKO_MAP[baseAsset] || baseAsset.toLowerCase(),
      order: prev.length,
      is_favorite: false,
    }]);
  };

  const removeSymbol = (symbol: string) => {
    setItems(prev => prev.filter(i => i.symbol !== symbol));
  };

  const toggleFavorite = (symbol: string) => {
    setItems(prev => prev.map(i =>
      i.symbol === symbol ? { ...i, is_favorite: !i.is_favorite } : i
    ));
  };

  const moveUp = (index: number) => {
    if (index === 0) return;
    setItems(prev => {
      const newItems = [...prev];
      [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
      return newItems.map((item, i) => ({ ...item, order: i }));
    });
  };

  const moveDown = (index: number) => {
    setItems(prev => {
      if (index >= prev.length - 1) return prev;
      const newItems = [...prev];
      [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
      return newItems.map((item, i) => ({ ...item, order: i }));
    });
  };

  const saveWatchlist = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const response = await apiFetch('/users/watchlist/sync/', {
        method: 'POST',
        body: JSON.stringify({ items }),
      });
      if (response.ok) {
        const data = await response.json();
        onUpdate(data);
        setMessage('Watchlist saved!');
        setTimeout(() => onClose(), 1000);
      } else {
        setMessage('Failed to save watchlist');
      }
    } catch (error) {
      setMessage('Network error');
    } finally {
      setSaving(false);
    }
  };

  const filteredAvailable = binanceSymbols.filter(s =>
    !isInWatchlist(s.symbol) &&
    (s.baseAsset.toLowerCase().includes(search.toLowerCase()) ||
     s.symbol.toLowerCase().includes(search.toLowerCase()))
  ).slice(0, 50); // Limit to 50 results for performance

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1e1e2e] rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-[#2a2a3e] shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a3e] flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Manage Watchlist</h2>
            <p className="text-xs text-gray-500 mt-1">
              {dataSource === 'binance' ? '⚡ Live Binance symbols' : '📋 Static list'} • {binanceSymbols.length} USDT pairs
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        </div>

        <div className="flex-1 overflow-hidden flex">
          {/* Current watchlist */}
          <div className="flex-1 p-4 overflow-y-auto border-r border-[#2a2a3e]">
            <h3 className="text-sm font-medium text-gray-400 mb-3">
              Your Watchlist ({items.length} symbols)
            </h3>
            {items.length === 0 ? (
              <p className="text-sm text-gray-500">No symbols in watchlist. Add from the right panel.</p>
            ) : (
              <div className="space-y-1">
                {items.map((item, index) => (
                  <div key={item.symbol} className="flex items-center gap-2 p-2 bg-[#131722] rounded-lg">
                    <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                    <button
                      onClick={() => toggleFavorite(item.symbol)}
                      className={`text-sm ${item.is_favorite ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'}`}
                    >
                      {item.is_favorite ? '★' : '☆'}
                    </button>
                    <div className="flex-1">
                      <div className="text-sm text-white">{item.display_name}</div>
                      <div className="text-xs text-gray-500">{item.symbol}</div>
                    </div>
                    <div className="flex gap-1">
                      <button onClick={() => moveUp(index)} className="text-xs text-gray-500 hover:text-white px-1">↑</button>
                      <button onClick={() => moveDown(index)} className="text-xs text-gray-500 hover:text-white px-1">↓</button>
                    </div>
                    <button
                      onClick={() => removeSymbol(item.symbol)}
                      className="text-red-400 hover:text-red-300 text-sm px-1"
                    >×</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available symbols */}
          <div className="w-72 p-4 overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-400 mb-3">
              {dataSource === 'binance' ? 'Search Binance Pairs' : 'Add Symbol'}
            </h3>
            <input
              type="text"
              placeholder={dataSource === 'binance' ? 'Search by name or symbol (e.g., BTC, PEPE, ARB)...' : 'Search...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 bg-[#131722] border border-[#2a2a3e] rounded-lg text-white text-sm mb-3 focus:outline-none focus:border-blue-500"
              autoFocus
            />
            {loadingSymbols ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                <span className="ml-2 text-sm text-gray-400">Loading symbols...</span>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredAvailable.length === 0 ? (
                  <p className="text-sm text-gray-500 py-4 text-center">
                    {search ? `No results for "${search}"` : 'Type to search...'}
                  </p>
                ) : (
                  filteredAvailable.map((s) => (
                    <button
                      key={s.symbol}
                      onClick={() => addSymbol(s.symbol, s.baseAsset)}
                      className="w-full flex items-center justify-between p-2 bg-[#131722] rounded-lg hover:bg-[#2a2a3e] text-left transition-colors"
                    >
                      <div>
                        <div className="text-sm text-white">{symbolToName(s.baseAsset)}</div>
                        <div className="text-xs text-gray-500">{s.symbol}</div>
                      </div>
                      <span className="text-blue-400 text-lg">+</span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#2a2a3e] flex items-center justify-between">
          {message && (
            <span className={`text-sm ${message.includes('saved') ? 'text-green-400' : 'text-red-400'}`}>
              {message}
            </span>
          )}
          <div className="flex gap-2 ml-auto">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg"
            >Cancel</button>
            <button
              onClick={saveWatchlist}
              disabled={saving}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Watchlist'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchlistManager;

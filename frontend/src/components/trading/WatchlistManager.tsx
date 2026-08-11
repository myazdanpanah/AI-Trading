import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface WatchlistItem {
  id?: string;
  symbol: string;
  display_name: string;
  coin_id: string;
  order: number;
  is_favorite: boolean;
}

interface Props {
  watchlist: WatchlistItem[];
  onUpdate: (items: WatchlistItem[]) => void;
  onClose: () => void;
}

// Available symbols to add
const AVAILABLE_SYMBOLS = [
  { symbol: 'BTCUSDT', display_name: 'Bitcoin', coin_id: 'bitcoin' },
  { symbol: 'ETHUSDT', display_name: 'Ethereum', coin_id: 'ethereum' },
  { symbol: 'SOLUSDT', display_name: 'Solana', coin_id: 'solana' },
  { symbol: 'BNBUSDT', display_name: 'BNB', coin_id: 'binancecoin' },
  { symbol: 'XRPUSDT', display_name: 'XRP', coin_id: 'ripple' },
  { symbol: 'ADAUSDT', display_name: 'Cardano', coin_id: 'cardano' },
  { symbol: 'DOGEUSDT', display_name: 'Dogecoin', coin_id: 'dogecoin' },
  { symbol: 'DOTUSDT', display_name: 'Polkadot', coin_id: 'polkadot' },
  { symbol: 'AVAXUSDT', display_name: 'Avalanche', coin_id: 'avalanche-2' },
  { symbol: 'LINKUSDT', display_name: 'Chainlink', coin_id: 'chainlink' },
  { symbol: 'MATICUSDT', display_name: 'Polygon', coin_id: 'matic-network' },
  { symbol: 'UNIUSDT', display_name: 'Uniswap', coin_id: 'uniswap' },
  { symbol: 'ATOMUSDT', display_name: 'Cosmos', coin_id: 'cosmos' },
  { symbol: 'LTCUSDT', display_name: 'Litecoin', coin_id: 'litecoin' },
  { symbol: 'FILUSDT', display_name: 'Filecoin', coin_id: 'filecoin' },
  { symbol: 'NEARUSDT', display_name: 'NEAR', coin_id: 'near' },
  { symbol: 'APTUSDT', display_name: 'Aptos', coin_id: 'aptos' },
  { symbol: 'ARBUSDT', display_name: 'Arbitrum', coin_id: 'arbitrum' },
  { symbol: 'OPUSDT', display_name: 'Optimism', coin_id: 'optimism' },
  { symbol: 'SUIUSDT', display_name: 'Sui', coin_id: 'sui' },
];

export const WatchlistManager: React.FC<Props> = ({ watchlist, onUpdate, onClose }) => {
  const [items, setItems] = useState<WatchlistItem[]>(watchlist);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const isInWatchlist = (symbol: string) => items.some(i => i.symbol === symbol);

  const addSymbol = (symbol: string) => {
    const found = AVAILABLE_SYMBOLS.find(s => s.symbol === symbol);
    if (found && !isInWatchlist(symbol)) {
      setItems(prev => [...prev, {
        symbol: found.symbol,
        display_name: found.display_name,
        coin_id: found.coin_id,
        order: prev.length,
        is_favorite: false,
      }]);
    }
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

  const filteredAvailable = AVAILABLE_SYMBOLS.filter(s =>
    !isInWatchlist(s.symbol) &&
    (s.display_name.toLowerCase().includes(search.toLowerCase()) ||
     s.symbol.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1e1e2e] rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-[#2a2a3e] shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a3e] flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Manage Watchlist</h2>
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
          <div className="w-64 p-4 overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Add Symbol</h3>
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 bg-[#131722] border border-[#2a2a3e] rounded-lg text-white text-sm mb-3 focus:outline-none focus:border-blue-500"
            />
            <div className="space-y-1">
              {filteredAvailable.map((s) => (
                <button
                  key={s.symbol}
                  onClick={() => addSymbol(s.symbol)}
                  className="w-full flex items-center justify-between p-2 bg-[#131722] rounded-lg hover:bg-[#2a2a3e] text-left transition-colors"
                >
                  <div>
                    <div className="text-sm text-white">{s.display_name}</div>
                    <div className="text-xs text-gray-500">{s.symbol}</div>
                  </div>
                  <span className="text-blue-400 text-lg">+</span>
                </button>
              ))}
            </div>
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

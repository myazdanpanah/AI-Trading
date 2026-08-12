import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface BinanceSymbol {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  status: string;
}

interface WatchlistManagerProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

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

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300">{t('trading.watchlist')}</h3>
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

      {/* Watchlist */}
      <div className="flex-1 overflow-y-auto">
        {watchlist.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            {t('trading.noPositions')}
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {watchlist.map((item) => (
              <button
                key={item.symbol}
                onClick={() => onSelectSymbol(item.symbol)}
                className={`w-full text-left px-3 py-3 hover:bg-gray-700 transition-colors ${
                  selectedSymbol === item.symbol ? 'bg-gray-700' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{item.symbol.replace('USDT', '')}</div>
                    <div className="text-xs text-gray-400">{item.symbol}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-mono">
                      ${item.current_price?.toLocaleString() || '---'}
                    </div>
                    <div
                      className={`text-xs ${
                        (item.price_change_percent || 0) >= 0
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {(item.price_change_percent || 0) >= 0 ? '+' : ''}
                      {(item.price_change_percent || 0).toFixed(2)}%
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

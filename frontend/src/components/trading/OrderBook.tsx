import React, { useState, useEffect, useRef } from 'react';

interface Props {
  symbol?: string;
}

interface OrderLevel {
  price: number;
  qty: number;
  total: number;
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
};

export const OrderBook: React.FC<Props> = ({ symbol = 'BTCUSDT' }) => {
  const [bids, setBids] = useState<OrderLevel[]>([]);
  const [asks, setAsks] = useState<OrderLevel[]>([]);
  const [lastPrice, setLastPrice] = useState(0);
  const [prevPrice, setPrevPrice] = useState(0);
  const [source, setSource] = useState<'binance' | 'coingecko' | null>(null);
  const [spread, setSpread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    connectWebSocket(symbol);
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [symbol]);

  const connectWebSocket = (sym: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const stream = `${sym.toLowerCase()}@depth20@100ms`;
      const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${stream}`);

      ws.onopen = () => {
        setSource('binance');
        setLoading(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.bids && data.asks) {
            let cumBid = 0;
            let cumAsk = 0;

            const bidLevels: OrderLevel[] = data.bids.slice(0, 12).map(([price, qty]: [string, string]) => {
              cumBid += parseFloat(qty);
              return { price: parseFloat(price), qty: parseFloat(qty), total: cumBid };
            });

            const askLevels: OrderLevel[] = data.asks.slice(0, 12).map(([price, qty]: [string, string]) => {
              cumAsk += parseFloat(qty);
              return { price: parseFloat(price), qty: parseFloat(qty), total: cumAsk };
            });

            setBids(bidLevels);
            setAsks(askLevels);

            if (bidLevels.length > 0 && askLevels.length > 0) {
              setPrevPrice(lastPrice);
              setLastPrice(bidLevels[0].price);
              setSpread(askLevels[0].price - bidLevels[0].price);
            }
          }
        } catch (e) {}
      };

      ws.onerror = () => fetchOrderBookRest(sym);
      ws.onclose = () => fetchOrderBookRest(sym);
      wsRef.current = ws;
      
      // Timeout fallback - if WS doesn't connect in 3 seconds, try REST
      setTimeout(() => {
        if (bids.length === 0 && asks.length === 0) {
          fetchOrderBookRest(sym);
        }
      }, 3000);
    } catch (e) {
      fetchOrderBookRest(sym);
    }
  };

  const fetchOrderBookRest = async (sym: string) => {
    try {
      const response = await fetch(`https://api.binance.com/api/v3/depth?symbol=${sym}&limit=12`);
      if (response.ok) {
        const data = await response.json();
        setSource('binance');
        setLoading(false);

        let cumBid = 0;
        const bidLevels: OrderLevel[] = data.bids.map(([price, qty]: [string, string]) => {
          cumBid += parseFloat(qty);
          return { price: parseFloat(price), qty: parseFloat(qty), total: cumBid };
        });

        let cumAsk = 0;
        const askLevels: OrderLevel[] = data.asks.map(([price, qty]: [string, string]) => {
          cumAsk += parseFloat(qty);
          return { price: parseFloat(price), qty: parseFloat(qty), total: cumAsk };
        });

        setBids(bidLevels);
        setAsks(askLevels);

        if (bidLevels.length > 0 && askLevels.length > 0) {
          setLastPrice(bidLevels[0].price);
          setSpread(askLevels[0].price - bidLevels[0].price);
        }
      }
    } catch (e) {
      // Binance failed, try CoinGecko for basic price data
      fetchCoinGeckoPrice(sym);
    }
  };

  const fetchCoinGeckoPrice = async (sym: string) => {
    try {
      const coinId = COINGECKO_IDS[sym];
      if (!coinId) {
        setLoading(false);
        setError('Data unavailable');
        return;
      }

      const response = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${coinId}&vs_currencies=usd&include_24hr_vol=true`
      );
      
      if (response.ok) {
        const data = await response.json();
        const coinData = data[coinId];
        
        if (coinData) {
          setSource('coingecko');
          setLoading(false);
          
          const price = coinData.usd;
          setLastPrice(price);
          
          // Generate simulated order book from price
          const spread = price * 0.001; // 0.1% spread
          const newBids: OrderLevel[] = [];
          const newAsks: OrderLevel[] = [];
          
          for (let i = 0; i < 12; i++) {
            const bidPrice = price - spread * (i + 1);
            const askPrice = price + spread * (i + 1);
            const qty = Math.random() * 10 + 0.1;
            
            newBids.push({
              price: bidPrice,
              qty,
              total: newBids.reduce((sum, b) => sum + b.qty, 0) + qty,
            });
            
            newAsks.push({
              price: askPrice,
              qty,
              total: newAsks.reduce((sum, a) => sum + a.qty, 0) + qty,
            });
          }
          
          setBids(newBids);
          setAsks(newAsks);
          setSpread(spread * 2);
        }
      }
    } catch (e) {
      setLoading(false);
      setError('Unable to load data');
    }
  };

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(6);
  };

  const formatQty = (qty: number) => {
    if (qty >= 1) return qty.toFixed(4);
    return qty.toFixed(6);
  };

  const maxTotal = Math.max(
    ...bids.map(b => b.total),
    ...asks.map(a => a.total),
    1
  );

  const priceChange = lastPrice > prevPrice ? 'up' : lastPrice < prevPrice ? 'down' : 'same';

  if (loading) {
    return (
      <div className="bg-[#131722] h-full flex flex-col rounded-lg border border-gray-700">
        <div className="px-3 py-2 border-b border-gray-700">
          <span className="text-sm font-medium text-white">{symbol.replace('USDT', '')}/USDT</span>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent mx-auto mb-2"></div>
            <p className="text-gray-500 text-xs">Loading order book...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#131722] h-full flex flex-col rounded-lg border border-gray-700">
        <div className="px-3 py-2 border-b border-gray-700">
          <span className="text-sm font-medium text-white">{symbol.replace('USDT', '')}/USDT</span>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-3xl mb-2">📉</div>
            <p className="text-gray-500 text-xs">{error}</p>
            <button
              onClick={() => {
                setLoading(true);
                setError(null);
                connectWebSocket(symbol);
              }}
              className="mt-2 text-xs text-blue-400 hover:text-blue-300"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#131722] h-full flex flex-col rounded-lg border border-gray-700">
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{symbol.replace('USDT', '')}</span>
          <span className="text-xs text-gray-500">/USDT</span>
        </div>
        {source && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
            source === 'binance' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
          }`}>
            {source === 'binance' ? '⚡ Binance' : '🦎 CoinGecko'}
          </span>
        )}
      </div>

      {/* Column Headers */}
      <div className="px-3 py-1.5 text-[10px] text-gray-500 flex justify-between border-b border-gray-700">
        <span>Price (USDT)</span>
        <span>Size</span>
        <span>Total</span>
      </div>

      {/* Asks (reversed - highest at top) */}
      <div className="flex-1 overflow-hidden flex flex-col justify-end">
        {[...asks].reverse().map((level, i) => (
          <div
            key={`ask-${i}`}
            className="relative px-3 py-[3px] flex justify-between text-xs font-mono hover:bg-gray-700/30"
          >
            <div
              className="absolute inset-y-0 right-0 bg-red-500/10"
              style={{ width: `${(level.total / maxTotal) * 100}%` }}
            />
            <span className="text-red-400 relative z-10">{formatPrice(level.price)}</span>
            <span className="text-gray-300 relative z-10">{formatQty(level.qty)}</span>
            <span className="text-gray-500 relative z-10">{formatQty(level.total)}</span>
          </div>
        ))}
      </div>

      {/* Price + Spread */}
      <div className="px-3 py-2 border-y border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <span className={`text-lg font-bold font-mono ${
            priceChange === 'up' ? 'text-green-400' : priceChange === 'down' ? 'text-red-400' : 'text-white'
          }`}>
            ${formatPrice(lastPrice)}
          </span>
          <span className="text-[10px] text-gray-500">
            Spread: ${spread.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Bids */}
      <div className="flex-1 overflow-hidden">
        {bids.map((level, i) => (
          <div
            key={`bid-${i}`}
            className="relative px-3 py-[3px] flex justify-between text-xs font-mono hover:bg-gray-700/30"
          >
            <div
              className="absolute inset-y-0 right-0 bg-green-500/10"
              style={{ width: `${(level.total / maxTotal) * 100}%` }}
            />
            <span className="text-green-400 relative z-10">{formatPrice(level.price)}</span>
            <span className="text-gray-300 relative z-10">{formatQty(level.qty)}</span>
            <span className="text-gray-500 relative z-10">{formatQty(level.total)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrderBook;

import React, { useState, useEffect, useRef } from 'react';

interface Props {
  symbol?: string;
}

interface OrderLevel {
  price: number;
  qty: number;
  total: number;
}

export const OrderBook: React.FC<Props> = ({ symbol = 'BTCUSDT' }) => {
  const [bids, setBids] = useState<OrderLevel[]>([]);
  const [asks, setAsks] = useState<OrderLevel[]>([]);
  const [lastPrice, setLastPrice] = useState(0);
  const [prevPrice, setPrevPrice] = useState(0);
  const [source, setSource] = useState<'binance' | 'coingecko' | null>(null);
  const [spread, setSpread] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!symbol) return;
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
      setSource(null);
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

  return (
    <div className="bg-[#131722] h-full flex flex-col">
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#2a2a3e] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{symbol.replace('USDT', '')}</span>
          <span className="text-xs text-gray-500">/USDT</span>
        </div>
        {source && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
            source === 'binance' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
          }`}>
            {source === 'binance' ? '⚡' : '🦎'}
          </span>
        )}
      </div>

      {/* Column Headers */}
      <div className="px-3 py-1.5 text-[10px] text-gray-500 flex justify-between border-b border-[#2a2a3e]">
        <span>Price (USDT)</span>
        <span>Size</span>
        <span>Total</span>
      </div>

      {/* Asks (reversed - highest at top) */}
      <div className="flex-1 overflow-hidden flex flex-col justify-end">
        {[...asks].reverse().map((level, i) => (
          <div
            key={`ask-${i}`}
            className="relative px-3 py-[3px] flex justify-between text-xs font-mono hover:bg-[#2a2a3e]/30"
          >
            <div
              className="absolute inset-y-0 right-0 bg-[#ef5350]/8"
              style={{ width: `${(level.total / maxTotal) * 100}%` }}
            />
            <span className="text-[#ef5350] relative z-10">{formatPrice(level.price)}</span>
            <span className="text-gray-300 relative z-10">{formatQty(level.qty)}</span>
            <span className="text-gray-500 relative z-10">{formatQty(level.total)}</span>
          </div>
        ))}
      </div>

      {/* Price + Spread */}
      <div className="px-3 py-2 border-y border-[#2a2a3e] bg-[#1e1e2e]">
        <div className="flex items-center justify-between">
          <span className={`text-lg font-bold font-mono ${
            priceChange === 'up' ? 'text-[#26a69a]' : priceChange === 'down' ? 'text-[#ef5350]' : 'text-white'
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
            className="relative px-3 py-[3px] flex justify-between text-xs font-mono hover:bg-[#2a2a3e]/30"
          >
            <div
              className="absolute inset-y-0 right-0 bg-[#26a69a]/8"
              style={{ width: `${(level.total / maxTotal) * 100}%` }}
            />
            <span className="text-[#26a69a] relative z-10">{formatPrice(level.price)}</span>
            <span className="text-gray-300 relative z-10">{formatQty(level.qty)}</span>
            <span className="text-gray-500 relative z-10">{formatQty(level.total)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrderBook;

import { useEffect, useRef, useState, useCallback } from 'react';

interface PriceData {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  market_cap?: number;
}

interface UseLivePricesReturn {
  prices: Record<string, PriceData>;
  isConnected: boolean;
  lastUpdate: Date | null;
}

export function useLivePrices(symbols: string[] = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']): UseLivePricesReturn {
  const [prices, setPrices] = useState<Record<string, PriceData>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket('ws://localhost:8000/ws/prices/');
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // Send current symbols
        ws.send(JSON.stringify({ action: 'update_symbols', symbols }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'prices_batch' && data.prices) {
            setPrices(prev => {
              const next = { ...prev };
              for (const p of data.prices) {
                next[p.symbol] = p;
              }
              return next;
            });
            setLastUpdate(new Date());
          } else if (data.type === 'price_update') {
            setPrices(prev => ({
              ...prev,
              [data.symbol]: {
                symbol: data.symbol,
                price: data.price,
                change_24h: data.change_24h,
                volume_24h: data.volume_24h,
                market_cap: data.market_cap,
              },
            }));
            setLastUpdate(new Date());
          }
        } catch {
          // Ignore parse errors
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Auto-reconnect after 3s
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch {
      setIsConnected(false);
      reconnectTimeoutRef.current = setTimeout(connect, 5000);
    }
  }, [symbols.join(',')]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { prices, isConnected, lastUpdate };
}

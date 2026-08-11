import React, { useState, useEffect, useRef } from 'react';
import { connectOrderBookStream, disconnectStream, getWsUrl } from '../../utils/websocket';
import { isMockDataEnabled } from '../../utils/api';

interface OrderBookEntry {
  price: number;
  amount: number;
  total: number;
  side: 'bid' | 'ask';
}

interface OrderBookProps {
  symbol?: string;
}

export const OrderBook: React.FC<OrderBookProps> = ({ symbol = 'BTC-USDT' }) => {
  const [orders, setOrders] = useState<OrderBookEntry[]>([]);
  const [spread, setSpread] = useState(0);
  const [lastPrice, setLastPrice] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Try WebSocket first, fall back to mock data
    const useWebSocket = !isMockDataEnabled();
    
    if (useWebSocket) {
      const wsSymbol = symbol.replace('-', '/');
      const url = getWsUrl(`/ws/orderbook/${wsSymbol}/`);
      
      wsRef.current = connectOrderBookStream(symbol, (data) => {
        if (data.type === 'orderbook_update') {
          const askOrders: OrderBookEntry[] = data.asks.map((ask: any) => ({
            ...ask,
            side: 'ask' as const,
          }));
          const bidOrders: OrderBookEntry[] = data.bids.map((bid: any) => ({
            ...bid,
            side: 'bid' as const,
          }));
          
          setOrders([...askOrders.reverse(), ...bidOrders]);
          setSpread(data.spread);
          setLastPrice(data.last_price);
        }
      });
      
      return () => {
        if (wsRef.current) {
          disconnectStream(url);
        }
      };
    } else {
      // Mock data fallback
      generateMockOrderBook();
      const interval = setInterval(generateMockOrderBook, 1500);
      return () => clearInterval(interval);
    }
  }, [symbol]);

  const generateMockOrderBook = () => {
    const basePrice = 67500 + (Math.random() - 0.5) * 500;
    const asks: OrderBookEntry[] = [];
    const bids: OrderBookEntry[] = [];
    
    let totalAmount = 0;
    for (let i = 0; i < 10; i++) {
      const price = basePrice + (i + 1) * (3 + Math.random() * 8);
      const amount = 0.01 + Math.random() * 0.5;
      totalAmount += amount;
      asks.push({
        price: Math.round(price * 100) / 100,
        amount: Math.round(amount * 10000) / 10000,
        total: Math.round(totalAmount * 10000) / 10000,
        side: 'ask',
      });
    }
    
    totalAmount = 0;
    for (let i = 0; i < 10; i++) {
      const price = basePrice - (i + 1) * (3 + Math.random() * 8);
      const amount = 0.01 + Math.random() * 0.5;
      totalAmount += amount;
      bids.push({
        price: Math.round(price * 100) / 100,
        amount: Math.round(amount * 10000) / 10000,
        total: Math.round(totalAmount * 10000) / 10000,
        side: 'bid',
      });
    }
    
    setOrders([...asks.reverse(), ...bids]);
    setSpread(asks[asks.length - 1].price - bids[0].price);
    setLastPrice(basePrice);
  };

  const maxTotal = Math.max(...orders.map(o => o.total));

  return (
    <div className="bg-[#131722] h-full flex flex-col">
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#2a2a3e] flex items-center justify-between">
        <span className="text-sm font-medium text-white">Order Book</span>
        <span className="text-xs text-gray-500">{symbol.replace('-USDT', '/USDT')}</span>
      </div>
      
      {/* Column headers */}
      <div className="grid grid-cols-3 gap-1 px-3 py-1 text-[10px] text-gray-500 border-b border-[#2a2a3e]">
        <span>Price (USDT)</span>
        <span className="text-right">Amount</span>
        <span className="text-right">Total</span>
      </div>
      
      {/* Asks */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full flex flex-col justify-end">
          {orders.filter(o => o.side === 'ask').map((order, i) => (
            <div 
              key={`ask-${i}`}
              className="relative grid grid-cols-3 gap-1 px-3 py-[3px] hover:bg-[#1e1e2e] cursor-pointer"
            >
              <div 
                className="absolute inset-y-0 right-0 bg-[#ef5350]/10"
                style={{ width: `${(order.total / maxTotal) * 100}%` }}
              />
              <span className="relative text-[#ef5350] text-xs font-mono">{order.price.toLocaleString()}</span>
              <span className="relative text-right text-gray-300 text-xs font-mono">{order.amount.toFixed(4)}</span>
              <span className="relative text-right text-gray-500 text-xs font-mono">{order.total.toFixed(4)}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Last price */}
      <div className="px-3 py-2 border-y border-[#2a2a3e]">
        <div className="flex items-center justify-between">
          <span className={`text-lg font-mono font-semibold ${lastPrice >= 67500 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
            ${lastPrice.toLocaleString()}
          </span>
          <span className="text-[10px] text-gray-500">
            Spread: ${spread.toFixed(2)}
          </span>
        </div>
      </div>
      
      {/* Bids */}
      <div className="flex-1 overflow-hidden">
        <div>
          {orders.filter(o => o.side === 'bid').map((order, i) => (
            <div 
              key={`bid-${i}`}
              className="relative grid grid-cols-3 gap-1 px-3 py-[3px] hover:bg-[#1e1e2e] cursor-pointer"
            >
              <div 
                className="absolute inset-y-0 right-0 bg-[#26a69a]/10"
                style={{ width: `${(order.total / maxTotal) * 100}%` }}
              />
              <span className="relative text-[#26a69a] text-xs font-mono">{order.price.toLocaleString()}</span>
              <span className="relative text-right text-gray-300 text-xs font-mono">{order.amount.toFixed(4)}</span>
              <span className="relative text-right text-gray-500 text-xs font-mono">{order.total.toFixed(4)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrderBook;

import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrderBook();
    const interval = setInterval(fetchOrderBook, 3000);
    return () => clearInterval(interval);
  }, [symbol]);

  const fetchOrderBook = async () => {
    try {
      const apiSymbol = symbol.replace('-', '');
      const response = await apiFetch(`/market/orderbook/latest/?symbol=${apiSymbol}`);
      if (response.ok) {
        const data = await response.json();

        // Parse orderbook from backend
        const bidDepth = data.bid_depth || [];
        const askDepth = data.ask_depth || [];

        const asks: OrderBookEntry[] = askDepth.map((ask: any) => ({
          price: parseFloat(ask.price || '0'),
          amount: parseFloat(ask.amount || '0'),
          total: parseFloat(ask.total || '0'),
          side: 'ask' as const,
        }));

        const bids: OrderBookEntry[] = bidDepth.map((bid: any) => ({
          price: parseFloat(bid.price || '0'),
          amount: parseFloat(bid.amount || '0'),
          total: parseFloat(bid.total || '0'),
          side: 'bid' as const,
        }));

        if (asks.length > 0 && bids.length > 0) {
          setOrders([...asks.reverse(), ...bids]);
          setSpread(data.spread || 0);
          setLastPrice(asks[asks.length - 1]?.price || bids[0]?.price || 0);
          setLoading(false);
        } else {
          fetchFromExchange();
        }
      } else {
        fetchFromExchange();
      }
    } catch (error) {
      console.error('Failed to fetch orderbook:', error);
      fetchFromExchange();
    }
  };

  const fetchFromExchange = async () => {
    try {
      const apiSymbol = symbol.replace('-', '').toLowerCase();
      const response = await fetch(`https://api.binance.com/api/v3/depth?symbol=${apiSymbol.toUpperCase()}&limit=10`);
      if (response.ok) {
        const data = await response.json();

        let totalAmount = 0;
        const asks: OrderBookEntry[] = (data.asks || []).map((ask: any) => {
          totalAmount += parseFloat(ask[1]);
          return {
            price: parseFloat(ask[0]),
            amount: parseFloat(ask[1]),
            total: totalAmount,
            side: 'ask' as const,
          };
        });

        totalAmount = 0;
        const bids: OrderBookEntry[] = (data.bids || []).map((bid: any) => {
          totalAmount += parseFloat(bid[1]);
          return {
            price: parseFloat(bid[0]),
            amount: parseFloat(bid[1]),
            total: totalAmount,
            side: 'bid' as const,
          };
        });

        setOrders([...asks.reverse(), ...bids]);
        if (asks.length > 0 && bids.length > 0) {
          setSpread(asks[asks.length - 1].price - bids[0].price);
          setLastPrice((asks[asks.length - 1].price + bids[0].price) / 2);
        }
      }
    } catch (error) {
      console.error('Failed to fetch from exchange:', error);
    } finally {
      setLoading(false);
    }
  };

  const maxTotal = Math.max(...orders.map(o => o.total), 1);

  if (loading) {
    return (
      <div className="bg-[#131722] h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
      </div>
    );
  }

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

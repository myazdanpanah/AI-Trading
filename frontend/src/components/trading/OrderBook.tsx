import React, { useEffect, useRef } from 'react';

interface Props {
  symbol?: string;
}

const SYMBOL_MAP: Record<string, string> = {
  'BTCUSDT': 'BINANCE:BTCUSDT',
  'ETHUSDT': 'BINANCE:ETHUSDT',
  'SOLUSDT': 'BINANCE:SOLUSDT',
  'BNBUSDT': 'BINANCE:BNBUSDT',
  'XRPUSDT': 'BINANCE:XRPUSDT',
  'ADAUSDT': 'BINANCE:ADAUSDT',
  'DOGEUSDT': 'BINANCE:DOGEUSDT',
  'DOTUSDT': 'BINANCE:DOTUSDT',
  'AVAXUSDT': 'BINANCE:AVAXUSDT',
  'LINKUSDT': 'BINANCE:LINKUSDT',
};

let widgetId = 0;

export const OrderBook: React.FC<Props> = ({ symbol = 'BTCUSDT' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const idRef = useRef(`tv-mini-${++widgetId}`);

  useEffect(() => {
    if (!containerRef.current) return;

    const timer = setTimeout(() => {
      if (typeof (window as any).TradingView === 'undefined') return;
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '';

      const tvSymbol = SYMBOL_MAP[symbol] || `BINANCE:${symbol}`;

      new (window as any).TradingView.MiniChart({
        container_id: idRef.current,
        autosize: true,
        symbol: tvSymbol,
        interval: 'D',
        timezone: 'Etc/UTC',
        theme: 'dark',
        locale: 'en',
        color: '#26a69a',
        colorGrowing: '#26a69a',
        colorFalling: '#ef5350',
        colorVolume: 'rgba(38,166,154,0.3)',
        hideTopToolbar: true,
        hideLegend: true,
        scalePosition: 'right',
        scaleFontSize: 10,
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [symbol]);

  return (
    <div className="bg-[#131722] h-full flex flex-col">
      <div className="px-3 py-2 border-b border-[#2a2a3e]">
        <span className="text-sm font-medium text-white">{symbol.replace('USDT', '/USDT')}</span>
      </div>
      <div className="flex-1 min-h-0">
        <div id={idRef.current} ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default OrderBook;

import React, { useEffect, useRef } from 'react';

interface Props {
  symbol?: string;
  interval?: string;
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

const TIMEFRAMES = [
  { label: '1m', value: '1' },
  { label: '5m', value: '5' },
  { label: '15m', value: '15' },
  { label: '1h', value: '60' },
  { label: '4h', value: '240' },
  { label: '1D', value: 'D' },
  { label: '1W', value: 'W' },
];

let widgetId = 0;

export const TradingViewChart: React.FC<Props> = ({ symbol = 'BTCUSDT', interval = '60' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const idRef = useRef(`tv-chart-${++widgetId}`);

  useEffect(() => {
    if (!containerRef.current) return;

    const timer = setTimeout(() => {
      if (typeof (window as any).TradingView === 'undefined') return;
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '';

      const tvSymbol = SYMBOL_MAP[symbol] || `BINANCE:${symbol}`;

      new (window as any).TradingView.widget({
        container_id: idRef.current,
        autosize: true,
        symbol: tvSymbol,
        interval,
        timezone: 'Etc/UTC',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#1e1e2e',
        enable_publishing: false,
        allow_symbol_change: false,
        hide_side_toolbar: false,
        save_image: false,
        studies: [],
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [symbol, interval]);

  return (
    <div className="bg-[#131722] h-full flex flex-col">
      <div className="flex-1 min-h-0">
        <div id={idRef.current} ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default TradingViewChart;

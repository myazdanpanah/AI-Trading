import React, { useEffect, useRef, useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

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
  const widgetRef = useRef<any>(null);
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInterval, setSelectedInterval] = useState(interval);

  useEffect(() => {
    if (!containerRef.current) return;

    setLoading(true);
    setError(null);

    const timer = setTimeout(() => {
      // Check if TradingView library is loaded
      if (typeof (window as any).TradingView === 'undefined') {
        setError('TradingView library not loaded. Please refresh the page.');
        setLoading(false);
        return;
      }

      if (!containerRef.current) return;

      try {
        // Clear previous widget
        containerRef.current.innerHTML = '';

        const tvSymbol = SYMBOL_MAP[symbol] || `BINANCE:${symbol}`;

        widgetRef.current = new (window as any).TradingView.widget({
          container_id: idRef.current,
          autosize: true,
          symbol: tvSymbol,
          interval: selectedInterval,
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
          debug: false,
        });

        setLoading(false);
      } catch (err) {
        console.error('TradingView widget error:', err);
        setError('Failed to load chart');
        setLoading(false);
      }
    }, 500);

    return () => {
      clearTimeout(timer);
      if (widgetRef.current) {
        try {
          widgetRef.current.remove?.();
        } catch (e) {}
      }
    };
  }, [symbol, selectedInterval]);

  const handleIntervalChange = (newInterval: string) => {
    setSelectedInterval(newInterval);
  };

  return (
    <div className="bg-[#131722] h-full flex flex-col rounded-lg border border-gray-700 overflow-hidden">
      {/* Header with timeframe selector */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">
            {symbol.replace('USDT', '')}/USDT
          </span>
          <span className="text-xs text-gray-500">TradingView</span>
        </div>
        <div className="flex gap-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.value}
              onClick={() => handleIntervalChange(tf.value)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                selectedInterval === tf.value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart container */}
      <div className="flex-1 min-h-0 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#131722]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
              <p className="text-gray-400 text-sm">Loading chart...</p>
            </div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#131722]">
            <div className="text-center">
              <div className="text-4xl mb-4">📊</div>
              <p className="text-red-400 text-sm mb-2">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Refresh Page
              </button>
            </div>
          </div>
        )}
        
        <div id={idRef.current} ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default TradingViewChart;

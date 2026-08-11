import React, { useEffect, useRef } from 'react';

interface Props {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

let widgetId = 0;

export const Watchlist: React.FC<Props> = ({ onSelectSymbol, selectedSymbol }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const idRef = useRef(`tv-watchlist-${++widgetId}`);

  useEffect(() => {
    if (!containerRef.current) return;

    const timer = setTimeout(() => {
      if (typeof (window as any).TradingView === 'undefined') return;
      if (!containerRef.current) return;

      containerRef.current.innerHTML = '';

      new (window as any).TradingView.MarketOverview({
        container_id: idRef.current,
        colorTheme: 'dark',
        autosize: true,
        width: '100%',
        height: '100%',
        symbols: [
          { proName: 'BINANCE:BTCUSDT', title: 'Bitcoin' },
          { proName: 'BINANCE:ETHUSDT', title: 'Ethereum' },
          { proName: 'BINANCE:SOLUSDT', title: 'Solana' },
          { proName: 'BINANCE:BNBUSDT', title: 'BNB' },
          { proName: 'BINANCE:XRPUSDT', title: 'XRP' },
          { proName: 'BINANCE:ADAUSDT', title: 'Cardano' },
          { proName: 'BINANCE:DOGEUSDT', title: 'Dogecoin' },
          { proName: 'BINANCE:DOTUSDT', title: 'Polkadot' },
          { proName: 'BINANCE:AVAXUSDT', title: 'Avalanche' },
          { proName: 'BINANCE:LINKUSDT', title: 'Chainlink' },
        ],
        showSymbolLogo: true,
        isTransparent: false,
        locale: 'en',
      });
    }, 300);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="bg-[#1e1e2e] h-full flex flex-col">
      <div className="px-3 py-2 border-b border-[#2a2a3e]">
        <span className="text-sm font-semibold text-white">Watchlist</span>
      </div>
      <div className="flex-1 min-h-0">
        <div id={idRef.current} ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default Watchlist;

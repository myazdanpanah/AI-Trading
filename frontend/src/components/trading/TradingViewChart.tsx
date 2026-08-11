import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CrosshairMode, IChartApi, ISeriesApi, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { CandlestickData, HistogramData, Time } from 'lightweight-charts';

interface TradingViewChartProps {
  symbol?: string;
}

const TIMEFRAMES: { label: string; binanceInterval: string }[] = [
  { label: '1m', binanceInterval: '1m' },
  { label: '5m', binanceInterval: '5m' },
  { label: '15m', binanceInterval: '15m' },
  { label: '1h', binanceInterval: '1h' },
  { label: '4h', binanceInterval: '4h' },
  { label: '1D', binanceInterval: '1d' },
  { label: '1W', binanceInterval: '1w' },
];

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ symbol: propSymbol = 'BTCUSDT' }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [activeTimeframe, setActiveTimeframe] = useState('1h');
  const [currentPrice, setCurrentPrice] = useState(0);
  const [priceChange, setPriceChange] = useState(0);
  const [priceChangePercent, setPriceChangePercent] = useState('0.00');
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#d1d4dc',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#1e1e2e' },
        horzLines: { color: '#1e1e2e' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#758696', width: 1, style: 2, labelBackgroundColor: '#2a2a3e' },
        horzLine: { color: '#758696', width: 1, style: 2, labelBackgroundColor: '#2a2a3e' },
      },
      rightPriceScale: {
        borderColor: '#2a2a3e',
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: '#2a2a3e',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { vertTouchDrag: false },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickRef.current = candlestickSeries;
    volumeRef.current = volumeSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Fetch candle data from Binance
  const fetchCandles = async (symbol: string, interval: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=500`
      );
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();

      const candles: CandlestickData<Time>[] = data.map((k: any[]) => ({
        time: (Math.floor(k[0] / 1000)) as Time,
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4]),
      }));

      const volumes: HistogramData<Time>[] = data.map((k: any[]) => ({
        time: (Math.floor(k[0] / 1000)) as Time,
        value: parseFloat(k[5]),
        color: parseFloat(k[4]) >= parseFloat(k[1]) ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)',
      }));

      if (candlestickRef.current) {
        candlestickRef.current.setData(candles);
      }
      if (volumeRef.current) {
        volumeRef.current.setData(volumes);
      }

      if (candles.length > 0) {
        const last = candles[candles.length - 1];
        const prev = candles.length > 1 ? candles[candles.length - 2] : last;
        setCurrentPrice(last.close);
        setPriceChange(last.close - prev.close);
        setPriceChangePercent(((last.close - prev.close) / prev.close * 100).toFixed(2));
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch candles:', error);
      setLoading(false);
    }
  };

  // WebSocket for live price updates
  useEffect(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsSymbol = propSymbol.toLowerCase();
    const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${wsSymbol}@kline_${activeTimeframe}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const k = data.k;

      if (k && candlestickRef.current) {
        const candle: CandlestickData<Time> = {
          time: (Math.floor(k.t / 1000)) as Time,
          open: parseFloat(k.o),
          high: parseFloat(k.h),
          low: parseFloat(k.l),
          close: parseFloat(k.c),
        };
        candlestickRef.current.update(candle);

        if (volumeRef.current) {
          volumeRef.current.update({
            time: (Math.floor(k.t / 1000)) as Time,
            value: parseFloat(k.v),
            color: k.c >= k.o ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)',
          });
        }

        setCurrentPrice(k.c);
        const change = k.c - k.o;
        setPriceChange(change);
        setPriceChangePercent((change / k.o * 100).toFixed(2));
      }
    };

    ws.onerror = (error) => console.error('WebSocket error:', error);
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [propSymbol, activeTimeframe]);

  // Fetch candles when symbol or timeframe changes
  useEffect(() => {
    fetchCandles(propSymbol, activeTimeframe);
  }, [propSymbol, activeTimeframe]);

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  return (
    <div className="bg-[#131722] rounded-lg overflow-hidden h-full flex flex-col">
      {/* Top toolbar */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-3 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-white font-semibold">{propSymbol.replace('USDT', '/USDT')}</span>
            <span className="text-lg font-mono text-white">${formatPrice(currentPrice)}</span>
            <span className={`text-sm font-mono ${priceChange >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChange >= 0 ? '+' : ''}{priceChangePercent}%)
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <span className="text-[#26a69a]">●</span>
            <span className="text-gray-400">Live</span>
          </div>
        </div>
      </div>

      {/* Timeframe bar */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-3 py-1">
        <div className="flex items-center gap-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.binanceInterval}
              onClick={() => setActiveTimeframe(tf.binanceInterval)}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                activeTimeframe === tf.binanceInterval
                  ? 'bg-[#2a2a3e] text-white'
                  : 'text-gray-500 hover:text-white hover:bg-[#2a2a3e]/50'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/80 z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default TradingViewChart;

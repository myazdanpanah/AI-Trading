import React, { useState, useMemo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradingViewChartProps {
  data: CandleData[];
}

const TIMEFRAMES = ['1', '5', '15', '30', '60', '240', 'D', 'W'];

const INDICATORS = [
  { id: 'sma20', label: 'SMA(20)', color: '#2196F3' },
  { id: 'sma50', label: 'SMA(50)', color: '#FF9800' },
  { id: 'ema12', label: 'EMA(12)', color: '#4CAF50' },
  { id: 'ema26', label: 'EMA(26)', color: '#E91E63' },
  { id: 'bb', label: 'BB(20,2)', color: '#9C27B0' },
];

const calculateSMA = (data: CandleData[], period: number) => {
  return data.map((_, index) => {
    if (index < period - 1) return null;
    const sum = data.slice(index - period + 1, index + 1).reduce((a, b) => a + b.close, 0);
    return sum / period;
  });
};

const calculateEMA = (data: CandleData[], period: number) => {
  const multiplier = 2 / (period + 1);
  let ema = data[0].close;
  return data.map((d, i) => {
    if (i === 0) return d.close;
    ema = (d.close - ema) * multiplier + ema;
    return ema;
  });
};

const calculateBollinger = (data: CandleData[], period: number = 20, stdDev: number = 2) => {
  const sma = calculateSMA(data, period);
  return data.map((d, i) => {
    if (i < period - 1) return null;
    const slice = data.slice(i - period + 1, i + 1);
    const mean = sma[i]!;
    const variance = slice.reduce((sum, item) => sum + Math.pow(item.close - mean, 2), 0) / period;
    const std = Math.sqrt(variance);
    return { upper: mean + std * stdDev, middle: mean, lower: mean - std * stdDev };
  });
};

// Custom candle shape for TradingView look
const CandleShape = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;
  
  const { open, close, high, low } = payload;
  const isGreen = close >= open;
  const bodyColor = isGreen ? '#26a69a' : '#ef5350';
  const wickColor = isGreen ? '#26a69a' : '#ef5350';
  
  const centerX = x + width / 2;
  const bodyTop = Math.min(y, y + height);
  const bodyHeight = Math.max(Math.abs(height), 1);
  
  // Scale wicks proportionally
  const priceRange = high - low || 1;
  const bodyRange = Math.abs(close - open) || 1;
  const wickScale = bodyHeight / bodyRange;
  
  const wickTop = bodyTop - (high - Math.max(open, close)) * wickScale;
  const wickBottom = bodyTop + bodyHeight + (Math.min(open, close) - low) * wickScale;
  
  return (
    <g>
      <line x1={centerX} y1={wickTop} x2={centerX} y2={bodyTop} stroke={wickColor} strokeWidth={1} />
      <rect
        x={x + 1}
        y={bodyTop}
        width={Math.max(width - 2, 2)}
        height={bodyHeight}
        fill={isGreen ? bodyColor : bodyColor}
        stroke={bodyColor}
        strokeWidth={0.5}
      />
      <line x1={centerX} y1={bodyTop + bodyHeight} x2={centerX} y2={wickBottom} stroke={wickColor} strokeWidth={1} />
    </g>
  );
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;
  
  const isGreen = data.close >= data.open;
  const change = ((data.close - data.open) / data.open * 100).toFixed(2);
  
  return (
    <div className="bg-[#1e1e2e] border border-[#2a2a3e] rounded p-3 shadow-xl text-xs font-mono">
      <div className="flex items-center gap-4 mb-2 text-gray-400">
        <span>{data.date}</span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">O</span>
          <span className="text-white">${data.open.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">H</span>
          <span className="text-[#26a69a]">${data.high.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">L</span>
          <span className="text-[#ef5350]">${data.low.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">C</span>
          <span className="text-white">${data.close.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4 pt-1 border-t border-[#2a2a3e]">
          <span className="text-gray-400">Chg</span>
          <span className={isGreen ? 'text-[#26a69a]' : 'text-[#ef5350]'}>
            {isGreen ? '+' : ''}{change}%
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Vol</span>
          <span className="text-white">{(data.volume / 1000000).toFixed(2)}M</span>
        </div>
      </div>
    </div>
  );
};

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ data }) => {
  const [activeTimeframe, setActiveTimeframe] = useState('D');
  const [activeIndicators, setActiveIndicators] = useState<string[]>(['sma20']);
  const [showVolume, setShowVolume] = useState(true);
  
  const chartData = useMemo(() => {
    const sma20 = calculateSMA(data, 20);
    const sma50 = calculateSMA(data, 50);
    const ema12 = calculateEMA(data, 12);
    const ema26 = calculateEMA(data, 26);
    const bollinger = calculateBollinger(data);
    
    return data.map((d, i) => ({
      ...d,
      sma20: activeIndicators.includes('sma20') ? sma20[i] : null,
      sma50: activeIndicators.includes('sma50') ? sma50[i] : null,
      ema12: activeIndicators.includes('ema12') ? ema12[i] : null,
      ema26: activeIndicators.includes('ema26') ? ema26[i] : null,
      bbUpper: activeIndicators.includes('bb') && bollinger[i] ? bollinger[i]!.upper : null,
      bbLower: activeIndicators.includes('bb') && bollinger[i] ? bollinger[i]!.lower : null,
    }));
  }, [data, activeIndicators]);
  
  const currentPrice = data.length > 0 ? data[data.length - 1].close : 0;
  const prevPrice = data.length > 1 ? data[data.length - 2].close : currentPrice;
  const priceChange = currentPrice - prevPrice;
  const priceChangePercent = ((priceChange / prevPrice) * 100).toFixed(2);
  
  const toggleIndicator = (id: string) => {
    setActiveIndicators(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="bg-[#131722] rounded-lg overflow-hidden h-full flex flex-col">
      {/* Top toolbar - TradingView style */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-3 py-2">
        <div className="flex items-center justify-between">
          {/* Left: Symbol */}
          <div className="flex items-center gap-3">
            <span className="text-white font-semibold">BTC/USDT</span>
            <span className="text-lg font-mono text-white">${currentPrice.toLocaleString()}</span>
            <span className={`text-sm font-mono ${priceChange >= 0 ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChange >= 0 ? '+' : ''}{priceChangePercent}%)
            </span>
          </div>
          
          {/* Right: Indicators */}
          <div className="flex items-center gap-2">
            {INDICATORS.map(ind => (
              <button
                key={ind.id}
                onClick={() => toggleIndicator(ind.id)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  activeIndicators.includes(ind.id) 
                    ? 'text-white' 
                    : 'text-gray-500 hover:text-gray-300'
                }`}
                style={{ 
                  backgroundColor: activeIndicators.includes(ind.id) ? ind.color + '30' : 'transparent',
                  color: activeIndicators.includes(ind.id) ? ind.color : undefined
                }}
              >
                {ind.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Timeframe bar */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-3 py-1">
        <div className="flex items-center gap-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf}
              onClick={() => setActiveTimeframe(tf)}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                activeTimeframe === tf 
                  ? 'bg-[#2a2a3e] text-white' 
                  : 'text-gray-500 hover:text-white hover:bg-[#2a2a3e]/50'
              }`}
            >
              {tf}
            </button>
          ))}
          <div className="w-px h-4 bg-[#2a2a3e] mx-2" />
          <button
            onClick={() => setShowVolume(!showVolume)}
            className={`px-2 py-1 text-xs rounded ${
              showVolume ? 'text-blue-400' : 'text-gray-500'
            }`}
          >
            Vol
          </button>
        </div>
      </div>
      
      {/* Main chart area */}
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 60, bottom: showVolume ? 0 : 10, left: 10 }}>
            <CartesianGrid stroke="#1e1e2e" strokeDasharray="0" />
            <XAxis 
              dataKey="date" 
              stroke="#2a2a3e"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              height={20}
            />
            <YAxis 
              domain={['auto', 'auto']}
              stroke="#2a2a3e"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              orientation="right"
              width={70}
              tickFormatter={(v) => `$${v.toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Indicators */}
            {activeIndicators.includes('sma20') && (
              <Line type="monotone" dataKey="sma20" stroke="#2196F3" dot={false} strokeWidth={1} />
            )}
            {activeIndicators.includes('sma50') && (
              <Line type="monotone" dataKey="sma50" stroke="#FF9800" dot={false} strokeWidth={1} />
            )}
            {activeIndicators.includes('ema12') && (
              <Line type="monotone" dataKey="ema12" stroke="#4CAF50" dot={false} strokeWidth={1} />
            )}
            {activeIndicators.includes('ema26') && (
              <Line type="monotone" dataKey="ema26" stroke="#E91E63" dot={false} strokeWidth={1} />
            )}
            {activeIndicators.includes('bb') && (
              <>
                <Line type="monotone" dataKey="bbUpper" stroke="#9C27B0" dot={false} strokeWidth={1} strokeDasharray="3 3" />
                <Line type="monotone" dataKey="bbLower" stroke="#9C27B0" dot={false} strokeWidth={1} strokeDasharray="3 3" />
              </>
            )}
            
            {/* Candles */}
            <Bar dataKey="high" shape={<CandleShape />} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {/* Volume area */}
      {showVolume && (
        <div className="h-20 border-t border-[#2a2a3e]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 60, bottom: 5, left: 10 }}>
              <XAxis dataKey="date" stroke="#2a2a3e" tick={false} axisLine={false} />
              <YAxis stroke="#2a2a3e" tick={{ fill: '#6b7280', fontSize: 9 }} tickLine={false} axisLine={false} orientation="right" width={70} tickFormatter={(v) => `${(v/1000000).toFixed(0)}M`} />
              <Bar dataKey="volume" isAnimationActive={false}>
                {chartData.map((entry, index) => (
                  <rect
                    key={`vol-${index}`}
                    fill={entry.close >= entry.open ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)'}
                  />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default TradingViewChart;

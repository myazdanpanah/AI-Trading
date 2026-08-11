import React, { useState, useMemo } from 'react';
import {
  ComposedChart,
  Bar,
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

interface CandlestickChartProps {
  data: CandleData[];
  height?: number;
}

// Custom candle shape
const CandleShape = (props: any) => {
  const { x, y, width, height, payload } = props;
  const { open, close, high, low } = payload;
  
  const isGreen = close >= open;
  const color = isGreen ? '#10b981' : '#ef4444';
  const bodyColor = isGreen ? '#10b981' : '#ef4444';
  
  // Calculate positions
  const centerX = x + width / 2;
  const bodyTop = Math.min(y, y + height);
  const bodyHeight = Math.abs(height);
  
  // Wick positions (scaled)
  const priceRange = high - low;
  const wickScale = priceRange > 0 ? bodyHeight / priceRange : 1;
  
  const wickTop = bodyTop - (high - Math.max(open, close)) * wickScale;
  const wickBottom = bodyTop + bodyHeight + (Math.min(open, close) - low) * wickScale;
  
  return (
    <g>
      {/* Upper wick */}
      <line
        x1={centerX}
        y1={wickTop}
        x2={centerX}
        y2={bodyTop}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body */}
      <rect
        x={x + 2}
        y={bodyTop}
        width={width - 4}
        height={Math.max(bodyHeight, 1)}
        fill={bodyColor}
        stroke={color}
        strokeWidth={1}
        rx={1}
      />
      {/* Lower wick */}
      <line
        x1={centerX}
        y1={bodyTop + bodyHeight}
        x2={centerX}
        y2={wickBottom}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload;
    if (!data) return null;
    
    const isGreen = data.close >= data.open;
    const change = ((data.close - data.open) / data.open * 100).toFixed(2);
    
    return (
      <div className="bg-slate-800/95 backdrop-blur-lg p-4 rounded-lg border border-white/20 shadow-xl min-w-[200px]">
        <p className="text-white font-semibold mb-2">{data.date}</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-purple-200/60">Open:</span>
            <span className="text-white font-mono">${data.open.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-purple-200/60">High:</span>
            <span className="text-green-400 font-mono">${data.high.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-purple-200/60">Low:</span>
            <span className="text-red-400 font-mono">${data.low.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-purple-200/60">Close:</span>
            <span className="text-white font-mono">${data.close.toLocaleString()}</span>
          </div>
          <div className="flex justify-between pt-1 border-t border-white/10">
            <span className="text-purple-200/60">Change:</span>
            <span className={`font-mono ${isGreen ? 'text-green-400' : 'text-red-400'}`}>
              {isGreen ? '+' : ''}{change}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-purple-200/60">Volume:</span>
            <span className="text-white font-mono">{(data.volume / 1000000).toFixed(2)}M</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const CandlestickChart: React.FC<CandlestickChartProps> = ({ data, height = 400 }) => {
  const [timeframe, setTimeframe] = useState<'1D' | '1W' | '1M'>('1D');
  
  // Transform data for the chart
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      // For Recharts, we need open-close range as a bar
      openClose: [d.open, d.close],
      // Body size for the bar height
      bodySize: Math.abs(d.close - d.open),
    }));
  }, [data]);
  
  // Calculate price range for Y axis
  const priceRange = useMemo(() => {
    if (data.length === 0) return { min: 0, max: 100 };
    const allPrices = data.flatMap(d => [d.high, d.low]);
    const min = Math.min(...allPrices) * 0.99;
    const max = Math.max(...allPrices) * 1.01;
    return { min, max };
  }, [data]);
  
  // Current price
  const currentPrice = data.length > 0 ? data[data.length - 1].close : 0;
  
  return (
    <div className="space-y-4">
      {/* Header with timeframe selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-white">📊 Candlestick Chart</h3>
          <span className="text-sm text-purple-200/60">BTC/USDT</span>
        </div>
        <div className="flex space-x-1 bg-white/5 rounded-lg p-1">
          {(['1D', '1W', '1M'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 text-sm rounded-md transition-all ${
                timeframe === tf
                  ? 'bg-purple-600 text-white'
                  : 'text-purple-200/60 hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>
      
      {/* Price info */}
      <div className="flex items-center space-x-6">
        <div>
          <span className="text-sm text-purple-200/60">Current Price</span>
          <p className="text-2xl font-bold text-white">${currentPrice.toLocaleString()}</p>
        </div>
        {data.length > 0 && (
          <div>
            <span className="text-sm text-purple-200/60">24h Change</span>
            <p className={`text-lg font-semibold ${
              data[data.length - 1].close >= data[0].open ? 'text-green-400' : 'text-red-400'
            }`}>
              {data[data.length - 1].close >= data[0].open ? '+' : ''}
              {((data[data.length - 1].close - data[0].open) / data[0].open * 100).toFixed(2)}%
            </p>
          </div>
        )}
      </div>
      
      {/* Chart */}
      <div className="bg-white/5 rounded-xl p-4" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="date" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
            />
            <YAxis 
              domain={[priceRange.min, priceRange.max]}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Current price reference line */}
            <ReferenceLine 
              y={currentPrice} 
              stroke="#8b5cf6" 
              strokeDasharray="5 5"
              label={{ value: 'Current', fill: '#8b5cf6', fontSize: 10 }}
            />
            
            {/* Candlestick bars */}
            <Bar 
              dataKey="bodySize" 
              shape={<CandleShape />}
              isAnimationActive={true}
              animationDuration={800}
              animationEasing="ease-out"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {/* Volume bars */}
      <div className="bg-white/5 rounded-xl p-4" style={{ height: 100 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="date" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              tickLine={false}
            />
            <YAxis 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              tickLine={false}
              tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="volume" 
              fill="rgba(139, 92, 246, 0.5)"
              radius={[2, 2, 0, 0]}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default CandlestickChart;

import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Brush,
  ReferenceLine,
} from 'recharts';

interface PerformanceData {
  date: string;
  winRate: number;
  avgReturn: number;
  signalCount: number;
  cumulativeReturn?: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800/95 backdrop-blur-lg p-4 rounded-lg border border-white/20 shadow-xl min-w-[180px]">
        <p className="text-white font-semibold mb-2">{label}</p>
        <div className="space-y-1 text-sm">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-purple-200/60">{entry.name}:</span>
              <span className="font-mono" style={{ color: entry.color }}>
                {entry.name === 'Win Rate' || entry.name === 'Avg Return' 
                  ? `${entry.value.toFixed(1)}%` 
                  : entry.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ data }) => {
  const [activeMetric, setActiveMetric] = useState<'winRate' | 'avgReturn' | 'both'>('both');
  const [showVolume, setShowVolume] = useState(true);
  
  // Calculate average win rate
  const avgWinRate = data.reduce((sum, d) => sum + d.winRate, 0) / data.length;
  
  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-purple-200/60">Display:</span>
          <div className="flex space-x-1 bg-white/5 rounded-lg p-1">
            {[
              { id: 'both', label: 'Both' },
              { id: 'winRate', label: 'Win Rate' },
              { id: 'avgReturn', label: 'Avg Return' },
            ].map((option) => (
              <button
                key={option.id}
                onClick={() => setActiveMetric(option.id as any)}
                className={`px-3 py-1 text-xs rounded-md transition-all ${
                  activeMetric === option.id
                    ? 'bg-purple-600 text-white'
                    : 'text-purple-200/60 hover:text-white'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <label className="flex items-center space-x-2 text-sm text-purple-200/60">
          <input
            type="checkbox"
            checked={showVolume}
            onChange={(e) => setShowVolume(e.target.checked)}
            className="rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-500"
          />
          <span>Show Signals</span>
        </label>
      </div>
      
      {/* Main Chart */}
      <div className="bg-white/5 rounded-xl p-4" style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="winRateGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="avgReturnGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="date" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
            />
            <YAxis 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Average win rate reference line */}
            <ReferenceLine 
              y={avgWinRate} 
              stroke="#10b981" 
              strokeDasharray="5 5"
              strokeOpacity={0.5}
            />
            
            {(activeMetric === 'both' || activeMetric === 'winRate') && (
              <Area
                type="monotone"
                dataKey="winRate"
                name="Win Rate"
                stroke="#10b981"
                fill="url(#winRateGradient)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2, fill: '#10b981' }}
                animationDuration={1000}
              />
            )}
            
            {(activeMetric === 'both' || activeMetric === 'avgReturn') && (
              <Area
                type="monotone"
                dataKey="avgReturn"
                name="Avg Return"
                stroke="#3b82f6"
                fill="url(#avgReturnGradient)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2, fill: '#3b82f6' }}
                animationDuration={1000}
              />
            )}
            
            {showVolume && (
              <Area
                type="monotone"
                dataKey="signalCount"
                name="Signals"
                stroke="#8b5cf6"
                fill="rgba(139, 92, 246, 0.1)"
                strokeWidth={1}
                dot={false}
                animationDuration={1000}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Brush for zooming */}
      <div className="bg-white/5 rounded-xl p-2" style={{ height: 60 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="date" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 9 }}
              tickLine={false}
            />
            <YAxis hide />
            <Area
              type="monotone"
              dataKey="winRate"
              stroke="#10b981"
              fill="rgba(16, 185, 129, 0.2)"
              strokeWidth={1}
              dot={false}
            />
            <Brush 
              dataKey="date" 
              height={30} 
              stroke="#8b5cf6"
              fill="rgba(255,255,255,0.05)"
              travellerWidth={10}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-purple-200/60">Win Rate</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-purple-200/60">Avg Return</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-purple-500"></div>
          <span className="text-purple-200/60">Signal Count</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-0.5 bg-green-500 border-dashed"></div>
          <span className="text-purple-200/60">Avg ({avgWinRate.toFixed(1)}%)</span>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;

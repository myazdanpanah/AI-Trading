import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface FactorData {
  name: string;
  value: number;
  color: string;
  icon?: string;
  description?: string;
}

interface FactorBarChartProps {
  data: FactorData[];
  showDetails?: boolean;
}

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800/95 backdrop-blur-lg p-4 rounded-lg border border-white/20 shadow-xl min-w-[180px]">
        <div className="flex items-center space-x-2 mb-2">
          {data.icon && <span className="text-xl">{data.icon}</span>}
          <p className="text-white font-semibold">{data.name}</p>
        </div>
        <p className="text-2xl font-bold text-purple-400">{data.value}%</p>
        {data.description && (
          <p className="text-sm text-purple-200/60 mt-2">{data.description}</p>
        )}
        <div className="mt-2 pt-2 border-t border-white/10">
          <div className="flex items-center justify-between text-sm">
            <span className="text-purple-200/60">Performance:</span>
            <span className={`font-medium ${
              data.value >= 70 ? 'text-green-400' : 
              data.value >= 50 ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {data.value >= 70 ? 'Excellent' : data.value >= 50 ? 'Good' : 'Needs Improvement'}
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const FactorBarChart: React.FC<FactorBarChartProps> = ({ data, showDetails = true }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  
  // Sort data by value
  const sortedData = [...data].sort((a, b) => b.value - a.value);
  
  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="bg-white/5 rounded-xl p-4" style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={sortedData} 
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            layout="vertical"
            onMouseMove={(state) => {
              if (state?.activeTooltipIndex !== undefined) {
                setHoveredIndex(state.activeTooltipIndex);
              }
            }}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
            <XAxis 
              type="number"
              domain={[0, 100]}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis 
              dataKey="name"
              type="category"
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
              tickLine={false}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} cursor={false} />
            <Bar 
              dataKey="value" 
              radius={[0, 6, 6, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              {sortedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color}
                  opacity={hoveredIndex === null || hoveredIndex === index ? 1 : 0.5}
                  style={{ transition: 'opacity 0.2s ease' }}
                />
              ))}
              <LabelList 
                dataKey="value" 
                position="right"
                fill="rgba(255,255,255,0.7)"
                fontSize={12}
                formatter={(value: number) => `${value}%`}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Factor Details */}
      {showDetails && (
        <div className="grid grid-cols-5 gap-3">
          {sortedData.map((factor, index) => (
            <div 
              key={factor.name}
              className={`bg-white/5 rounded-lg p-3 text-center transition-all hover:bg-white/10 cursor-pointer ${
                hoveredIndex === index ? 'ring-2 ring-purple-500' : ''
              }`}
            >
              {factor.icon && <div className="text-2xl mb-1">{factor.icon}</div>}
              <p className="text-xs text-purple-200/60">{factor.name}</p>
              <div className="mt-2 w-full bg-white/10 rounded-full h-2">
                <div 
                  className="h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${factor.value}%`,
                    backgroundColor: factor.color
                  }}
                />
              </div>
              <p className="text-lg font-semibold text-white mt-1">{factor.value}%</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FactorBarChart;

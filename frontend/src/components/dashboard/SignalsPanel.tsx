import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface Signal {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  risk_score: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number[];
  timeframe: string;
  composite_score: number;
  created_at: string;
}

export const SignalsPanel: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC-USDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');

  useEffect(() => {
    fetchSignals();
  }, []);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch('/signals/signals/latest/?limit=20');
      if (response.ok) {
        setSignals(await response.json());
      } else {
        setError('Failed to load signals');
      }
    } catch (err) {
      console.error('Failed to fetch signals:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateSignal = async () => {
    setGenerating(true);
    try {
      const response = await apiFetch('/signals/signals/generate/', {
        method: 'POST',
        body: JSON.stringify({
          symbol: selectedSymbol,
          timeframe: selectedTimeframe,
          current_price: 50000,
        }),
      });
      
      if (response.ok) {
        fetchSignals();
      } else {
        setError('Failed to generate signal');
      }
    } catch (err) {
      console.error('Failed to generate signal:', err);
      setError('Network error. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 animate-pulse">
            <div className="h-4 bg-white/20 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-white/10 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 backdrop-blur-lg rounded-xl p-6 border border-red-500/20">
        <p className="text-red-400">{error}</p>
        <button 
          onClick={fetchSignals}
          className="mt-4 px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Signal Generator */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
        <h2 className="text-xl font-semibold text-white mb-4">🎯 Signal Generator</h2>
        <div className="flex flex-wrap items-center gap-4">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="BTC-USDT" className="bg-slate-800">BTC-USDT</option>
            <option value="ETH-USDT" className="bg-slate-800">ETH-USDT</option>
            <option value="SOL-USDT" className="bg-slate-800">SOL-USDT</option>
          </select>
          
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="1h" className="bg-slate-800">1 Hour</option>
            <option value="4h" className="bg-slate-800">4 Hours</option>
            <option value="1d" className="bg-slate-800">1 Day</option>
          </select>
          
          <button
            onClick={generateSignal}
            disabled={generating}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 transition-all shadow-lg shadow-purple-500/25"
          >
            {generating ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </span>
            ) : (
              'Generate Signal'
            )}
          </button>
        </div>
      </div>

      {/* Signals List */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
        <h2 className="text-xl font-semibold text-white mb-4">📋 Recent Signals</h2>
        {signals.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-purple-200/60">No signals generated yet</p>
            <button
              onClick={generateSignal}
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
            >
              Generate Your First Signal
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Symbol</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Direction</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Confidence</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Risk</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Entry</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Stop Loss</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Timeframe</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-purple-200/60">Created</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((signal) => (
                  <tr key={signal.id} className="border-b border-white/5 hover:bg-white/5 transition-all">
                    <td className="px-4 py-4 font-medium text-white">{signal.symbol}</td>
                    <td className="px-4 py-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                        signal.direction.includes('buy') 
                          ? 'bg-green-500/20 text-green-400' 
                          : signal.direction.includes('sell')
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {signal.direction.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center">
                        <div className="w-20 bg-white/10 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              signal.confidence > 70 ? 'bg-green-500' : 
                              signal.confidence > 40 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${signal.confidence}%` }}
                          />
                        </div>
                        <span className="ml-2 text-sm text-white">{signal.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`text-sm font-medium ${
                        signal.risk_score < 30 ? 'text-green-400' :
                        signal.risk_score < 70 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {signal.risk_score}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-mono text-sm text-white">
                      ${signal.entry_price?.toLocaleString() || '-'}
                    </td>
                    <td className="px-4 py-4 font-mono text-sm text-red-400">
                      ${signal.stop_loss?.toLocaleString() || '-'}
                    </td>
                    <td className="px-4 py-4 text-sm text-purple-200">{signal.timeframe}</td>
                    <td className="px-4 py-4 text-sm text-purple-200/60">
                      {new Date(signal.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SignalsPanel;

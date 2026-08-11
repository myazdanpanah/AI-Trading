import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../utils/api';

interface Trader {
  id: string;
  display_name: string;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  followers_count: number;
  total_signals: number;
  is_following: boolean;
}

export const Leaderboard: React.FC = () => {
  const [traders, setTraders] = useState<Trader[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'win_rate' | 'profit_factor' | 'followers_count'>('win_rate');

  useEffect(() => {
    fetchTraders();
  }, []);

  const fetchTraders = async () => {
    try {
      const response = await apiFetch('/social/traders/leaderboard/');
      if (response.ok) {
        setTraders(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch traders:', error);
      // Mock data
      setTraders([
        { id: '1', display_name: 'CryptoMaster', win_rate: 72.5, profit_factor: 2.1, sharpe_ratio: 1.8, followers_count: 1250, total_signals: 342, is_following: false },
        { id: '2', display_name: 'AlphaTrader', win_rate: 68.3, profit_factor: 1.9, sharpe_ratio: 1.6, followers_count: 890, total_signals: 278, is_following: true },
        { id: '3', display_name: 'BullSignal', win_rate: 65.1, profit_factor: 1.7, sharpe_ratio: 1.4, followers_count: 654, total_signals: 198, is_following: false },
        { id: '4', display_name: 'SmartMoney', win_rate: 71.2, profit_factor: 2.3, sharpe_ratio: 1.9, followers_count: 1580, total_signals: 421, is_following: true },
        { id: '5', display_name: 'WhaleTracker', win_rate: 63.8, profit_factor: 1.5, sharpe_ratio: 1.2, followers_count: 432, total_signals: 156, is_following: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleFollow = async (traderId: string) => {
    try {
      const response = await apiFetch(`/social/traders/${traderId}/follow/`, {
        method: 'POST',
      });
      if (response.ok) {
        setTraders(prev => prev.map(t => 
          t.id === traderId ? { ...t, is_following: !t.is_following } : t
        ));
      }
    } catch (error) {
      console.error('Failed to follow trader:', error);
    }
  };

  const sortedTraders = [...traders].sort((a, b) => b[sortBy] - a[sortBy]);

  if (loading) {
    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 animate-pulse">
        <div className="h-6 bg-white/20 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-white/10 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-white">🏆 Top Traders</h2>
        <div className="flex space-x-2">
          {(['win_rate', 'profit_factor', 'followers_count'] as const).map((metric) => (
            <button
              key={metric}
              onClick={() => setSortBy(metric)}
              className={`px-3 py-1 text-xs rounded-lg transition-all ${
                sortBy === metric
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-purple-200/60 hover:text-white'
              }`}
            >
              {metric === 'win_rate' ? 'Win Rate' : metric === 'profit_factor' ? 'Profit' : 'Followers'}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {sortedTraders.map((trader, index) => (
          <div
            key={trader.id}
            className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all"
          >
            <div className="flex items-center space-x-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
                index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                index === 1 ? 'bg-gray-400/20 text-gray-300' :
                index === 2 ? 'bg-orange-500/20 text-orange-400' :
                'bg-white/10 text-white'
              }`}>
                {index + 1}
              </div>
              <div>
                <div className="font-medium text-white">{trader.display_name}</div>
                <div className="text-sm text-purple-200/60">{trader.total_signals} signals</div>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="text-center">
                <div className="text-lg font-semibold text-green-400">{trader.win_rate}%</div>
                <div className="text-xs text-purple-200/60">Win Rate</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-blue-400">{trader.profit_factor}x</div>
                <div className="text-xs text-purple-200/60">Profit</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-purple-400">{trader.sharpe_ratio}</div>
                <div className="text-xs text-purple-200/60">Sharpe</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">{trader.followers_count}</div>
                <div className="text-xs text-purple-200/60">Followers</div>
              </div>

              <button
                onClick={() => toggleFollow(trader.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  trader.is_following
                    ? 'bg-white/10 text-white hover:bg-white/20'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {trader.is_following ? 'Following' : 'Follow'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Leaderboard;

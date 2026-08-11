/**
 * API utility with authentication headers and mock data fallback
 */

const API_BASE = '/api';

// Mock data for testing without backend
const MOCK_DATA = {
  market: [
    { symbol: 'BTC-USDT', price: 67542.30, change_24h: 2.45, volume: 28500000000 },
    { symbol: 'ETH-USDT', price: 3456.78, change_24h: -1.23, volume: 15200000000 },
    { symbol: 'SOL-USDT', price: 178.92, change_24h: 5.67, volume: 3800000000 },
  ],
  signals: [
    { id: '1', symbol: 'BTC-USDT', direction: 'buy', confidence: 85, risk_score: 35, entry_price: 67500, stop_loss: 65000, take_profit: [72000, 75000], timeframe: '4h', composite_score: 78, created_at: new Date().toISOString() },
    { id: '2', symbol: 'ETH-USDT', direction: 'strong_buy', confidence: 92, risk_score: 25, entry_price: 3450, stop_loss: 3200, take_profit: [3800, 4000], timeframe: '1d', composite_score: 88, created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: '3', symbol: 'SOL-USDT', direction: 'sell', confidence: 68, risk_score: 55, entry_price: 180, stop_loss: 195, take_profit: [160, 150], timeframe: '1h', composite_score: 55, created_at: new Date(Date.now() - 7200000).toISOString() },
  ],
  insights: [
    { id: '1', type: 'weight_adjustment', title: 'Increase Technical Weight', description: 'Technical analysis has shown 73% accuracy over the past week. Consider increasing its weight from 30% to 35%.', confidence: 0.85, impact_score: 0.72, related_symbols: ['BTC-USDT', 'ETH-USDT'], was_implemented: false, created_at: new Date().toISOString() },
    { id: '2', type: 'strategy_recommendation', title: 'Favor Long Positions', description: 'Market sentiment and on-chain metrics suggest bullish momentum. Consider favoring long positions for major cryptocurrencies.', confidence: 0.78, impact_score: 0.65, related_symbols: ['BTC-USDT'], was_implemented: false, created_at: new Date(Date.now() - 86400000).toISOString() },
  ],
  cycles: [
    { id: '1', cycle_type: 'daily', status: 'completed', signals_evaluated: 15, signals_correct: 10, win_rate: 66.7, insights_generated: 3, summary: 'Daily cycle completed with good performance', started_at: new Date(Date.now() - 86400000).toISOString(), completed_at: new Date(Date.now() - 86400000 + 300000).toISOString() },
    { id: '2', cycle_type: 'weekly', status: 'completed', signals_evaluated: 85, signals_correct: 55, win_rate: 64.7, insights_generated: 8, summary: 'Weekly cycle completed with consistent performance', started_at: new Date(Date.now() - 604800000).toISOString(), completed_at: new Date(Date.now() - 604800000 + 1800000).toISOString() },
  ],
  performance: {
    win_rate: 65.2,
    total_signals: 156,
    avg_return: 3.45,
    profit_factor: 1.82,
    sharpe_ratio: 1.45,
  },
  insights_list: [
    { id: '1', type: 'weight_adjustment', title: 'Increase Technical Weight', description: 'Technical analysis has shown 73% accuracy over the past week.', confidence: 0.85, impact_score: 0.72, related_symbols: ['BTC-USDT', 'ETH-USDT'], was_implemented: false, created_at: new Date().toISOString() },
  ],
};

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Get the authorization headers for API requests
 */
export function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token');
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
  return {
    'Content-Type': 'application/json',
  };
}

/**
 * Check if we should use mock data
 */
function shouldUseMockData(): boolean {
  return localStorage.getItem('use_mock_data') === 'true';
}

/**
 * Authenticated fetch wrapper with mock data fallback
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  // Check if we should use mock data
  if (shouldUseMockData()) {
    return mockFetch(url, options);
  }

  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };
  
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers,
    });
    
    return response;
  } catch (error) {
    // If network error, try mock data as fallback
    console.log('API unavailable, using mock data as fallback');
    return mockFetch(url, options);
  }
}

/**
 * Mock fetch that returns fake data
 */
async function mockFetch(url: string, options: RequestInit = {}): Promise<Response> {
  await delay(300); // Simulate network delay
  
  let data: any;
  
  if (url.includes('/market/prices/')) {
    data = MOCK_DATA.market;
  } else if (url.includes('/signals/signals/latest/')) {
    data = MOCK_DATA.signals;
  } else if (url.includes('/signals/signals/generate/')) {
    data = { id: Date.now().toString(), symbol: 'BTC-USDT', direction: 'buy', confidence: 75 };
  } else if (url.includes('/feedback/analysis/insights/')) {
    data = MOCK_DATA.insights;
  } else if (url.includes('/feedback/cycles/history/')) {
    data = MOCK_DATA.cycles;
  } else if (url.includes('/learning/results/performance/')) {
    data = MOCK_DATA.performance;
  } else if (url.includes('/feedback/analysis/analyze/')) {
    data = { overall: MOCK_DATA.performance, insights: MOCK_DATA.insights };
  } else if (url.includes('/auth/login/')) {
    data = { access: 'mock_token', refresh: 'mock_refresh' };
  } else {
    data = { message: 'Mock endpoint' };
  }
  
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Check if the user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('access_token');
}

/**
 * Clear authentication tokens
 */
export function clearAuth(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/**
 * Toggle mock data mode
 */
export function toggleMockData(): boolean {
  const current = localStorage.getItem('use_mock_data') === 'true';
  localStorage.setItem('use_mock_data', (!current).toString());
  return !current;
}

/**
 * Check if mock data is enabled
 */
export function isMockDataEnabled(): boolean {
  return localStorage.getItem('use_mock_data') === 'true';
}

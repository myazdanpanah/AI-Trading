import axios from 'axios';
import { getAuthToken } from './auth';

const API_BASE = 'http://localhost:8000/api';

// Types
export interface PriceData {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
}

export interface Signal {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  risk_score: number;
  entry_price: number;
  stop_loss: number | null;
  take_profit: number[];
  timeframe: string;
  composite_score: number;
  created_at: string;
}

// API client with auth interceptor
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Add auth token to requests
apiClient.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, could refresh here
    }
    return Promise.reject(error);
  }
);

// API functions
export const fetchPrices = async (): Promise<PriceData[]> => {
  try {
    const response = await apiClient.get('/market/prices/');
    return response.data;
  } catch (error) {
    // Return mock data for demo
    return [
      { symbol: 'BTC-USDT', price: 67542.30, change_24h: 2.45, volume: 28500000000 },
      { symbol: 'ETH-USDT', price: 3456.78, change_24h: -1.23, volume: 15200000000 },
      { symbol: 'SOL-USDT', price: 178.92, change_24h: 5.67, volume: 3800000000 },
      { symbol: 'BNB-USDT', price: 621.45, change_24h: 1.89, volume: 2100000000 },
      { symbol: 'XRP-USDT', price: 0.6234, change_24h: -0.45, volume: 1800000000 },
    ];
  }
};

export const fetchSignals = async (): Promise<Signal[]> => {
  try {
    const response = await apiClient.get('/signals/signals/latest/');
    return response.data;
  } catch (error) {
    // Return mock data for demo
    return [
      {
        id: '1',
        symbol: 'BTC-USDT',
        direction: 'buy',
        confidence: 85,
        risk_score: 35,
        entry_price: 67500,
        stop_loss: 65000,
        take_profit: [72000, 75000],
        timeframe: '4h',
        composite_score: 78,
        created_at: new Date().toISOString(),
      },
      {
        id: '2',
        symbol: 'ETH-USDT',
        direction: 'strong_buy',
        confidence: 92,
        risk_score: 25,
        entry_price: 3450,
        stop_loss: 3200,
        take_profit: [3800, 4000],
        timeframe: '1d',
        composite_score: 88,
        created_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: '3',
        symbol: 'SOL-USDT',
        direction: 'sell',
        confidence: 68,
        risk_score: 55,
        entry_price: 180,
        stop_loss: 195,
        take_profit: [160, 150],
        timeframe: '1h',
        composite_score: 55,
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
    ];
  }
};

export const fetchPortfolio = async () => {
  try {
    const response = await apiClient.get('/portfolio/portfolios/');
    return response.data;
  } catch (error) {
    return null;
  }
};

export const generateSignal = async (symbol: string, timeframe: string): Promise<Signal> => {
  const response = await apiClient.post('/signals/signals/generate/', {
    symbol,
    timeframe,
    current_price: 50000,
  });
  return response.data;
};

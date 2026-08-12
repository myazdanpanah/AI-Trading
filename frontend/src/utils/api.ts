/**
 * API utility with authentication headers
 */
import axios from 'axios';

const API_BASE = '/api';

// Axios instance with auth
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;


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
 * Authenticated fetch wrapper
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  return response;
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
 * Toggle mock data mode (kept for backward compatibility, now always false)
 */
export function toggleMockData(): boolean {
  return false;
}

/**
 * Check if mock data is enabled (always false now)
 */
export function isMockDataEnabled(): boolean {
  return false;
}

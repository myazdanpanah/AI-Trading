import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const login = async (username: string, password: string): Promise<void> => {
  const response = await axios.post(`${API_BASE}/auth/login/`, {
    username,
    password,
  });

  const { access, refresh } = response.data;
  await AsyncStorage.setItem('access_token', access);
  await AsyncStorage.setItem('refresh_token', refresh);
};

export const logout = async (): Promise<void> => {
  await AsyncStorage.removeItem('access_token');
  await AsyncStorage.removeItem('refresh_token');
};

export const isAuthenticated = async (): Promise<boolean> => {
  const token = await AsyncStorage.getItem('access_token');
  return !!token;
};

export const getAuthToken = async (): Promise<string | null> => {
  return AsyncStorage.getItem('access_token');
};

export const refreshToken = async (): Promise<string | null> => {
  const refresh = await AsyncStorage.getItem('refresh_token');
  if (!refresh) return null;

  try {
    const response = await axios.post(`${API_BASE}/auth/token/refresh/`, {
      refresh,
    });
    const { access } = response.data;
    await AsyncStorage.setItem('access_token', access);
    return access;
  } catch (error) {
    await logout();
    return null;
  }
};

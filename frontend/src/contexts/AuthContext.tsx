import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  loading: true,
  login: () => {},
  logout: () => {},
  refreshToken: async () => false,
});

export const useAuth = () => useContext(AuthContext);

// Session timeout: 15 minutes in milliseconds
const SESSION_TIMEOUT = 15 * 60 * 1000;
const ACTIVITY_KEY = 'last_activity';

const getActivityTimestamp = (): number => {
  const stored = localStorage.getItem(ACTIVITY_KEY);
  return stored ? parseInt(stored, 10) : Date.now();
};

const updateActivityTimestamp = (): void => {
  localStorage.setItem(ACTIVITY_KEY, Date.now().toString());
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    // Try to load user from localStorage on init
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [loading, setLoading] = useState(true);
  const logoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Check if session has expired
  const isSessionExpired = (): boolean => {
    const lastActivity = getActivityTimestamp();
    const now = Date.now();
    return (now - lastActivity) > SESSION_TIMEOUT;
  };

  // Reset logout timer
  const resetLogoutTimer = () => {
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current);
    }
    
    // Set new timer for 15 minutes
    logoutTimerRef.current = setTimeout(() => {
      console.log('Session expired due to inactivity');
      logout();
    }, SESSION_TIMEOUT);
  };

  // Track user activity
  useEffect(() => {
    const handleActivity = () => {
      updateActivityTimestamp();
      resetLogoutTimer();
    };

    // Events that count as user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove'];
    
    events.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    // Initialize activity timestamp if not set
    if (!localStorage.getItem(ACTIVITY_KEY)) {
      updateActivityTimestamp();
    }

    // Start the timer
    resetLogoutTimer();

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      if (logoutTimerRef.current) {
        clearTimeout(logoutTimerRef.current);
      }
    };
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setLoading(false);
      return;
    }

    // Check if session expired
    if (isSessionExpired()) {
      console.log('Session expired, logging out');
      logout();
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/users/users/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Handle paginated list or single object
        const userData = Array.isArray(data) ? data[0] : (data.results && data.results.length > 0 ? data.results[0] : data);
        if (userData && userData.username) {
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));
          updateActivityTimestamp();
        }
      } else if (response.status === 401) {
        // Token expired, try to refresh
        const refreshed = await refreshToken();
        if (!refreshed) {
          logout();
        }
      } else {
        // Token invalid, clear everything
        logout();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Network error - keep existing user if we have one from localStorage
      // This allows the app to work offline or when backend is down
    } finally {
      setLoading(false);
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    const refreshTokenValue = localStorage.getItem('refresh_token');
    
    if (!refreshTokenValue) {
      return false;
    }

    try {
      const response = await fetch('/api/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshTokenValue }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        if (data.refresh) {
          localStorage.setItem('refresh_token', data.refresh);
        }
        updateActivityTimestamp();
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  };

  const login = (token: string, userData: User) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    updateActivityTimestamp();
    setUser(userData);
    resetLogoutTimer();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem(ACTIVITY_KEY);
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current);
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

import React, { useState, useEffect } from 'react';
import { Dashboard } from './components/dashboard/Dashboard';
import { LoginForm } from './components/auth/LoginForm';
import { isAuthenticated } from './utils/api';
import { WatchlistProvider } from './contexts/WatchlistContext';
import { LanguageProvider } from './contexts/LanguageContext';

const App: React.FC = () => {
  const [isAuth, setIsAuth] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated()) {
      setIsAuth(true);
    }
    setLoading(false);
  }, []);

  const handleLogin = () => {
    setIsAuth(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsAuth(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto"></div>
          <p className="mt-4 text-purple-200">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuth) {
    return (
      <LanguageProvider>
        <LoginForm onLogin={handleLogin} />
      </LanguageProvider>
    );
  }

  return (
    <LanguageProvider>
      <WatchlistProvider>
        <Dashboard onLogout={handleLogout} />
      </WatchlistProvider>
    </LanguageProvider>
  );
};

export default App;

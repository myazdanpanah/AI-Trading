import React, { useState, useEffect } from 'react';
import { Dashboard } from './components/dashboard/Dashboard';
import { LoginForm } from './components/auth/LoginForm';
import { isAuthenticated, toggleMockData, isMockDataEnabled } from './utils/api';

const App: React.FC = () => {
  const [isAuth, setIsAuth] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mockMode, setMockMode] = useState(false);

  useEffect(() => {
    // Check if mock data is enabled
    setMockMode(isMockDataEnabled());
    
    // Check authentication
    if (isAuthenticated() || isMockDataEnabled()) {
      setIsAuth(true);
    }
    setLoading(false);
  }, []);

  const handleLogin = (token: string) => {
    setIsAuth(true);
    setMockMode(false);
    localStorage.removeItem('use_mock_data');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('use_mock_data');
    setIsAuth(false);
    setMockMode(false);
  };

  const handleToggleMock = () => {
    const newMode = toggleMockData();
    setMockMode(newMode);
    if (newMode) {
      setIsAuth(true);
    }
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
      <div>
        <LoginForm onLogin={handleLogin} />
        <div className="fixed bottom-4 right-4">
          <button
            onClick={handleToggleMock}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 shadow-lg text-sm"
          >
            🚀 Try Demo Mode
          </button>
        </div>
      </div>
    );
  }

  return (
    <Dashboard 
      onLogout={handleLogout} 
      mockMode={mockMode} 
      onToggleMock={handleToggleMock}
    />
  );
};

export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WatchlistProvider } from './contexts/WatchlistContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { SettingsProvider } from './contexts/SettingsContext';
import Login from './pages/Login';
import Register from './pages/Register';
import { Dashboard } from './components/dashboard/Dashboard';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <div className="text-white text-xl">Loading...</div>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

// Dashboard wrapper that handles tab routing
const DashboardRoute: React.FC = () => {
  const { tab } = useParams();
  const validTabs = ['trading', 'signals', 'analysis', 'journal', 'feedback', 'settings'];
  const activeTab = validTabs.includes(tab || '') ? tab as string : 'trading';
  
  return (
    <ProtectedRoute>
      <Dashboard initialTab={activeTab} />
    </ProtectedRoute>
  );
};

function App() {
  return (
    <Router>
      <LanguageProvider>
        <AuthProvider>
          <SettingsProvider>
            <WatchlistProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/dashboard" element={<Navigate to="/dashboard/trading" replace />} />
                <Route path="/dashboard/:tab" element={<DashboardRoute />} />
                <Route path="/" element={<Navigate to="/dashboard/trading" />} />
                <Route path="*" element={<Navigate to="/dashboard/trading" />} />
              </Routes>
            </WatchlistProvider>
          </SettingsProvider>
        </AuthProvider>
      </LanguageProvider>
    </Router>
  );
}

export default App;

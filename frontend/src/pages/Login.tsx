import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from '../components/auth/LoginForm';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = (token: string) => {
    // Fetch user data after login
    fetch('/api/users/users/', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then(res => res.json())
      .then(data => {
        const userData = Array.isArray(data) ? data[0] : (data.results && data.results.length > 0 ? data.results[0] : data);
        login(token, userData || { id: 1, username: 'user', email: 'user@example.com' });
        navigate('/dashboard');
      })
      .catch(() => {
        login(token, { id: 1, username: 'user', email: 'user@example.com' });
        navigate('/dashboard');
      });
  };

  return <LoginForm onLogin={handleLogin} />;
};

export default Login;

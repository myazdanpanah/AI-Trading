import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

interface SignalNotification {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  price: number;
  timeframe: string;
  timestamp: Date;
}

interface ToastProps {
  notification: SignalNotification;
  onDismiss: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ notification, onDismiss }) => {
  const { language } = useLanguage();
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Animate in
    setTimeout(() => setIsVisible(true), 10);
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      setIsExiting(true);
      setTimeout(() => onDismiss(notification.id), 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [notification.id, onDismiss]);

  const directionColor = notification.direction === 'buy' || notification.direction === 'long'
    ? 'border-green-500 bg-green-500/10'
    : notification.direction === 'sell' || notification.direction === 'short'
    ? 'border-red-500 bg-red-500/50/10'
    : 'border-yellow-500 bg-yellow-500/10';

  const directionIcon = notification.direction === 'buy' || notification.direction === 'long'
    ? '📈'
    : notification.direction === 'sell' || notification.direction === 'short'
    ? '📉'
    : '⏸️';

  return (
    <div
      className={`
        fixed top-4 right-4 z-50 w-80
        transform transition-all duration-300 ease-out
        ${isVisible && !isExiting ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
    >
      <div className={`rounded-lg border-l-4 ${directionColor} bg-gray-800 shadow-lg p-4`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{directionIcon}</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">{notification.symbol}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  notification.direction === 'buy' ? 'bg-green-500/20 text-green-400' :
                  notification.direction === 'sell' ? 'bg-red-500/20 text-red-400' :
                  'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {notification.direction.toUpperCase()}
                </span>
              </div>
              <div className="text-sm text-gray-400 mt-1">
                {language === 'fa' ? 'اطمینان' : 'Confidence'}: {notification.confidence}%
                {notification.price > 0 && (
                  <span className="ml-2">${notification.price.toLocaleString()}</span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={() => onDismiss(notification.id)}
            className="text-gray-500 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          {notification.timeframe} • {new Date(notification.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

interface SignalToastManagerProps {
  notifications: SignalNotification[];
  onDismiss: (id: string) => void;
}

export const SignalToastManager: React.FC<SignalToastManagerProps> = ({ notifications, onDismiss }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          notification={notification}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
};

// Hook to manage signal notifications
export function useSignalNotifications() {
  const [notifications, setNotifications] = useState<SignalNotification[]>([]);

  const addNotification = useCallback((signal: Omit<SignalNotification, 'id' | 'timestamp'>) => {
    const notification: SignalNotification = {
      ...signal,
      id: `signal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setNotifications(prev => [...prev, notification]);

    // Play sound for high confidence signals
    if (signal.confidence >= 70) {
      try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAf39/f3+AgICAgICBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGB');
        audio.volume = 0.3;
        audio.play().catch(() => {});
      } catch {}
    }

    // Request browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`Signal: ${signal.symbol} ${signal.direction.toUpperCase()}`, {
        body: `Confidence: ${signal.confidence}% | Price: $${signal.price.toLocaleString()}`,
        icon: '/favicon.ico',
      });
    }
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return {
    notifications,
    addNotification,
    dismissNotification,
    clearAll,
  };
}

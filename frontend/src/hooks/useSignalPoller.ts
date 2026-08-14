import { useEffect, useRef, useCallback, useState } from 'react';
import { apiFetch } from '../utils/api';

interface Signal {
  id: string;
  symbol: string;
  direction: string;
  confidence: number;
  entry_price: number;
  timeframe: string;
  created_at: string;
}

interface UseSignalPollerOptions {
  intervalMs?: number;
  enabled?: boolean;
  onNewSignal?: (signal: Signal) => void;
}

export function useSignalPoller(options: UseSignalPollerOptions = {}) {
  const { intervalMs = 30000, enabled = true, onNewSignal } = options;
  const [lastSignalId, setLastSignalId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkForNewSignals = useCallback(async () => {
    try {
      const response = await apiFetch('/signals/signals/?format=json&is_active=true&ordering=-created_at&limit=1');
      if (response.ok) {
        const data = await response.json();
        const signals = data.results || data || [];
        
        if (signals.length > 0) {
          const latestSignal = signals[0];
          
          // Check if this is a new signal
          if (lastSignalId && latestSignal.id !== lastSignalId) {
            // New signal detected!
            if (onNewSignal) {
              onNewSignal({
                id: latestSignal.id,
                symbol: latestSignal.symbol,
                direction: latestSignal.direction,
                confidence: latestSignal.confidence,
                entry_price: latestSignal.entry_price,
                timeframe: latestSignal.timeframe,
                created_at: latestSignal.created_at,
              });
            }
          }
          
          setLastSignalId(latestSignal.id);
        }
      }
    } catch (e) {
      console.error('Signal poll error:', e);
    }
  }, [lastSignalId, onNewSignal]);

  useEffect(() => {
    if (!enabled) return;

    // Initial check
    checkForNewSignals();

    // Set up polling
    intervalRef.current = setInterval(() => {
      checkForNewSignals();
    }, intervalMs);

    setIsPolling(true);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };
  }, [enabled, intervalMs, checkForNewSignals]);

  return { isPolling, lastSignalId };
}

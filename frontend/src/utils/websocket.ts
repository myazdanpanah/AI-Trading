/**
 * WebSocket utility for real-time data streaming
 */

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

interface WebSocketOptions {
  onMessage?: MessageHandler;
  onConnect?: ConnectionHandler;
  onDisconnect?: ConnectionHandler;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  private handlers: Map<string, MessageHandler[]> = new Map();
  private options: WebSocketOptions;
  private reconnectAttempts: number;
  private reconnectInterval: number;

  constructor(options: WebSocketOptions = {}) {
    this.options = options;
    this.reconnectAttempts = options.reconnectAttempts || 5;
    this.reconnectInterval = options.reconnectInterval || 3000;
  }

  connect(url: string, onMessage?: MessageHandler): WebSocket {
    // Check if already connected
    const existing = this.connections.get(url);
    if (existing && existing.readyState === WebSocket.OPEN) {
      if (onMessage) {
        const handlers = this.handlers.get(url) || [];
        handlers.push(onMessage);
        this.handlers.set(url, handlers);
      }
      return existing;
    }

    // Create new connection
    const ws = new WebSocket(url);
    
    // Store handlers
    if (onMessage) {
      const handlers = this.handlers.get(url) || [];
      handlers.push(onMessage);
      this.handlers.set(url, handlers);
    }

    ws.onopen = () => {
      console.log(`WebSocket connected: ${url}`);
      this.options.onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const handlers = this.handlers.get(url) || [];
        handlers.forEach(handler => handler(data));
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket disconnected: ${url}`, event.code);
      this.connections.delete(url);
      this.options.onDisconnect?.();
      
      // Attempt reconnection if not intentionally closed
      if (event.code !== 1000 && this.reconnectAttempts > 0) {
        setTimeout(() => {
          this.reconnectAttempts--;
          this.connect(url);
        }, this.reconnectInterval);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error: ${url}`, error);
      this.options.onError?.(error);
    };

    this.connections.set(url, ws);
    return ws;
  }

  disconnect(url: string) {
    const ws = this.connections.get(url);
    if (ws) {
      ws.close(1000); // Normal closure
      this.connections.delete(url);
      this.handlers.delete(url);
    }
  }

  disconnectAll() {
    this.connections.forEach((ws) => {
      ws.close(1000);
    });
    this.connections.clear();
    this.handlers.clear();
  }

  send(url: string, data: any) {
    const ws = this.connections.get(url);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }

  isConnected(url: string): boolean {
    const ws = this.connections.get(url);
    return ws !== undefined && ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const wsManager = new WebSocketManager({
  reconnectAttempts: 5,
  reconnectInterval: 3000,
});

// Helper functions
export const getWsUrl = (path: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}${path}`;
};

export const connectPriceStream = (
  symbol: string,
  onPrice: (data: any) => void
): WebSocket => {
  const wsSymbol = symbol.replace('-', '/');
  const wsUrl = getWsUrl(`/ws/prices/${wsSymbol}/`);
  return wsManager.connect(wsUrl, onPrice);
};

export const connectOrderBookStream = (
  symbol: string,
  onOrderBook: (data: any) => void
): WebSocket => {
  const wsSymbol = symbol.replace('-', '/');
  const wsUrl = getWsUrl(`/ws/orderbook/${wsSymbol}/`);
  return wsManager.connect(wsUrl, onOrderBook);
};

export const connectSignalStream = (
  onSignal: (data: any) => void
): WebSocket => {
  const wsUrl = getWsUrl('/ws/signals/');
  return wsManager.connect(wsUrl, onSignal);
};

export const disconnectStream = (wsUrl: string) => {
  wsManager.disconnect(wsUrl);
};

export const disconnectAllStreams = () => {
  wsManager.disconnectAll();
};

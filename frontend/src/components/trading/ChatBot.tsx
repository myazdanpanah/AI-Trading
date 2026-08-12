import React, { useState, useRef, useEffect } from 'react';
import { apiFetch } from '../../utils/api';
import { useWatchlist } from '../../contexts/WatchlistContext';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  recommendation?: string;
  confidence?: number;
  model_used?: string;
  timestamp: string;
}

interface ChatResponse {
  answer: string;
  recommendation: string;
  confidence: number;
  symbol: string;
  model_used: string;
  analysis_summary: {
    trend: string;
    technical_score: number;
    candlestick_score: number;
    regime_zone: string;
  };
  risk_factors: string[];
  key_levels: Record<string, number>;
  execution_time_ms: number;
}

export const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedSymbol } = useWatchlist();
  const symbol = selectedSymbol.replace('USDT', '');

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiFetch('/skills/chat/', {
        method: 'POST',
        body: JSON.stringify({
          question: input,
          symbol: symbol,
        }),
      });

      if (response.ok) {
        const data: ChatResponse = await response.json();
        
        const assistantMessage: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.answer,
          recommendation: data.recommendation,
          confidence: data.confidence,
          model_used: data.model_used,
          timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        const errorMsg: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'Sorry, I encountered an error analyzing the market. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } catch (error) {
      const errorMsg: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Network error. Please check your connection and try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getRecommendationColor = (rec: string) => {
    if (rec === 'BUY') return 'bg-green-500/20 text-green-400 border border-green-500/30';
    if (rec === 'SELL') return 'bg-red-500/20 text-red-400 border border-red-500/30';
    return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 70) return 'text-green-400';
    if (conf >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const suggestedQuestions = [
    `Should I buy ${symbol} now?`,
    `Is it a good time to sell?`,
    `What's the trend?`,
    `Analyze ${symbol}`,
    `Should I hold?`,
  ];

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 ${
          isOpen 
            ? 'bg-red-500 hover:bg-red-600 rotate-0' 
            : 'bg-gradient-to-br from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 hover:scale-110'
        }`}
      >
        {isOpen ? (
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>

      {/* Notification Badge */}
      {!isOpen && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
        <div className="fixed bottom-16 right-6 z-50 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
      )}

      {/* Chat Popup */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 h-[500px] bg-[#1e1e2e] rounded-xl shadow-2xl border border-[#2a2a3e] flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <span className="text-xl">🤖</span>
              </div>
              <div>
                <h3 className="text-white font-semibold">Trading AI</h3>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full" />
                  <span className="text-white/70 text-xs">Online • {symbol}/USD</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white/70 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">💬</span>
                </div>
                <p className="text-white font-medium">Ask me about {symbol}</p>
                <p className="text-gray-400 text-sm mt-1">I'll analyze the market and give you a recommendation</p>
                
                {/* Suggested Questions */}
                <div className="mt-6 space-y-2">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(q)}
                      className="block w-full text-left px-4 py-2 bg-[#2a2a3e] text-gray-300 text-sm rounded-lg hover:bg-[#3a3a4e] hover:text-white transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-md' 
                    : 'bg-[#2a2a3e] text-gray-200 rounded-bl-md'
                }`}>
                  {msg.role === 'assistant' && msg.recommendation && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getRecommendationColor(msg.recommendation)}`}>
                        {msg.recommendation}
                      </span>
                      {msg.confidence !== undefined && (
                        <span className={`text-xs font-bold ${getConfidenceColor(msg.confidence)}`}>
                          {msg.confidence.toFixed(0)}%
                        </span>
                      )}
                    </div>
                  )}
                  <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10">
                    <span className="text-[10px] text-gray-400">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                    {msg.model_used && (
                      <span className="text-[10px] text-gray-500">
                        via {msg.model_used}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[#2a2a3e] rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm text-gray-400">Analyzing...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#2a2a3e] bg-[#131722]">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask about ${symbol}...`}
                className="flex-1 px-4 py-3 bg-[#1e1e2e] border border-[#2a2a3e] rounded-xl text-white text-sm focus:outline-none focus:border-blue-500 placeholder-gray-500"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;

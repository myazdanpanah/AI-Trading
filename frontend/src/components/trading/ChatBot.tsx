import React, { useState, useRef, useEffect } from 'react';
import { apiFetch } from '../../utils/api';
import { useWatchlist } from '../../contexts/WatchlistContext';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  recommendation?: string;
  confidence?: number;
  timestamp: string;
}

interface ChatResponse {
  answer: string;
  recommendation: string;
  confidence: number;
  symbol: string;
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedSymbol } = useWatchlist();
  const symbol = selectedSymbol.replace('USDT', '');

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    if (rec === 'BUY') return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (rec === 'SELL') return 'bg-red-500/20 text-red-400 border-red-500/30';
    return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 70) return 'text-green-400';
    if (conf >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const suggestedQuestions = [
    `Should I buy ${symbol} now?`,
    `Is it a good time to sell ${symbol}?`,
    `Analyze ${symbol} for me`,
    `What's the trend for ${symbol}?`,
    `Should I hold ${symbol}?`,
  ];

  return (
    <div className={`bg-[#1e1e2e] border-l border-[#2a2a3e] flex flex-col ${isExpanded ? 'w-96' : 'w-12'}`}>
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#2a2a3e] flex items-center justify-between">
        {isExpanded ? (
          <>
            <div className="flex items-center gap-2">
              <span className="text-lg">🤖</span>
              <span className="text-sm font-medium text-white">Trading AI</span>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ▶
            </button>
          </>
        ) : (
          <button
            onClick={() => setIsExpanded(true)}
            className="w-full text-left text-lg hover:bg-[#2a2a3e] rounded p-1"
          >
            🤖
          </button>
        )}
      </div>

      {isExpanded && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-8">
                <div className="text-3xl mb-2">💬</div>
                <p>Ask me about trading {symbol}</p>
                <p className="text-xs mt-1">I'll analyze the market and give you a recommendation with confidence score</p>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-[#2a2a3e] text-gray-200'
                }`}>
                  {msg.role === 'assistant' && msg.recommendation && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded border ${getRecommendationColor(msg.recommendation)}`}>
                        {msg.recommendation}
                      </span>
                      {msg.confidence !== undefined && (
                        <span className={`text-xs font-bold ${getConfidenceColor(msg.confidence)}`}>
                          {msg.confidence.toFixed(0)}% confidence
                        </span>
                      )}
                    </div>
                  )}
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                  <div className="text-[10px] text-gray-400 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[#2a2a3e] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent" />
                    <span className="text-sm text-gray-400">Analyzing {symbol}...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Questions */}
          {messages.length === 0 && (
            <div className="px-3 pb-2">
              <div className="text-[10px] text-gray-500 mb-2">Suggested questions:</div>
              <div className="flex flex-wrap gap-1">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    className="text-[10px] px-2 py-1 bg-[#2a2a3e] text-gray-400 rounded hover:bg-[#3a3a4e] hover:text-white transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-[#2a2a3e]">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask about ${symbol}...`}
                className="flex-1 px-3 py-2 bg-[#131722] border border-[#2a2a3e] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatBot;

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { useSettings } from '../../contexts/SettingsContext';
import { apiFetch } from '../../utils/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    recommendation?: string;
    model_used?: string;
    execution_time_ms?: number;
    language?: string;
    analysis_summary?: any;
    risk_factors?: string[];
    key_levels?: any;
  };
}

const STORAGE_KEY = 'trading_chat_history';

export const ChatBot: React.FC = () => {
  const { selectedSymbol } = useWatchlist();
  const { t, language } = useLanguage();
  const { selectedModel } = useSettings();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load conversation from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setMessages(parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp),
        })));
      }
    } catch (e) { /* ignore */ }
  }, []);

  // Save conversation to localStorage when messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        // Keep last 50 messages to avoid localStorage overflow
        const toSave = messages.slice(-50);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
      } catch (e) { /* ignore */ }
    }
  }, [messages]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const getPlaceholder = () => {
    if (language === 'fa') {
      return `درباره ${selectedSymbol.replace('USDT', '')} بپرسید...`;
    }
    return `Ask about ${selectedSymbol.replace('USDT', '')}...`;
  };

  const getSuggestedQuestions = () => {
    if (language === 'fa') {
      return [
        'آیا الان وقتشه بخرم?',
        '趋势 BTC چطوره?',
        'تحلیل کن ببینم',
        ' risks چیه?',
        'بهترین قیمت ورود چنده?',
      ];
    }
    return [
      'Should I buy now?',
      'What do you think about BTC?',
      'Give me your analysis',
      'What are the risks?',
      'What\'s a good entry price?',
    ];
  };

  const handleSendMessage = async (question?: string) => {
    const text = question || inputValue.trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Build conversation history for context
      const history = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content,
      }));

      const response = await apiFetch('/skills/chat/', {
        method: 'POST',
        body: JSON.stringify({
          symbol: selectedSymbol.replace('USDT', ''),
          question: text,
          model: selectedModel,
          history: history, // Send conversation history
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer || data.error || 'No response received.',
        timestamp: new Date(),
        metadata: {
          confidence: data.confidence,
          recommendation: data.recommendation,
          model_used: data.model_used,
          execution_time_ms: data.execution_time_ms,
          language: data.language,
          analysis_summary: data.analysis_summary,
          risk_factors: data.risk_factors,
          key_levels: data.key_levels,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: language === 'fa'
          ? `متأسفانه خطایی رخ داد: ${error.message || 'خطای ناشناخته'}. لطفاً دوباره امتحان کن.`
          : `Sorry, an error occurred: ${error.message || 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec?.toUpperCase()) {
      case 'BUY':
      case 'STRONG BUY':
        return 'bg-green-500';
      case 'SELL':
      case 'STRONG SELL':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      timeZone: 'Asia/Tehran',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full shadow-lg flex items-center justify-center text-white text-2xl hover:scale-110 transition-transform z-50"
      >
        {isOpen ? '✕' : '💬'}
        {!isOpen && messages.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {messages.filter(m => m.role === 'assistant').length}
          </span>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-[420px] h-[600px] bg-gray-900 rounded-xl shadow-2xl border border-gray-700 flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 rounded-t-xl flex-shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-white">
                  {language === 'fa' ? 'هوش ترید' : 'Trading AI'}
                </h3>
                <div className="text-xs text-blue-200">
                  ● {language === 'fa' ? 'آنلاین' : 'Online'} • {selectedSymbol.replace('USDT', '')} • {selectedModel}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-white/60 hover:text-white text-xs px-2 py-1 rounded bg-white/10"
                    title="Clear history"
                  >
                    🗑️
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-white/80 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
            {messages.length === 0 ? (
              <div className="text-center text-gray-400 mt-8">
                <div className="text-4xl mb-4">🤖</div>
                <p className="text-white">{language === 'fa' ? 'سلام! من دستیار ترید شما هستم.' : 'Hey! I\'m your trading assistant.'}</p>
                <p className="text-sm mt-2">
                  {language === 'fa'
                    ? `هر سوالی درباره ${selectedSymbol.replace('USDT', '')} دارید بپرسید.`
                    : `Ask me anything about ${selectedSymbol.replace('USDT', '')}.`}
                </p>
                <p className="text-xs mt-1 text-gray-500">
                  {language === 'fa' ? 'فارسی یا انگلیسی صحبت کنید' : 'Speak in English or Persian'}
                </p>

                <div className="mt-4 space-y-2">
                  {getSuggestedQuestions().map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(q)}
                      className="block w-full text-left px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors text-white"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </div>

                    {msg.metadata && (
                      <div className="mt-2 pt-2 border-t border-gray-600 space-y-2">
                        {/* Recommendation badge */}
                        {msg.metadata.recommendation && (
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-semibold ${getRecommendationColor(
                                msg.metadata.recommendation
                              )} text-white`}
                            >
                              {msg.metadata.recommendation}
                            </span>
                            {msg.metadata.confidence && (
                              <span className="text-xs text-gray-400">
                                {msg.metadata.confidence.toFixed(0)}% confidence
                              </span>
                            )}
                            {msg.metadata.language && (
                              <span className="text-xs">
                                {msg.metadata.language === 'fa' ? '🇫🇦' : '🇬🇧'}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Analysis summary */}
                        {msg.metadata.analysis_summary && (
                          <div className="text-xs text-gray-400 space-y-1">
                            <div className="flex gap-3">
                              <span>Trend: <span className="text-white">{msg.metadata.analysis_summary.trend}</span></span>
                              <span>Score: <span className="text-white">{msg.metadata.analysis_summary.technical_score}</span></span>
                            </div>
                          </div>
                        )}

                        {/* Risk factors */}
                        {msg.metadata.risk_factors && msg.metadata.risk_factors.length > 0 && (
                          <div className="text-xs">
                            <span className="text-gray-500">Risks:</span>
                            <div className="text-gray-400 mt-1">
                              {msg.metadata.risk_factors.slice(0, 3).map((r: string, i: number) => (
                                <div key={i}>⚠ {r}</div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Key levels */}
                        {msg.metadata.key_levels && Object.keys(msg.metadata.key_levels).length > 0 && (
                          <div className="text-xs text-gray-400 flex gap-3">
                            {msg.metadata.key_levels.support && <span>Support: <span className="text-green-400">${msg.metadata.key_levels.support}</span></span>}
                            {msg.metadata.key_levels.resistance && <span>Resistance: <span className="text-red-400">${msg.metadata.key_levels.resistance}</span></span>}
                          </div>
                        )}

                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          {msg.metadata.model_used && <span>via {msg.metadata.model_used}</span>}
                          {msg.metadata.execution_time_ms && <span>• {msg.metadata.execution_time_ms}ms</span>}
                        </div>
                      </div>
                    )}

                    <div className="text-xs text-gray-400 mt-1">
                      {formatTime(msg.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                    </div>
                    <span className="text-xs text-gray-500">
                      {language === 'fa' ? 'در حال تایپ...' : 'Thinking...'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-700 flex-shrink-0">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={getPlaceholder()}
                className="flex-1 bg-gray-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={isLoading}
                dir="auto"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isLoading || !inputValue.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg disabled:opacity-50 text-sm font-medium"
              >
                {isLoading ? '...' : (language === 'fa' ? 'ارسال' : 'Send')}
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-center">
              {messages.length > 0 && (
                <span>{messages.length} messages • {language === 'fa' ? 'تاریخچه ذخیره شده' : 'History saved'}</span>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;

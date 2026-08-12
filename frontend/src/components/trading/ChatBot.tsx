import React, { useState, useRef, useEffect } from 'react';
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
  };
}

export const ChatBot: React.FC = () => {
  const { selectedSymbol } = useWatchlist();
  const { t } = useLanguage();
  const { selectedModel } = useSettings();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const suggestedQuestions = [
    t('chatbot.shouldIBuy'),
    t('chatbot.goodTimeToSell'),
    t('chatbot.whatsTheTrend'),
  ];

  const handleSendMessage = async (question?: string) => {
    const text = question || inputValue.trim();
    if (!text) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await apiFetch('/skills/chat/', {
        method: 'POST',
        body: JSON.stringify({
          symbol: selectedSymbol.replace('USDT', ''),
          question: text,
          model: selectedModel,  // Send the selected model
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        metadata: {
          confidence: data.confidence,
          recommendation: data.recommendation,
          model_used: data.model_used,
          execution_time_ms: data.execution_time_ms,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: t('common.error'),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec?.toUpperCase()) {
      case 'BUY':
        return 'bg-green-500';
      case 'SELL':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full shadow-lg flex items-center justify-center text-white text-2xl hover:scale-110 transition-transform z-50"
      >
        💬
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-gray-800 rounded-xl shadow-2xl border border-gray-700 flex flex-col z-50">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 rounded-t-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{t('chatbot.title')}</h3>
                <div className="text-xs text-blue-200">
                  ● {t('chatbot.online')} • {selectedSymbol.replace('USDT', '')} • {selectedModel}
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/80 hover:text-white"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-400 mt-8">
                <div className="text-4xl mb-4">🤖</div>
                <p>{t('chatbot.title')}</p>
                <p className="text-sm mt-2">{t('chatbot.placeholder').replace('{symbol}', selectedSymbol.replace('USDT', ''))}</p>
                <p className="text-xs mt-1 text-gray-500">Model: {selectedModel}</p>
                
                <div className="mt-4 space-y-2">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(q)}
                      className="block w-full text-left px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
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
                    className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    
                    {msg.metadata && (
                      <div className="mt-2 pt-2 border-t border-gray-600 flex items-center gap-2 text-xs">
                        {msg.metadata.recommendation && (
                          <span
                            className={`px-2 py-0.5 rounded ${getRecommendationColor(
                              msg.metadata.recommendation
                            )} text-white font-semibold`}
                          >
                            {msg.metadata.recommendation}
                          </span>
                        )}
                        {msg.metadata.confidence && (
                          <span className="text-gray-400">
                            {(msg.metadata.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                        {msg.metadata.model_used && (
                          <span className="text-gray-500">
                            via {msg.metadata.model_used}
                          </span>
                        )}
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-400 mt-1">
                      {msg.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-700 rounded-lg p-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder={t('chatbot.placeholder').replace('{symbol}', selectedSymbol.replace('USDT', ''))}
                className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isLoading || !inputValue.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {t('chatbot.send')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

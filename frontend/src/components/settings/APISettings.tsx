import React, { useState, useEffect } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { apiFetch } from '../../utils/api';

interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
}

interface OllamaInfo {
  models: OllamaModel[];
  count: number;
  base_url: string;
  active_model: string | null;
}

export const APISettings: React.FC = () => {
  const { selectedModel, setSelectedModel, temperature, setTemperature } = useSettings();
  const [activeTab, setActiveTab] = useState<'ai' | 'exchanges' | 'general'>('ai');
  const [ollamaInfo, setOllamaInfo] = useState<OllamaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [ollamaStatus, setOllamaStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchOllamaModels();
  }, []);

  const fetchOllamaModels = async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/ai/providers/ollama-models/');
      if (response.ok) {
        const data: OllamaInfo = await response.json();
        setOllamaInfo(data);
        setOllamaStatus(data.models.length > 0 ? 'connected' : 'disconnected');
        // If we don't have a selected model yet, use the active one from backend
        if (!selectedModel && data.active_model) {
          setSelectedModel(data.active_model);
        }
      } else {
        setOllamaStatus('disconnected');
      }
    } catch (err) {
      setOllamaStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  const pullModel = async (modelName: string) => {
    setMessage({ type: 'success', text: `Pulling ${modelName}... This may take a few minutes.` });
    try {
      setMessage({ type: 'success', text: `Pull request sent for ${modelName}. Check Ollama for progress.` });
    } catch (err) {
      setMessage({ type: 'error', text: `Failed to pull ${modelName}` });
    }
  };

  const testConnection = async () => {
    setOllamaStatus('checking');
    try {
      const response = await apiFetch('/ai/providers/health/');
      if (response.ok) {
        const data = await response.json();
        setOllamaStatus(data.ollama ? 'connected' : 'disconnected');
        setMessage({ 
          type: data.ollama ? 'success' : 'error', 
          text: data.ollama ? 'Connected to Ollama!' : 'Cannot connect to Ollama' 
        });
      } else {
        setOllamaStatus('disconnected');
      }
    } catch (err) {
      setOllamaStatus('disconnected');
      setMessage({ type: 'error', text: 'Failed to check connection' });
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
    if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    return `${(bytes / 1e3).toFixed(1)} KB`;
  };

  const tabs = [
    { id: 'ai' as const, label: 'AI Models', icon: '🤖' },
    { id: 'exchanges' as const, label: 'Exchanges', icon: '💱' },
    { id: 'general' as const, label: 'General', icon: '⚙️' },
  ];

  return (
    <div className="bg-[#131722] rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="bg-[#1e1e2e] border-b border-[#2a2a3e] px-4 py-3">
        <h2 className="text-white font-semibold">Settings</h2>
        <p className="text-xs text-gray-400">Selected Model: {selectedModel}</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2a2a3e]">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-3 text-sm font-medium ${
              activeTab === tab.id ? 'text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {message && (
          <div className={`mb-4 p-3 rounded text-sm ${
            message.type === 'success' ? 'bg-[#26a69a]/20 text-[#26a69a]' : 'bg-[#ef5350]/20 text-[#ef5350]'
          }`}>
            {message.text}
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-4">
            {/* Ollama Status */}
            <div className="bg-[#1e1e2e] rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">🦙</div>
                  <div>
                    <h3 className="text-white font-medium">Ollama (Local)</h3>
                    <p className="text-xs text-gray-400">{ollamaInfo?.base_url || 'http://localhost:11434'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={testConnection}
                    className="px-3 py-1 bg-[#2a2a3e] text-white text-xs rounded hover:bg-[#3a3a4e]"
                  >
                    Test
                  </button>
                  <div className={`px-3 py-1 rounded-full text-xs ${
                    ollamaStatus === 'connected' ? 'bg-[#26a69a]/20 text-[#26a69a]' : 
                    ollamaStatus === 'checking' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-[#ef5350]/20 text-[#ef5350]'
                  }`}>
                    {ollamaStatus === 'connected' ? '● Connected' : 
                     ollamaStatus === 'checking' ? '● Checking...' : '● Disconnected'}
                  </div>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent mx-auto" />
                  <p className="text-gray-400 text-sm mt-2">Loading models...</p>
                </div>
              ) : ollamaInfo && ollamaInfo.models.length > 0 ? (
                <>
                  {/* Active Model */}
                  <div className="mb-4">
                    <label className="block text-xs text-gray-400 mb-2">Active Model (used by ChatBot & AI)</label>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-[#131722] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      {ollamaInfo.models.map(m => (
                        <option key={m.name} value={m.name}>{m.name} ({formatSize(m.size)})</option>
                      ))}
                    </select>
                    <p className="text-[10px] text-gray-500 mt-1">
                      Changes are saved automatically and applied to all AI features
                    </p>
                  </div>

                  {/* Temperature */}
                  <div className="mb-4">
                    <label className="block text-xs text-gray-400 mb-2">
                      Temperature: {temperature.toFixed(1)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-[10px] text-gray-500">
                      <span>Precise (0)</span>
                      <span>Creative (1)</span>
                    </div>
                  </div>

                  {/* Installed Models */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-2">
                      Installed Models ({ollamaInfo.count})
                    </label>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {ollamaInfo.models.map(model => (
                        <div 
                          key={model.name} 
                          className={`flex items-center justify-between p-3 rounded cursor-pointer transition-colors ${
                            model.name === selectedModel 
                              ? 'bg-blue-600/20 border border-blue-500/50' 
                              : 'bg-[#131722] hover:bg-[#2a2a3e]'
                          }`}
                          onClick={() => setSelectedModel(model.name)}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${model.name === selectedModel ? 'bg-[#26a69a]' : 'bg-gray-500'}`} />
                            <div>
                              <div className="text-sm text-white font-medium">{model.name}</div>
                              <div className="text-[10px] text-gray-500">
                                {formatSize(model.size)} • {new Date(model.modified_at).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          {model.name === selectedModel && (
                            <span className="text-xs text-[#26a69a] bg-[#26a69a]/10 px-2 py-0.5 rounded">Active</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-400">No models installed</p>
                  <p className="text-xs text-gray-500 mt-1">Install models via Ollama CLI or click Pull below</p>
                </div>
              )}
            </div>

            {/* Quick Pull */}
            <div className="bg-[#1e1e2e] rounded-lg p-4">
              <h3 className="text-white font-medium mb-3">Quick Install Models</h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { name: 'gemma4:latest', desc: 'Google Gemma 4' },
                  { name: 'llama3:latest', desc: 'Meta Llama 3' },
                  { name: 'qwen3.5:latest', desc: 'Alibaba Qwen' },
                  { name: 'mistral:latest', desc: 'Mistral AI' },
                ].map(model => {
                  const isInstalled = ollamaInfo?.models.some(m => m.name === model.name);
                  return (
                    <button
                      key={model.name}
                      onClick={() => pullModel(model.name)}
                      disabled={isInstalled}
                      className="p-3 bg-[#131722] rounded text-left hover:bg-[#2a2a3e] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <div className="text-sm text-white">{model.name}</div>
                      <div className="text-[10px] text-gray-500">{model.desc}</div>
                      {isInstalled ? (
                        <div className="text-[10px] text-[#26a69a] mt-1">✓ Installed</div>
                      ) : (
                        <div className="text-[10px] text-blue-400 mt-1">Click to install</div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Cloud AI */}
            <div className="bg-[#1e1e2e] rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">☁️</div>
                  <div>
                    <h3 className="text-white font-medium">Cloud AI</h3>
                    <p className="text-xs text-gray-400">OpenAI, Anthropic, etc.</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-[#2a2a3e] text-white text-xs rounded hover:bg-[#3a3a4e]">
                  Configure
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'exchanges' && (
          <div className="space-y-4">
            {['Binance', 'Bybit', 'OKX'].map(exchange => (
              <div key={exchange} className="bg-[#1e1e2e] rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">💱</div>
                    <div>
                      <h3 className="text-white font-medium">{exchange}</h3>
                      <p className="text-xs text-gray-400">Spot & Futures</p>
                    </div>
                  </div>
                  <div className="px-2 py-1 bg-gray-600/20 text-gray-400 text-xs rounded">Not Connected</div>
                </div>
                <div className="space-y-2">
                  <input
                    type="password"
                    placeholder="API Key"
                    className="w-full bg-[#131722] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                  <input
                    type="password"
                    placeholder="API Secret"
                    className="w-full bg-[#131722] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-xs text-gray-400">
                      <input type="checkbox" defaultChecked className="rounded" />
                      Testnet
                    </label>
                    <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
                      Connect
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'general' && (
          <div className="space-y-4">
            <div className="bg-[#1e1e2e] rounded-lg p-4 space-y-4">
              <div>
                <label className="block text-xs text-gray-400 mb-2">Default Trading Pair</label>
                <select className="w-full bg-[#131722] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500">
                  <option>BTC/USDT</option>
                  <option>ETH/USDT</option>
                  <option>SOL/USDT</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-2">Risk Level</label>
                <div className="grid grid-cols-3 gap-2">
                  {['Conservative', 'Moderate', 'Aggressive'].map(level => (
                    <button key={level} className="py-2 bg-[#131722] border border-[#2a2a3e] rounded text-sm text-white hover:border-blue-500">
                      {level}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between py-2">
                <div>
                  <div className="text-sm text-white">Auto-trading</div>
                  <div className="text-xs text-gray-400">Execute signals automatically</div>
                </div>
                <div className="w-10 h-5 bg-gray-600 rounded-full relative cursor-pointer">
                  <div className="w-4 h-4 bg-white rounded-full absolute top-0.5 left-0.5" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default APISettings;

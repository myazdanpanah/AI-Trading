import React, { useState, useEffect } from 'react';

interface OllamaModel {
  name: string;
  size: number;
  modified: string;
}

export const APISettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ai' | 'exchanges' | 'general'>('ai');
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [pullingModel, setPullingModel] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('gemma2:latest');
  const [ollamaStatus, setOllamaStatus] = useState<'connected' | 'disconnected'>('connected');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    // Mock Ollama models
    setOllamaModels([
      { name: 'gemma2:latest', size: 5.4e9, modified: '2 hours ago' },
      { name: 'llama3.1:latest', size: 4.7e9, modified: '1 day ago' },
      { name: 'mistral:latest', size: 4.1e9, modified: '3 days ago' },
      { name: 'codellama:latest', size: 3.8e9, modified: '1 week ago' },
      { name: 'phi3:latest', size: 2.2e9, modified: '2 weeks ago' },
      { name: 'qwen2:latest', size: 4.4e9, modified: '1 week ago' },
    ]);
  }, []);

  const pullModel = async (modelName: string) => {
    setPullingModel(modelName);
    setMessage({ type: 'success', text: `Pulling ${modelName}... This may take a few minutes.` });
    
    // Simulate pull
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    if (!ollamaModels.find(m => m.name === modelName)) {
      setOllamaModels(prev => [...prev, {
        name: modelName,
        size: 5e9,
        modified: 'Just now',
      }]);
    }
    
    setPullingModel(null);
    setMessage({ type: 'success', text: `${modelName} pulled successfully!` });
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
                    <p className="text-xs text-gray-400">Run AI models locally</p>
                  </div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs ${
                  ollamaStatus === 'connected' ? 'bg-[#26a69a]/20 text-[#26a69a]' : 'bg-[#ef5350]/20 text-[#ef5350]'
                }`}>
                  {ollamaStatus === 'connected' ? '● Connected' : '● Disconnected'}
                </div>
              </div>
              
              {/* Model selector */}
              <div className="mb-4">
                <label className="block text-xs text-gray-400 mb-2">Active Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-[#131722] border border-[#2a2a3e] rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  {ollamaModels.map(m => (
                    <option key={m.name} value={m.name}>{m.name} ({formatSize(m.size)})</option>
                  ))}
                </select>
              </div>
              
              {/* Installed models */}
              <div>
                <label className="block text-xs text-gray-400 mb-2">Installed Models</label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {ollamaModels.map(model => (
                    <div key={model.name} className="flex items-center justify-between p-2 bg-[#131722] rounded">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${model.name === selectedModel ? 'bg-[#26a69a]' : 'bg-gray-500'}`} />
                        <div>
                          <div className="text-sm text-white">{model.name}</div>
                          <div className="text-[10px] text-gray-500">{formatSize(model.size)} • {model.modified}</div>
                        </div>
                      </div>
                      {model.name === selectedModel && (
                        <span className="text-xs text-[#26a69a]">Active</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Pull new model */}
            <div className="bg-[#1e1e2e] rounded-lg p-4">
              <h3 className="text-white font-medium mb-3">Pull New Model</h3>
              <div className="grid grid-cols-2 gap-2">
                {['gemma2:latest', 'llama3.1:latest', 'mistral:latest', 'codellama:latest', 'phi3:latest', 'qwen2:latest'].map(model => (
                  <button
                    key={model}
                    onClick={() => pullModel(model)}
                    disabled={pullingModel === model || ollamaModels.find(m => m.name === model)}
                    className="p-2 bg-[#131722] rounded text-left hover:bg-[#2a2a3e] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <div className="text-sm text-white">{model}</div>
                    {pullingModel === model ? (
                      <div className="text-[10px] text-blue-400">Pulling...</div>
                    ) : ollamaModels.find(m => m.name === model) ? (
                      <div className="text-[10px] text-[#26a69a]">Installed</div>
                    ) : (
                      <div className="text-[10px] text-gray-500">Click to pull</div>
                    )}
                  </button>
                ))}
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

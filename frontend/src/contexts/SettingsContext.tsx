import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SettingsContextType {
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  ollamaUrl: string;
  setOllamaUrl: (url: string) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

const DEFAULT_SETTINGS = {
  selectedModel: 'gemma4:latest',
  ollamaUrl: 'http://localhost:11434',
  temperature: 0.7,
};

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedModel, setSelectedModel] = useState(() => {
    return localStorage.getItem('selected_model') || DEFAULT_SETTINGS.selectedModel;
  });
  const [ollamaUrl, setOllamaUrl] = useState(() => {
    return localStorage.getItem('ollama_url') || DEFAULT_SETTINGS.ollamaUrl;
  });
  const [temperature, setTemperature] = useState(() => {
    const saved = localStorage.getItem('temperature');
    return saved ? parseFloat(saved) : DEFAULT_SETTINGS.temperature;
  });

  useEffect(() => {
    localStorage.setItem('selected_model', selectedModel);
  }, [selectedModel]);

  useEffect(() => {
    localStorage.setItem('ollama_url', ollamaUrl);
  }, [ollamaUrl]);

  useEffect(() => {
    localStorage.setItem('temperature', temperature.toString());
  }, [temperature]);

  return (
    <SettingsContext.Provider value={{
      selectedModel,
      setSelectedModel,
      ollamaUrl,
      setOllamaUrl,
      temperature,
      setTemperature,
    }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

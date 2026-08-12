export type Language = 'en' | 'fa';

export interface Translations {
  // Navigation
  trading: string;
  signals: string;
  journal: string;
  feedback: string;
  analysis: string;
  backtest: string;
  news: string;
  settings: string;
  profile: string;
  logout: string;
  live: string;
  
  // Trading
  watchlist: string;
  orderBook: string;
  portfolio: string;
  hide: string;
  show: string;
  manage: string;
  search: string;
  
  // Signals
  signalDashboard: string;
  finalSignal: string;
  combined: string;
  regime: string;
  technical: string;
  exposurePosture: string;
  maxExposure: string;
  historicalPerformance: string;
  winRate: string;
  totalSignals: string;
  scoreAdj: string;
  fiveFactorAnalysis: string;
  regimeAnalyzer: string;
  technicalAnalysis: string;
  positionSizer: string;
  entryPrice: string;
  stopLoss: string;
  takeProfit: string;
  positionSize: string;
  positionValue: string;
  riskReward: string;
  risk: string;
  account: string;
  
  // Analysis
  regimeScore: string;
  technicalScore: string;
  signal: string;
  rsi: string;
  period: string;
  priceChart: string;
  performance: string;
  factors: string;
  regimeComponents: string;
  trend: string;
  momentum: string;
  volatility: string;
  overall: string;
  vwap: string;
  ichimoku: string;
  cloud: string;
  
  // Feedback
  learningInsights: string;
  insights: string;
  recommendations: string;
  memory: string;
  cycles: string;
  adjustWeights: string;
  runCycle: string;
  
  // Journal
  journalEntries: string;
  generateEntry: string;
  marketAnalysis: string;
  signalReview: string;
  newsDigest: string;
  technicalReview: string;
  dailySummary: string;
  lessonsLearned: string;
  
  // News
  newsSources: string;
  addSource: string;
  loadDefaults: string;
  sourceName: string;
  sourceUrl: string;
  category: string;
  reliability: string;
  
  // Settings
  ollamaLocal: string;
  connected: string;
  disconnected: string;
  activeModel: string;
  installedModels: string;
  pullModel: string;
  exchanges: string;
  general: string;
  defaultPair: string;
  riskLevel: string;
  conservative: string;
  moderate: string;
  aggressive: string;
  autoTrading: string;
  
  // Common
  buy: string;
  sell: string;
  hold: string;
  loading: string;
  error: string;
  retry: string;
  save: string;
  cancel: string;
  delete: string;
  edit: string;
  add: string;
  remove: string;
  close: string;
  open: string;
  yes: string;
  no: string;
  confirm: string;
  success: string;
  failed: string;
  analyzing: string;
  generatedBy: string;
  dataPoints: string;
  source: string;
  executionTime: string;
  
  // Chatbot
  tradingAI: string;
  askAbout: string;
  recommend: string;
  confidence: string;
  suggestedQuestions: string;
  shouldIBuy: string;
  goodTimeToSell: string;
  whatsTheTrend: string;
  analyzeSymbol: string;
  shouldIHold: string;
  
  // Direction
  bullish: string;
  bearish: string;
  neutral: string;
  strongBuy: string;
  strongSell: string;
  
  // Regime zones
  riskOn: string;
  riskOff: string;
  unknown: string;
}

export const translations: Record<Language, Translations> = {
  en: {
    // Navigation
    trading: 'Trading',
    signals: 'Signals',
    journal: 'Journal',
    feedback: 'Feedback',
    analysis: 'Analysis',
    backtest: 'Backtest',
    news: 'News',
    settings: 'Settings',
    profile: 'Profile',
    logout: 'Logout',
    live: 'Live',
    
    // Trading
    watchlist: 'Watchlist',
    orderBook: 'Order Book',
    portfolio: 'Portfolio',
    hide: 'Hide',
    show: 'Show',
    manage: 'Manage',
    search: 'Search',
    
    // Signals
    signalDashboard: 'Signal Analysis Dashboard',
    finalSignal: 'FINAL SIGNAL',
    combined: 'Combined',
    regime: 'Regime',
    technical: 'Technical',
    exposurePosture: 'EXPOSURE POSTURE',
    maxExposure: 'Max Exposure',
    historicalPerformance: 'Historical Performance Feedback',
    winRate: 'Win Rate',
    totalSignals: 'Total Signals',
    scoreAdj: 'Score Adj',
    fiveFactorAnalysis: '5-Factor Analysis',
    regimeAnalyzer: 'Regime Analyzer',
    technicalAnalysis: 'Technical Analysis',
    positionSizer: 'Position Sizer',
    entryPrice: 'Entry Price',
    stopLoss: 'Stop Loss',
    takeProfit: 'Take Profit',
    positionSize: 'Position Size',
    positionValue: 'Position Value',
    riskReward: 'R:R Ratio',
    risk: 'Risk',
    account: 'Account',
    
    // Analysis
    regimeScore: 'Regime Score',
    technicalScore: 'Technical Score',
    signal: 'Signal',
    rsi: 'RSI',
    period: 'Period',
    priceChart: 'Price Chart',
    performance: 'Performance',
    factors: 'Factors',
    regimeComponents: 'Regime Components',
    trend: 'Trend',
    momentum: 'Momentum',
    volatility: 'Volatility',
    overall: 'Overall',
    vwap: 'VWAP',
    ichimoku: 'Ichimoku',
    cloud: 'Cloud',
    
    // Feedback
    learningInsights: 'Learning Insights',
    insights: 'Insights',
    recommendations: 'Recommendations',
    memory: 'Memory',
    cycles: 'Cycles',
    adjustWeights: 'Adjust Weights',
    runCycle: 'Run Cycle',
    
    // Journal
    journalEntries: 'Journal Entries',
    generateEntry: 'Generate Entry',
    marketAnalysis: 'Market Analysis',
    signalReview: 'Signal Review',
    newsDigest: 'News Digest',
    technicalReview: 'Technical Review',
    dailySummary: 'Daily Summary',
    lessonsLearned: 'Lessons Learned',
    
    // News
    newsSources: 'News Sources',
    addSource: 'Add Source',
    loadDefaults: 'Load Defaults',
    sourceName: 'Source Name',
    sourceUrl: 'Source URL',
    category: 'Category',
    reliability: 'Reliability',
    
    // Settings
    ollamaLocal: 'Ollama (Local)',
    connected: 'Connected',
    disconnected: 'Disconnected',
    activeModel: 'Active Model',
    installedModels: 'Installed Models',
    pullModel: 'Pull Model',
    exchanges: 'Exchanges',
    general: 'General',
    defaultPair: 'Default Trading Pair',
    riskLevel: 'Risk Level',
    conservative: 'Conservative',
    moderate: 'Moderate',
    aggressive: 'Aggressive',
    autoTrading: 'Auto-trading',
    
    // Common
    buy: 'BUY',
    sell: 'SELL',
    hold: 'HOLD',
    loading: 'Loading',
    error: 'Error',
    retry: 'Retry',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    remove: 'Remove',
    close: 'Close',
    open: 'Open',
    yes: 'Yes',
    no: 'No',
    confirm: 'Confirm',
    success: 'Success',
    failed: 'Failed',
    analyzing: 'Analyzing',
    generatedBy: 'Generated by',
    dataPoints: 'data points',
    source: 'Source',
    executionTime: 'Execution time',
    
    // Chatbot
    tradingAI: 'Trading AI',
    askAbout: 'Ask about',
    recommend: 'Recommend',
    confidence: 'Confidence',
    suggestedQuestions: 'Suggested questions',
    shouldIBuy: 'Should I buy now?',
    goodTimeToSell: 'Is it a good time to sell?',
    whatsTheTrend: "What's the trend?",
    analyzeSymbol: 'Analyze this symbol',
    shouldIHold: 'Should I hold?',
    
    // Direction
    bullish: 'Bullish',
    bearish: 'Bearish',
    neutral: 'Neutral',
    strongBuy: 'STRONG BUY',
    strongSell: 'STRONG SELL',
    
    // Regime zones
    riskOn: 'RISK ON',
    riskOff: 'RISK OFF',
    unknown: 'UNKNOWN',
  },
  
  fa: {
    // Navigation
    trading: '\u062a\u0631\u0627\u062f',
    signals: '\u0633\u06cc\u06af\u0646\u0627\u0644\u200c\u0647\u0627',
    journal: '\u062f\u0648\u0646\u0628\u0633\u062a',
    feedback: '\u0628\u0627\u0632\u062e\u0634',
    analysis: '\u062a\u062d\u0644\u06cc\u0644',
    backtest: '\u0622\u0632\u0645\u0627\u06cc\u0634',
    news: '\u0627\u062e\u0628\u0627\u0631',
    settings: '\u062a\u0646\u0638\u06cc\u0645\u0627\u062a',
    profile: '\u067e\u0631\u0648\u0641\u0627\u06cc\u0644',
    logout: '\u062e\u0631\u0648\u062c',
    live: '\u0632\u0646\u062f\u0647',
    
    // Trading
    watchlist: '\u0644\u06cc\u0633\u062a \u062a\u0647\u0631\u0636\u0639\u0627\u062a',
    orderBook: '\u062f\u0641\u062a\u0631\u0633 \u0633\u0641\u0627\u0631\u0634\u0627\u062a',
    portfolio: '\u0635\u0641\u062d\u0647 \u062e\u0631\u0648\u062c',
    hide: '\u0645\u0634\u0631\u0648\u0641',
    show: '\u0646\u0645\u0627\u06cc\u0634',
    manage: '\u0645\u062f\u06cc\u0631\u06cc\u062a',
    search: '\u062c\u0633\u062a\u062c\u0648',
    
    // Signals
    signalDashboard: '\u062f\u0634\u0628\u0631\u062f \u062a\u062d\u0644\u06cc\u0644 \u0633\u06cc\u06af\u0646\u0627\u0644',
    finalSignal: '\u0633\u06cc\u06af\u0646\u0627\u0644 \u0646\u0647\u0627\u06cc\u06cc',
    combined: '\u062a\u0631\u06a9\u06cc\u0628\u06cc',
    regime: '\u0631\u0648\u0632\u0647',
    technical: '\u0641\u0646\u06cc',
    exposurePosture: '\u0648\u0636\u0639\u06cc\u062a \u0627\u0639\u0645\u0627\u0644',
    maxExposure: '\u062d\u062f\u0627\u06a9\u062b\u0631 \u0627\u0639\u0645\u0627\u0644',
    historicalPerformance: '\u0628\u0627\u0632\u062e\u0634 \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u06af\u0630\u0634\u062a\u0647',
    winRate: '\u0646\u0631\u062e \u0628\u0631\u062f',
    totalSignals: '\u06a9\u0644 \u0633\u06cc\u06af\u0646\u0627\u0644\u200c\u0647\u0627',
    scoreAdj: '\u062a\u0635\u062d\u06cc\u062d \u0627\u0645\u062a\u06cc\u0627\u0632',
    fiveFactorAnalysis: '\u062a\u062d\u0644\u06cc\u0644 \u067e\u0646\u062c\u0631\u0647\u200c\u0627\u06cc',
    regimeAnalyzer: '\u062a\u062d\u0644\u06cc\u0644\u06af\u0631 \u0631\u0648\u0632\u0647',
    technicalAnalysis: '\u062a\u062d\u0644\u06cc\u0644 \u0641\u0646\u06cc',
    positionSizer: '\u0627\u0646\u062f\u0627\u0632\u0647 \u0645\u0648\u0642\u0639\u06cc\u062a',
    entryPrice: '\u0642\u06cc\u0645\u062a \u0648\u0631\u0648\u062f',
    stopLoss: '\u0633\u0648\u062f \u0644\u0648\u0633',
    takeProfit: '\u062d\u062f \u0633\u0648\u062f',
    positionSize: '\u062d\u062c\u0645 \u0645\u0648\u0642\u0639\u06cc\u062a',
    positionValue: '\u0627\u0631\u0632\u0634 \u0645\u0648\u0642\u0639\u06cc\u062a',
    riskReward: '\u0646\u0633\u0628\u062a \u0628\u0647 \u0631\u06cc\u0633\u06a9',
    risk: '\u0631\u06cc\u0633\u06a9',
    account: '\u062d\u0633\u0627\u0628',
    
    // Analysis
    regimeScore: '\u0627\u0645\u062a\u06cc\u0627\u0632 \u0631\u0648\u0632\u0647',
    technicalScore: '\u0627\u0645\u062a\u06cc\u0627\u0632 \u0641\u0646\u06cc',
    signal: '\u0633\u06cc\u06af\u0646\u0627\u0644',
    rsi: '\u0634\u0627\u063a\u0636\u06cc \u0646\u0633\u0628\u062a\u06cc',
    period: '\u0627\u0635\u0644',
    priceChart: '\u0646\u0645\u0648\u062f\u0627\u0631 \u0642\u06cc\u0645\u062a',
    performance: '\u0627\u0639\u062a\u0645\u0627\u062f',
    factors: '\u0639\u0648\u0627\u0645\u0644',
    regimeComponents: '\u0627\u0639\u0635\u0627\u0626\u0631 \u0631\u0648\u0632\u0647',
    trend: '\u0631\u0648\u0646\u062f',
    momentum: '\u062a\u0634\u0631\u0639',
    volatility: '\u0646\u0648\u0633\u0627\u0646',
    overall: '\u06a9\u0644\u06cc',
    vwap: '\u0642\u06cc\u0645\u062a \u0645\u062a\u0648\u0636\u0639 \u062d\u062c\u0645',
    ichimoku: '\u0627\u06cc\u0686\u06cc\u0645\u0648\u06a9\u0648',
    cloud: '\u0627\u0628\u0631',
    
    // Feedback
    learningInsights: '\u0628\u0631\u0635\u062f \u06cc\u0627\u062f\u06af\u0631\u06cc',
    insights: '\u0628\u0631\u0635\u062f\u0647\u0627',
    recommendations: '\u06a9\u0645\u06a9\u0647\u0627',
    memory: '\u062d\u0627\u0641\u0638\u0647',
    cycles: '\u0698\u0631\u0646\u0647\u200c\u0647\u0627',
    adjustWeights: '\u062a\u0635\u062d\u06cc\u062d \u0630\u0648\u0646',
    runCycle: '\u0627\u062c\u0631\u0627\u06cc \u0698\u0631\u0646\u0647',
    
    // Journal
    journalEntries: '\u0622\u062e\u0631\u06cc\u0646 \u0627\u0637\u0644\u0627\u0639\u0627\u062a',
    generateEntry: '\u0627\u06cc\u062c\u0627\u062f \u0627\u0637\u0644\u0627\u0639\u0647',
    marketAnalysis: '\u062a\u062d\u0644\u06cc\u0644 \u0628\u0627\u0632\u0627\u0631',
    signalReview: '\u0628\u0627\u0631\u0633\u06cc \u0633\u06cc\u06af\u0646\u0627\u0644',
    newsDigest: '\u062e\u0631\u062f\u0633\u0637 \u0627\u062e\u0628\u0627\u0631',
    technicalReview: '\u0628\u0627\u0631\u0633\u06cc \u0641\u0646\u06cc',
    dailySummary: '\u062e\u0644\u0635\u0647 \u0631\u0648\u0632\u0627\u0646\u0647',
    lessonsLearned: '\u062f\u0631\u0633 \u0647\u0627\u06cc \u0622\u0645\u0648\u0632\u062a\u0647',
    
    // News
    newsSources: '\u0645\u0646\u0627\u0628\u0639 \u0627\u062e\u0628\u0627\u0631',
    addSource: '\u0627\u0636\u0627\u0641\u0647 \u0645\u0646\u0628\u0639',
    loadDefaults: '\u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc',
    sourceName: '\u0646\u0627\u0645 \u0645\u0646\u0628\u0639',
    sourceUrl: '\u0644\u06cc\u0646\u06a9 \u0645\u0646\u0628\u0639',
    category: '\u062f\u0633\u062a\u0647',
    reliability: '\u0642\u0627\u0628\u0644\u06cc\u062a',
    
    // Settings
    ollamaLocal: '\u0627\u0648\u0644\u0627\u0645\u0627 (\u0645\u062d\u0644\u06cc)',
    connected: '\u0645\u062a\u0635\u0644',
    disconnected: '\u0642\u0637\u0639 \u0634\u062f\u0647',
    activeModel: '\u0645\u062f\u0644 \u0641\u0639\u0627\u0644',
    installedModels: '\u0645\u062f\u0644\u0647\u0627\u06cc \u0646\u0635\u0628',
    pullModel: '\u062f\u0646\u0644\u0648\u062f \u0645\u062f\u0644',
    exchanges: '\u0635\u0631\u0641\u0647\u200c\u062e\u0627\u0646\u0647\u200c\u0647\u0627',
    general: '\u0639\u0645\u0648\u0645\u06cc',
    defaultPair: '\u062c\u0641\u062a \u067e\u06cc\u0634\u0631\u0636 \u062a\u0631\u0627\u062f',
    riskLevel: '\u0633\u0637\u062d\u0647 \u0631\u06cc\u0633\u06a9',
    conservative: '\u0645\u062d\u0627\u0641\u0638\u0627\u0646\u0647',
    moderate: '\u0645\u062a\u0648\u0633\u0637',
    aggressive: '\u062a\u0647\u0632\u0631',
    autoTrading: '\u062a\u0631\u0627\u062f \u062e\u0648\u062f\u06a9\u0627\u0631',
    
    // Common
    buy: '\u062e\u0631\u06cc\u062f',
    sell: '\u0641\u0631\u0648\u0634',
    hold: '\u0646\u06af\u0647 \u062f\u0627\u0634\u062a\u0646',
    loading: '\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc',
    error: '\u062e\u0637\u0627',
    retry: '\u062a\u0644\u0627\u0634 \u0645\u062c\u062f\u0648',
    save: '\u0630\u062e\u06cc\u0631\u0647 \u06a9\u0631\u062f\u0646',
    cancel: '\u0644\u063a\u0648',
    delete: '\u062d\u0630\u0641',
    edit: '\u0648\u06cc\u0631\u0627\u06cc\u0634',
    add: '\u0627\u0636\u0627\u0641\u0647',
    remove: '\u062d\u0630\u0641',
    close: '\u0628\u0633\u062a\u0646',
    open: '\u0628\u0627\u0632',
    yes: '\u0628\u0644\u0647',
    no: '\u062e\u06cc\u0631',
    confirm: '\u062a\u0623\u06a9\u06cc\u062f',
    success: '\u0645\u0648\u0641\u0642\u06cc\u062a',
    failed: '\u0646\u0627\u0645\u0648\u0641\u0642',
    analyzing: '\u062a\u062d\u0644\u06cc\u0644',
    generatedBy: '\u062a\u0648\u0633\u0637 \u0628\u062f\u0647',
    dataPoints: '\u0646\u0642\u0637\u0647 \u062f\u0627\u062f\u0647',
    source: '\u0645\u0646\u0628\u0639',
    executionTime: '\u0632\u0645\u0627\u0646 \u0627\u062c\u0631\u0627',
    
    // Chatbot
    tradingAI: '\u0647\u0634\u0648\u0627\u0631 \u062a\u0631\u0627\u062f',
    askAbout: '\u0628\u067e\u0631\u0633\u0631\u0648 \u062f\u0631\u0628\u0627\u0631\u0647',
    recommend: '\u062a\u0648\u0635\u06cc\u0647',
    confidence: '\u0627\u0637\u0645\u06cc\u0646\u0627\u0646',
    suggestedQuestions: '\u0633\u0648\u0627\u0644\u0627\u062a \u067e\u06cc\u0634\u0646\u0647\u0627\u0626\u06cc',
    shouldIBuy: '\u0622\u06cc\u0627 \u0628\u062e\u0631\u0645 \u062e\u0648\u062f\u0631\u0645\u061f',
    goodTimeToSell: '\u0632\u0645\u0627\u0646 \u062e\u0648\u0628 \u0641\u0631\u0648\u0634\u0633\u062a\u061f',
    whatsTheTrend: '\u0631\u0648\u0646\u062f \u0685\u0627\u0634 \u0628\u0627\u0631\u0627\u062e\u062a\u0631 \u0627\u0633\u062a\u061f',
    analyzeSymbol: '\u062a\u062d\u0644\u06cc\u0644 \u06a9\u0646\u06cc\u062f',
    shouldIHold: '\u0622\u06cc\u0627 \u0646\u06af\u0647 \u062f\u0627\u0634\u062a\u0646\u061f',
    
    // Direction
    bullish: '\u0635\u0639\u0648\u062f\u06cc',
    bearish: '\u0646\u0632\u0648\u0644\u06cc',
    neutral: '\u062e\u0646\u062b\u06cc',
    strongBuy: '\u062e\u0631\u06cc\u062f \u0642\u0648\u06cc',
    strongSell: '\u0641\u0631\u0648\u0634 \u0642\u0648\u06cc',
    
    // Regime zones
    riskOn: '\u0631\u06cc\u0633\u06a9 \u067e\u0630\u06cc\u0631\u0641\u062a\u0647',
    riskOff: '\u0631\u06cc\u0633\u06a9 \u06af\u0631\u06cc\u0632',
    unknown: '\u0646\u0627\u0634\u0646\u0627\u062e\u062a\u0647',
  },
};

export default translations;

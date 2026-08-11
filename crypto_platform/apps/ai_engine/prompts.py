"""Prompt versioning system."""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib


@dataclass
class PromptVersion:
    """A versioned prompt."""
    name: str
    version: str
    template: str
    description: str = ''
    author: str = 'system'
    model_compatibility: List[str] = field(default_factory=list)
    expected_schema: Optional[Dict] = None
    evaluation_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def hash(self) -> str:
        """Generate hash for deduplication."""
        content = f"{self.name}:{self.version}:{self.template}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def render(self, **kwargs) -> str:
        """Render prompt with variables."""
        return self.template.format(**kwargs)


class PromptLibrary:
    """Library of versioned prompts."""

    def __init__(self):
        self._prompts: Dict[str, List[PromptVersion]] = {}
        self._current_versions: Dict[str, str] = {}

    def register(self, prompt: PromptVersion):
        """Register a prompt version."""
        if prompt.name not in self._prompts:
            self._prompts[prompt.name] = []
        self._prompts[prompt.name].append(prompt)
        self._current_versions[prompt.name] = prompt.version

    def get(self, name: str, version: str = None) -> Optional[PromptVersion]:
        """Get a prompt by name and version."""
        if name not in self._prompts:
            return None

        if version is None:
            version = self._current_versions.get(name)

        for p in self._prompts[name]:
            if p.version == version:
                return p
        return None

    def get_current(self, name: str) -> Optional[PromptVersion]:
        """Get current version of a prompt."""
        return self.get(name)

    def list_prompts(self) -> List[Dict]:
        """List all prompts."""
        return [
            {
                'name': name,
                'current_version': self._current_versions.get(name),
                'versions': len(versions),
            }
            for name, versions in self._prompts.items()
        ]

    def set_current(self, name: str, version: str):
        """Set current version."""
        if name in self._prompts:
            self._current_versions[name] = version


# Global prompt library instance
prompt_library = PromptLibrary()


# Default prompts for the platform
DEFAULT_PROMPTS = {
    'market_analysis': {
        'name': 'market_analysis',
        'version': '1.0',
        'template': """You are a cryptocurrency market analyst. Analyze the following market data and provide insights.

Symbol: {symbol}
Current Price: {price}
24h Change: {change_24h}%
Volume: {volume}

Technical Indicators:
{indicators}

Provide:
1. Market trend assessment
2. Key support/resistance levels
3. Risk factors
4. Short-term outlook""",
        'description': 'Market analysis prompt',
        'model_compatibility': ['llama3', 'gpt-4o', 'claude-3-5-sonnet-20241022'],
    },
    'signal_generation': {
        'name': 'signal_generation',
        'version': '1.0',
        'template': """You are a crypto trading signal generator. Based on the following analysis, generate a trading signal.

Symbol: {symbol}
Technical Analysis:
{technical_analysis}

News Sentiment:
{news_sentiment}

Market Conditions:
{market_conditions}

Generate a signal with:
- Direction (BUY/SELL/HOLD)
- Confidence (0-100)
- Entry price suggestion
- Stop loss level
- Take profit levels
- Reasoning""",
        'description': 'Signal generation prompt',
        'model_compatibility': ['llama3', 'gpt-4o', 'claude-3-5-sonnet-20241022'],
    },
    'news_summary': {
        'name': 'news_summary',
        'version': '1.0',
        'template': """Summarize the following crypto news article and assess its market impact.

Title: {title}
Content: {content}

Provide:
1. Brief summary (2-3 sentences)
2. Sentiment (bullish/bearish/neutral)
3. Affected assets
4. Impact level (0-100)
5. Time horizon (short/medium/long)""",
        'description': 'News summary prompt',
        'model_compatibility': ['llama3', 'gpt-4o-mini', 'claude-3-5-haiku-20241022'],
    },
    'risk_analysis': {
        'name': 'risk_analysis',
        'version': '1.0',
        'template': """Analyze the risk factors for the following trading setup.

Symbol: {symbol}
Direction: {direction}
Entry: {entry_price}
Stop Loss: {stop_loss}
Take Profit: {take_profit}

Market Conditions:
{market_conditions}

Provide:
1. Risk score (0-100)
2. Key risk factors
3. Risk mitigation suggestions
4. Position sizing recommendation""",
        'description': 'Risk analysis prompt',
        'model_compatibility': ['llama3', 'gpt-4o', 'claude-3-5-sonnet-20241022'],
    },
}


# Register default prompts
for name, config in DEFAULT_PROMPTS.items():
    prompt_library.register(PromptVersion(**config))

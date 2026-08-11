"""Base AI provider interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIResponse:
    """Standardized AI response."""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: int = 0
    finish_reason: str = 'stop'
    metadata: Dict = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class PromptMessage:
    """Prompt message format."""
    role: str  # system, user, assistant
    content: str


class BaseProvider(ABC):
    """Base AI provider interface."""

    def __init__(self, name: str, api_key: str = '', base_url: str = ''):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.is_configured = bool(api_key) or name == 'ollama'

    @abstractmethod
    async def generate(
        self,
        messages: List[PromptMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[PromptMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name}) configured={self.is_configured}>"

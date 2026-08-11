"""AI Provider Manager - manages multiple AI providers."""
import asyncio
from typing import Dict, List, Optional, Type
from .base import BaseProvider, AIResponse, PromptMessage
import logging

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages multiple AI providers with routing and failover."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._priorities: Dict[str, int] = {}  # Initialize here
        self._provider_priority: List[str] = []
        self._default_provider: str = 'ollama'

    def register_provider(self, provider: BaseProvider, priority: int = 0):
        """Register an AI provider."""
        self._providers[provider.name] = provider
        self._priorities[provider.name] = priority
        self._provider_priority = sorted(
            self._providers.keys(),
            key=lambda name: self._priorities.get(name, 0),
            reverse=True
        )
        logger.info(f"Registered provider: {provider.name} with priority {priority}")

    def set_default_provider(self, provider_name: str):
        """Set the default provider."""
        if provider_name in self._providers:
            self._default_provider = provider_name

    def get_provider(self, name: str = None) -> Optional[BaseProvider]:
        """Get a specific provider."""
        provider_name = name or self._default_provider
        return self._providers.get(provider_name)

    def get_available_providers(self) -> List[Dict]:
        """Get list of available providers."""
        return [
            {
                'name': p.name,
                'configured': p.is_configured,
                'priority': self._priorities.get(p.name, 0),
                'models': p.get_available_models(),
            }
            for p in self._providers.values()
        ]

    async def generate(
        self,
        messages: List[PromptMessage],
        provider: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        fallback: bool = True,
        **kwargs
    ) -> AIResponse:
        """Generate response with automatic failover."""
        provider_name = provider or self._default_provider
        providers_to_try = [provider_name]

        if fallback:
            for p in self._provider_priority:
                if p != provider_name and p in self._providers:
                    providers_to_try.append(p)

        last_error = None
        for p_name in providers_to_try:
            p = self._providers.get(p_name)
            if not p or not p.is_configured:
                continue

            try:
                response = await p.generate(
                    messages, model=model, temperature=temperature,
                    max_tokens=max_tokens, **kwargs
                )
                return response
            except Exception as e:
                logger.warning(f"Provider {p_name} failed: {e}")
                last_error = e
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    async def generate_stream(
        self,
        messages: List[PromptMessage],
        provider: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """Generate streaming response."""
        provider_name = provider or self._default_provider
        p = self._providers.get(provider_name)
        if not p or not p.is_configured:
            raise ValueError(f"Provider {provider_name} not available")

        async for chunk in p.generate_stream(
            messages, model=model, temperature=temperature,
            max_tokens=max_tokens, **kwargs
        ):
            yield chunk

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    async def close_all(self):
        """Close all provider connections."""
        for provider in self._providers.values():
            if hasattr(provider, 'close'):
                await provider.close()


# Global provider manager instance
provider_manager = ProviderManager()

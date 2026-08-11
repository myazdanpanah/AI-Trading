"""AI Gateway - main interface for AI operations."""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from ..providers.provider_manager import provider_manager, ProviderManager
from ..providers.base import PromptMessage, AIResponse
from ..prompts import prompt_library, PromptVersion
from ..models import AIProvider, AIModel, AIRequest, AIMemory
import logging
import time

logger = logging.getLogger(__name__)


class AIGateway:
    """Main AI gateway for all AI operations."""

    def __init__(self):
        self.manager = provider_manager
        self._initialized = False

    async def initialize(self):
        """Initialize AI gateway with configured providers."""
        if self._initialized:
            return

        def _load_providers():
            return list(AIProvider.objects.filter(is_active=True))

        providers = await asyncio.to_thread(_load_providers)

        for provider_config in providers:
            try:
                if provider_config.provider_type == 'ollama':
                    from ..providers.ollama_provider import OllamaProvider
                    provider = OllamaProvider(base_url=provider_config.base_url or 'http://localhost:11434')
                elif provider_config.provider_type == 'openai':
                    from ..providers.openai_provider import OpenAIProvider
                    provider = OpenAIProvider(api_key=provider_config.api_key)
                elif provider_config.provider_type == 'anthropic':
                    from ..providers.anthropic_provider import AnthropicProvider
                    provider = AnthropicProvider(api_key=provider_config.api_key)
                else:
                    continue

                self.manager.register_provider(provider, priority=provider_config.priority)
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_config.name}: {e}")

        self._initialized = True
        logger.info(f"AI Gateway initialized with {len(self.manager.get_available_providers())} providers")

    async def analyze(
        self,
        prompt_name: str,
        variables: Dict,
        provider: str = None,
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Analyze using a registered prompt."""
        await self.initialize()

        prompt = prompt_library.get_current(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' not found")

        rendered = prompt.render(**variables)
        messages = [PromptMessage(role='user', content=rendered)]

        response = await self.manager.generate(
            messages,
            provider=provider,
            model=model,
            **kwargs
        )

        await self._log_request(
            prompt_name=prompt_name,
            provider=response.provider,
            model_name=response.model,
            tokens=response.tokens_used,
            latency=response.latency_ms,
        )

        return response

    async def chat(
        self,
        messages: List[PromptMessage],
        provider: str = None,
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Direct chat with AI."""
        await self.initialize()

        response = await self.manager.generate(
            messages,
            provider=provider,
            model=model,
            **kwargs
        )

        await self._log_request(
            prompt_name='direct_chat',
            provider=response.provider,
            model_name=response.model,
            tokens=response.tokens_used,
            latency=response.latency_ms,
        )

        return response

    async def store_memory(
        self,
        content: str,
        category: str,
        metadata: Dict = None
    ) -> str:
        """Store AI memory."""
        def _create():
            memory = AIMemory.objects.create(
                content=content,
                category=category,
                metadata=metadata or {},
            )
            return str(memory.id)

        return await asyncio.to_thread(_create)

    async def search_memory(
        self, query: str, category: str = None, limit: int = 10
    ) -> List[Dict]:
        """Search AI memory."""
        def _search():
            qs = AIMemory.objects.all()
            if category:
                qs = qs.filter(category=category)
            return list(qs.filter(content__icontains=query)[:limit])

        memories = await asyncio.to_thread(_search)
        return [
            {
                'id': str(m.id),
                'content': m.content,
                'category': m.category,
                'metadata': m.metadata,
            }
            for m in memories
        ]

    async def _log_request(
        self,
        prompt_name: str,
        provider: str,
        model_name: str,
        tokens: int,
        latency: int,
    ):
        """Log AI request."""
        def _create():
            # Try to find the model
            model_obj = None
            try:
                provider_obj = AIProvider.objects.get(name=provider)
                model_obj = AIModel.objects.filter(provider=provider_obj, name=model_name).first()
            except AIProvider.DoesNotExist:
                pass

            AIRequest.objects.create(
                model=model_obj,
                prompt=prompt_name,
                response='',
                tokens_used=tokens,
                latency_ms=latency,
                status='completed',
            )

        try:
            await asyncio.to_thread(_create)
        except Exception as e:
            logger.error(f"Failed to log AI request: {e}")

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        await self.initialize()
        return await self.manager.health_check_all()

    async def close(self):
        """Close all connections."""
        await self.manager.close_all()


# Global AI gateway instance
ai_gateway = AIGateway()

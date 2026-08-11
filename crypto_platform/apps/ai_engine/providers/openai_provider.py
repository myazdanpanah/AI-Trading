"""OpenAI API provider."""
import httpx
from typing import List, AsyncGenerator
from .base import BaseProvider, AIResponse, PromptMessage
import time
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    BASE_URL = 'https://api.openai.com/v1'

    AVAILABLE_MODELS = [
        'gpt-4o', 'gpt-4o-mini',
        'gpt-4-turbo', 'gpt-4',
        'gpt-3.5-turbo',
        'o1-preview', 'o1-mini',
    ]

    def __init__(self, api_key: str = '', base_url: str = None):
        super().__init__('openai', api_key=api_key, base_url=base_url or self.BASE_URL)
        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
        )

    async def generate(
        self,
        messages: List[PromptMessage],
        model: str = 'gpt-4o-mini',
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        start_time = time.time()
        try:
            openai_messages = [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ]
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    'model': model,
                    'messages': openai_messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                }
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)
            choice = data.get('choices', [{}])[0]
            content = choice.get('message', {}).get('content', '')
            usage = data.get('usage', {})
            return AIResponse(
                content=content,
                model=model,
                provider='openai',
                tokens_used=usage.get('total_tokens', 0),
                latency_ms=latency_ms,
                finish_reason=choice.get('finish_reason', 'stop'),
                metadata={
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                }
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[PromptMessage],
        model: str = 'gpt-4o-mini',
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        openai_messages = [{'role': msg.role, 'content': msg.content} for msg in messages]
        async with self.client.stream(
            'POST', f"{self.base_url}/chat/completions",
            json={
                'model': model,
                'messages': openai_messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': True,
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    import json
                    try:
                        data = json.loads(line[6:])
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS

    async def close(self):
        await self.client.aclose()

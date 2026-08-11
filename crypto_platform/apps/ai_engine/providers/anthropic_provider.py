"""Anthropic Claude API provider."""
import httpx
from typing import List, AsyncGenerator
from .base import BaseProvider, AIResponse, PromptMessage
import time
import logging

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    BASE_URL = 'https://api.anthropic.com/v1'

    AVAILABLE_MODELS = [
        'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku-20241022',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
    ]

    def __init__(self, api_key: str = '', base_url: str = None):
        super().__init__('anthropic', api_key=api_key, base_url=base_url or self.BASE_URL)
        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            }
        )

    async def generate(
        self,
        messages: List[PromptMessage],
        model: str = 'claude-3-5-sonnet-20241022',
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        start_time = time.time()
        try:
            # Extract system message if present
            system_msg = ''
            user_messages = []
            for msg in messages:
                if msg.role == 'system':
                    system_msg = msg.content
                else:
                    user_messages.append({'role': msg.role, 'content': msg.content})

            payload = {
                'model': model,
                'messages': user_messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
            if system_msg:
                payload['system'] = system_msg

            response = await self.client.post(
                f"{self.base_url}/messages",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            latency_ms = int((time.time() - start_time) * 1000)
            content = data.get('content', [{}])[0].get('text', '')
            usage = data.get('usage', {})

            return AIResponse(
                content=content,
                model=model,
                provider='anthropic',
                tokens_used=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                latency_ms=latency_ms,
                metadata={
                    'input_tokens': usage.get('input_tokens', 0),
                    'output_tokens': usage.get('output_tokens', 0),
                }
            )
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[PromptMessage],
        model: str = 'claude-3-5-sonnet-20241022',
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        system_msg = ''
        user_messages = []
        for msg in messages:
            if msg.role == 'system':
                system_msg = msg.content
            else:
                user_messages.append({'role': msg.role, 'content': msg.content})

        payload = {
            'model': model,
            'messages': user_messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': True,
        }
        if system_msg:
            payload['system'] = system_msg

        async with self.client.stream('POST', f"{self.base_url}/messages", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    import json
                    try:
                        data = json.loads(line[6:])
                        if data.get('type') == 'content_block_delta':
                            content = data.get('delta', {}).get('text', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Simple test request
            response = await self.client.post(
                f"{self.base_url}/messages",
                json={
                    'model': 'claude-3-5-haiku-20241022',
                    'messages': [{'role': 'user', 'content': 'Hi'}],
                    'max_tokens': 10,
                }
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS

    async def close(self):
        await self.client.aclose()

"""Ollama AI provider for local models."""
import httpx
from typing import List, Dict, AsyncGenerator
from .base import BaseProvider, AIResponse, PromptMessage
import time
import logging

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama provider for local AI models."""

    DEFAULT_MODELS = [
        'gemma4:latest',
        'llama3.2',
        'llama3', 'llama3.1', 'llama3:8b', 'llama3:70b',
        'qwen2.5', 'qwen2.5:7b', 'qwen2.5:72b',
        'deepseek-coder', 'deepseek-chat',
        'gemma2', 'gemma2:9b',
        'mistral', 'mixtral',
        'phi3', 'codellama',
    ]

    def __init__(self, base_url: str = 'http://localhost:11434'):
        super().__init__('ollama', base_url=base_url)
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=50.0)

    async def _get_installed_model(self) -> str:
        """Get the first installed model from Ollama."""
        try:
            models = await self.list_installed_models()
            if models:
                return models[0]['name']
        except Exception:
            pass
        return 'gemma4:latest'  # Fallback

    async def generate(
        self,
        messages: List[PromptMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        start_time = time.time()
        
        # Auto-detect model if not specified
        if model is None:
            model = await self._get_installed_model()
        
        try:
            ollama_messages = [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ]
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    'model': model,
                    'messages': ollama_messages,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)
            content = data.get('message', {}).get('content', '')
            tokens_used = data.get('eval_count', 0) + data.get('prompt_eval_count', 0)
            return AIResponse(
                content=content,
                model=model,
                provider='ollama',
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[PromptMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # Auto-detect model if not specified
        if model is None:
            model = await self._get_installed_model()
        
        ollama_messages = [{'role': msg.role, 'content': msg.content} for msg in messages]
        async with self.client.stream(
            'POST', f"{self.base_url}/api/chat",
            json={
                'model': model,
                'messages': ollama_messages,
                'stream': True,
                'options': {'temperature': temperature, 'num_predict': max_tokens}
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        content = data.get('message', {}).get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get models from Ollama (sync wrapper)."""
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return [m.get('name', '') for m in data.get('models', [])]
        except Exception:
            pass
        return self.DEFAULT_MODELS

    async def list_installed_models(self) -> List[Dict]:
        """List all installed models from Ollama."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = []
            for m in data.get('models', []):
                models.append({
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'modified_at': m.get('modified_at', ''),
                    'details': m.get('details', {}),
                })
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def get_model_info(self) -> Dict:
        """Get information about the current model."""
        models = await self.list_installed_models()
        if models:
            return {
                'installed_models': models,
                'active_model': models[0]['name'],
                'total_models': len(models),
            }
        return {
            'installed_models': [],
            'active_model': None,
            'total_models': 0,
        }

    async def close(self):
        await self.client.aclose()

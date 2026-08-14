"""LLM Router — local-first AI abstraction with mode selection and model routing.

AI Modes:
    AI OFF      - No LLM calls, pure quant signals
    AI LITE     - One small local model, 3 roles
    AI STANDARD - One stronger local model, 5 roles, adaptive routing
    AI CLOUD    - Optional cloud providers (OpenAI, Anthropic)

The router decides whether additional AI reasoning is needed based on:
- Market regime (extreme volatility → stronger model)
- Technical agreement (high agreement → skip AI)
- News impact (low impact → skip AI)

Cloud providers must be plugins/providers, not core dependencies.
"""
import logging
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AIMode(str, Enum):
    OFF = 'off'
    LITE = 'lite'
    STANDARD = 'standard'
    CLOUD = 'cloud'


class AgentRole(str, Enum):
    TECHNICAL_ANALYST = 'technical_analyst'
    NEWS_ANALYST = 'news_analyst'
    MARKET_ANALYST = 'market_analyst'
    RISK_ANALYST = 'risk_analyst'
    FINAL_VALIDATOR = 'final_validator'


@dataclass
class AIConfig:
    """AI configuration."""
    mode: AIMode = AIMode.STANDARD
    model: str = 'gemma4:latest'
    base_url: str = 'http://localhost:11434'
    timeout: int = 50000  # 50 seconds (per user request)
    max_retries: int = 3
    retry_delay: float = 1.0
    temperature: float = 0.3
    max_tokens: int = 2000
    # Cloud settings
    cloud_api_key: str = ''
    cloud_provider: str = ''  # openai, anthropic


@dataclass
class AIRouterResponse:
    """Response from the AI router."""
    content: str
    model: str
    provider: str
    mode: AIMode
    role: AgentRole
    latency_ms: int = 0
    tokens_used: int = 0
    parsed_output: Dict = None
    validation_errors: List[str] = None
    success: bool = True
    error: str = ''

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        if self.parsed_output is None:
            self.parsed_output = {}


# ── Role-Based Prompts ────────────────────────────────────────────────

ROLE_PROMPTS = {
    AgentRole.TECHNICAL_ANALYST: """You are a Technical Analyst for cryptocurrency markets.
Analyze the provided technical data and output a structured JSON response.

Output format:
{
  "direction": "bullish|bearish|neutral",
  "confidence": 0-100,
  "key_levels": {"support": [price], "resistance": [price]},
  "patterns": ["pattern names"],
  "recommendation": "brief text"
}""",

    AgentRole.NEWS_ANALYST: """You are a News Analyst for cryptocurrency markets.
Analyze the provided news data and output a structured JSON response.

Output format:
{
  "sentiment": "positive|negative|neutral",
  "impact": "high|medium|low",
  "key_events": ["event descriptions"],
  "affected_assets": ["BTC", "ETH"],
  "time_horizon": "1h|4h|1d|1w",
  "recommendation": "brief text"
}""",

    AgentRole.MARKET_ANALYST: """You are a Market Analyst for cryptocurrency markets.
Analyze the provided market data (regime, derivatives, macro) and output a structured JSON response.

Output format:
{
  "regime_assessment": "trend|range|volatile|transitioning",
  "key_drivers": ["driver descriptions"],
  "risk_level": "low|medium|high",
  "opportunity": "brief text",
  "recommendation": "brief text"
}""",

    AgentRole.RISK_ANALYST: """You are a Risk Analyst for cryptocurrency markets.
Analyze the provided risk data and output a structured JSON response.

Output format:
{
  "risk_level": "low|medium|high|extreme",
  "key_risks": ["risk descriptions"],
  "position_sizing": "conservative|moderate|aggressive",
  "max_drawdown_expected": "percentage",
  "recommendation": "brief text"
}""",

    AgentRole.FINAL_VALIDATOR: """You are the Final Validator for trading signals.
Review the quant composite score and all agent analyses.
Your job is to validate or reject the signal — you do NOT create signals.

Input: quant_composite_score, agent analyses, current regime
Output JSON format:
{
  "verdict": "validate|reject|modify",
  "adjusted_confidence": 0-100,
  "reasons": ["reason descriptions"],
  "risks": ["risk descriptions"],
  "modification": "if modified, what changed"
}""",
}


class LLMRouter:
    """
    LLM Router — the single entry point for all AI operations.

    Responsibilities:
    1. Route requests to appropriate provider based on AI mode
    2. Select model based on complexity requirements
    3. Validate structured outputs against JSON Schema
    4. Handle retries with exponential backoff
    5. Track model performance and health
    """

    def __init__(self, config: AIConfig = None):
        self.config = config or AIConfig()
        self._provider = None
        self._health_cache = {}
        self._health_cache_ttl = 60  # seconds

    async def initialize(self):
        """Initialize the appropriate provider based on mode."""
        if self.config.mode == AIMode.OFF:
            logger.info("AI mode: OFF — no LLM calls will be made")
            return

        if self.config.mode in (AIMode.LITE, AIMode.STANDARD):
            await self._init_ollama()
        elif self.config.mode == AIMode.CLOUD:
            await self._init_cloud()

    async def _init_ollama(self):
        """Initialize Ollama provider."""
        try:
            from ..providers.ollama_provider import OllamaProvider
            self._provider = OllamaProvider(base_url=self.config.base_url)
            health = await self._provider.health_check()
            if health:
                logger.info(f"Ollama connected: {self.config.base_url}")
            else:
                logger.warning(f"Ollama health check failed: {self.config.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")

    async def _init_cloud(self):
        """Initialize cloud provider."""
        # Cloud providers are optional plugins
        logger.info("Cloud mode — using cloud provider (if configured)")

    async def analyze(
        self,
        context: Dict,
        role: AgentRole = AgentRole.FINAL_VALIDATOR,
        schema: Dict = None,
        model: str = None,
    ) -> AIRouterResponse:
        """
        Analyze context using the appropriate AI model.

        Args:
            context: Analysis context (market data, signals, etc.)
            role: Agent role for specialized prompting
            schema: Optional JSON Schema for structured output validation
            model: Override model selection

        Returns:
            AIRouterResponse with content, parsed output, validation
        """
        # AI OFF mode — return quant-only response
        if self.config.mode == AIMode.OFF:
            return AIRouterResponse(
                content='AI OFF — using quant composite only',
                model='none',
                provider='none',
                mode=AIMode.OFF,
                role=role,
                parsed_output={'verdict': 'quant_only', 'confidence': context.get('quant_score', 50)},
            )

        if not self._provider:
            await self.initialize()
            if not self._provider:
                return AIRouterResponse(
                    content='AI provider not available',
                    model='none',
                    provider='none',
                    mode=self.config.mode,
                    role=role,
                    success=False,
                    error='Provider initialization failed',
                )

        # Build prompt
        system_prompt = ROLE_PROMPTS.get(role, '')
        user_prompt = self._build_prompt(context, role)

        from ..providers.base import PromptMessage
        messages = [
            PromptMessage(role='system', content=system_prompt),
            PromptMessage(role='user', content=user_prompt),
        ]

        # Select model
        selected_model = model or self.config.model

        # Execute with retry
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                response = await self._provider.generate(
                    messages=messages,
                    model=selected_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                latency_ms = int((time.time() - start_time) * 1000)

                # Parse and validate
                parsed, validation_errors = self._parse_and_validate(
                    response.content, schema
                )

                return AIRouterResponse(
                    content=response.content,
                    model=selected_model,
                    provider='ollama',
                    mode=self.config.mode,
                    role=role,
                    latency_ms=latency_ms,
                    tokens_used=response.tokens_used,
                    parsed_output=parsed,
                    validation_errors=validation_errors,
                    success=True,
                )

            except Exception as e:
                logger.warning(f"AI attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        return AIRouterResponse(
            content='AI generation failed after retries',
            model=selected_model,
            provider='ollama',
            mode=self.config.mode,
            role=role,
            success=False,
            error=f'Failed after {self.config.max_retries} attempts',
        )

    async def health_check(self) -> Dict:
        """Check health of all available providers."""
        result = {
            'ollama': {'available': False, 'models': []},
            'cloud': {'available': False, 'provider': self.config.cloud_provider},
            'mode': self.config.mode.value,
        }

        if self.config.mode in (AIMode.LITE, AIMode.STANDARD, AIMode.CLOUD):
            try:
                from ..providers.ollama_provider import OllamaProvider
                provider = OllamaProvider(base_url=self.config.base_url)
                health = await provider.health_check()
                result['ollama']['available'] = health
                if health:
                    models = await provider.list_installed_models()
                    result['ollama']['models'] = [m['name'] for m in models]
                await provider.close()
            except Exception as e:
                result['ollama']['error'] = str(e)

        return result

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        if not self._provider:
            return []
        try:
            return self._provider.get_available_models()
        except Exception:
            return []

    def _build_prompt(self, context: Dict, role: AgentRole) -> str:
        """Build role-specific prompt from context."""
        parts = []

        if 'quant_composite_score' in context:
            parts.append(f"Quant Composite Score: {context['quant_composite_score']}")
        if 'regime' in context:
            parts.append(f"Market Regime: {context['regime']}")
        if 'technical_score' in context:
            parts.append(f"Technical Score: {context['technical_score']}")
        if 'sentiment_score' in context:
            parts.append(f"Sentiment Score: {context['sentiment_score']}")
        if 'news_score' in context:
            parts.append(f"News Score: {context['news_score']}")
        if 'derivatives_score' in context:
            parts.append(f"Derivatives Score: {context['derivatives_score']}")
        if 'risk_state' in context:
            parts.append(f"Risk State: {json.dumps(context['risk_state'])}")
        if 'agent_analyses' in context:
            parts.append(f"Agent Analyses: {json.dumps(context['agent_analyses'])}")

        parts.append(f"\nAnalyze the above data and provide your assessment.")

        return '\n'.join(parts)

    def _parse_and_validate(
        self,
        content: str,
        schema: Dict = None,
    ) -> tuple:
        """
        Parse JSON from LLM response and validate against schema.

        Returns:
            Tuple of (parsed_dict, validation_errors)
        """
        parsed = {}
        errors = []

        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                # Try to find JSON object in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                else:
                    errors.append('No JSON found in response')
                    return parsed, errors

            parsed = json.loads(json_str)

        except json.JSONDecodeError as e:
            errors.append(f'Invalid JSON: {str(e)}')
            return parsed, errors

        # Validate against schema if provided
        if schema and parsed:
            errors = self._validate_schema(parsed, schema)

        return parsed, errors

    def _validate_schema(self, data: Dict, schema: Dict) -> List[str]:
        """Simple JSON Schema validation."""
        errors = []
        required = schema.get('required', [])
        properties = schema.get('properties', {})

        for field in required:
            if field not in data:
                errors.append(f'Missing required field: {field}')

        for field, spec in properties.items():
            if field in data:
                expected_type = spec.get('type')
                if expected_type == 'string' and not isinstance(data[field], str):
                    errors.append(f'Field {field} should be string')
                elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                    errors.append(f'Field {field} should be number')
                elif expected_type == 'array' and not isinstance(data[field], list):
                    errors.append(f'Field {field} should be array')

        return errors

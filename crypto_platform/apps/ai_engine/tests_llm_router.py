"""LLM Router tests — mode selection, routing, schema validation, retry.

Standalone tests that don't require Django model loading.
"""
import json
import sys
import importlib.util
from django.test import TestCase


def _load_module():
    """Load LLMRouter module directly to avoid Django model loading."""
    spec = importlib.util.spec_from_file_location(
        'llm_router',
        'crypto_platform/apps/ai_engine/services/llm_router.py'
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AIModeTest(TestCase):
    """Tests for AI mode selection."""

    def setUp(self):
        self.mod = _load_module()

    def test_off_mode(self):
        """AI OFF mode should return quant-only response."""
        config = self.mod.AIConfig(mode=self.mod.AIMode.OFF)
        router = self.mod.LLMRouter(config)

        import asyncio
        response = asyncio.run(router.analyze(
            context={'quant_score': 65},
            role=self.mod.AgentRole.FINAL_VALIDATOR,
        ))

        self.assertEqual(response.mode, self.mod.AIMode.OFF)
        self.assertIn('quant_only', response.parsed_output.get('verdict', ''))

    def test_lite_mode_config(self):
        """AI LITE mode should be configurable."""
        config = self.mod.AIConfig(mode=self.mod.AIMode.LITE, model='llama3.2')
        router = self.mod.LLMRouter(config)
        self.assertEqual(router.config.mode, self.mod.AIMode.LITE)
        self.assertEqual(router.config.model, 'llama3.2')

    def test_standard_mode_config(self):
        """AI STANDARD mode should be configurable."""
        config = self.mod.AIConfig(mode=self.mod.AIMode.STANDARD, model='gemma4:latest')
        router = self.mod.LLMRouter(config)
        self.assertEqual(router.config.mode, self.mod.AIMode.STANDARD)

    def test_cloud_mode_config(self):
        """AI CLOUD mode should be configurable."""
        config = self.mod.AIConfig(
            mode=self.mod.AIMode.CLOUD,
            cloud_provider='openai',
            cloud_api_key='test-key',
        )
        router = self.mod.LLMRouter(config)
        self.assertEqual(router.config.mode, self.mod.AIMode.CLOUD)
        self.assertEqual(router.config.cloud_provider, 'openai')


class AgentRoleTest(TestCase):
    """Tests for agent roles and prompts."""

    def setUp(self):
        self.mod = _load_module()

    def test_all_roles_have_prompts(self):
        """Every agent role should have a defined prompt."""
        for role in self.mod.AgentRole:
            self.assertIn(role, self.mod.ROLE_PROMPTS, f'Missing prompt for {role}')

    def test_prompts_are_json_friendly(self):
        """All role prompts should request JSON output."""
        for role, prompt in self.mod.ROLE_PROMPTS.items():
            self.assertIn('JSON', prompt.upper(), f'{role} prompt should request JSON')

    def test_final_validator_rejects_creates(self):
        """Final Validator should NOT create signals — only validate."""
        prompt = self.mod.ROLE_PROMPTS[self.mod.AgentRole.FINAL_VALIDATOR]
        self.assertIn('validate|reject|modify', prompt)
        self.assertIn('do NOT create signals', prompt)


class SchemaValidationTest(TestCase):
    """Tests for JSON Schema validation."""

    def setUp(self):
        self.mod = _load_module()
        self.router = self.mod.LLMRouter(self.mod.AIConfig(mode=self.mod.AIMode.OFF))

    def test_valid_json(self):
        """Valid JSON should parse correctly."""
        content = '{"direction": "bullish", "confidence": 75}'
        parsed, errors = self.router._parse_and_validate(content)
        self.assertEqual(parsed['direction'], 'bullish')
        self.assertEqual(parsed['confidence'], 75)
        self.assertEqual(errors, [])

    def test_json_in_code_block(self):
        """JSON in markdown code block should be extracted."""
        content = 'Here is the analysis:\n```json\n{"direction": "bearish", "confidence": 60}\n```'
        parsed, errors = self.router._parse_and_validate(content)
        self.assertEqual(parsed['direction'], 'bearish')

    def test_invalid_json(self):
        """Invalid JSON should produce error."""
        content = 'This is not JSON at all'
        parsed, errors = self.router._parse_and_validate(content)
        self.assertEqual(parsed, {})
        self.assertGreater(len(errors), 0)

    def test_missing_required_field(self):
        """Missing required field should produce validation error."""
        schema = {
            'required': ['direction', 'confidence'],
            'properties': {
                'direction': {'type': 'string'},
                'confidence': {'type': 'number'},
            }
        }
        content = '{"direction": "bullish"}'
        parsed, errors = self.router._parse_and_validate(content, schema)
        self.assertIn('Missing required field: confidence', errors)

    def test_wrong_type(self):
        """Wrong field type should produce validation error."""
        schema = {
            'properties': {
                'confidence': {'type': 'number'},
            }
        }
        content = '{"confidence": "high"}'
        parsed, errors = self.router._parse_and_validate(content, schema)
        self.assertIn('Field confidence should be number', errors)

    def test_no_schema_skips_validation(self):
        """Without schema, no validation errors should occur."""
        content = '{"anything": "goes"}'
        parsed, errors = self.router._parse_and_validate(content, None)
        self.assertEqual(errors, [])


class AIRouterResponseTest(TestCase):
    """Tests for AIRouterResponse dataclass."""

    def setUp(self):
        self.mod = _load_module()

    def test_default_values(self):
        """Response should have sensible defaults."""
        response = self.mod.AIRouterResponse(
            content='test',
            model='test',
            provider='test',
            mode=self.mod.AIMode.OFF,
            role=self.mod.AgentRole.FINAL_VALIDATOR,
        )
        self.assertTrue(response.success)
        self.assertEqual(response.latency_ms, 0)
        self.assertEqual(response.tokens_used, 0)
        self.assertEqual(response.parsed_output, {})
        self.assertEqual(response.validation_errors, [])

    def test_failure_response(self):
        """Failed response should have error details."""
        response = self.mod.AIRouterResponse(
            content='failed',
            model='test',
            provider='test',
            mode=self.mod.AIMode.OFF,
            role=self.mod.AgentRole.FINAL_VALIDATOR,
            success=False,
            error='Connection refused',
        )
        self.assertFalse(response.success)
        self.assertEqual(response.error, 'Connection refused')


class HealthCheckTest(TestCase):
    """Tests for health check functionality."""

    def setUp(self):
        self.mod = _load_module()

    def test_health_check_structure(self):
        """Health check should return structured result."""
        config = self.mod.AIConfig(mode=self.mod.AIMode.OFF)
        router = self.mod.LLMRouter(config)

        import asyncio
        result = asyncio.run(router.health_check())

        self.assertIn('ollama', result)
        self.assertIn('cloud', result)
        self.assertIn('mode', result)
        self.assertEqual(result['mode'], 'off')


class RetryLogicTest(TestCase):
    """Tests for retry configuration."""

    def setUp(self):
        self.mod = _load_module()

    def test_retry_config(self):
        """Retry config should be settable."""
        config = self.mod.AIConfig(max_retries=5, retry_delay=2.0)
        router = self.mod.LLMRouter(config)
        self.assertEqual(router.config.max_retries, 5)
        self.assertEqual(router.config.retry_delay, 2.0)

    def test_timeout_config(self):
        """Timeout should be configurable (default 50s per user request)."""
        config = self.mod.AIConfig(timeout=50000)
        router = self.mod.LLMRouter(config)
        self.assertEqual(router.config.timeout, 50000)

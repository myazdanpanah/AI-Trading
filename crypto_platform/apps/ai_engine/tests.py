"""Tests for AI Engine orchestrator."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from django.test import TestCase
from .models import (
    AgentDefinition, Workflow, WorkflowStep,
    WorkflowExecution, AgentExecution
)
from .services.orchestrator import (
    AIOrchestrator, PipelineAgent, ConsensusAgent, DebateAgent,
    AgentConfig, StepResult, WorkflowPattern
)
from .providers.base import PromptMessage, AIResponse


class AgentConfigTest(TestCase):
    """Test AgentConfig dataclass."""

    def test_agent_config_creation(self):
        config = AgentConfig(
            name='test_agent',
            role='market_analyst',
            system_prompt='You are a test agent.',
            temperature=0.5,
            max_tokens=1000,
        )
        self.assertEqual(config.name, 'test_agent')
        self.assertEqual(config.role, 'market_analyst')
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.max_tokens, 1000)
        self.assertEqual(config.capabilities, [])
        self.assertEqual(config.dependencies, [])

    def test_agent_config_with_capabilities(self):
        config = AgentConfig(
            name='test_agent',
            role='market_analyst',
            system_prompt='You are a test agent.',
            capabilities=['price_analysis', 'volume_analysis'],
            dependencies=['news_analyst'],
        )
        self.assertEqual(config.capabilities, ['price_analysis', 'volume_analysis'])
        self.assertEqual(config.dependencies, ['news_analyst'])


class StepResultTest(TestCase):
    """Test StepResult dataclass."""

    def test_step_result_success(self):
        result = StepResult(
            agent_name='test_agent',
            success=True,
            output='Analysis result',
            provider='ollama',
            model='llama3',
            tokens_used=100,
            latency_ms=500,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output, 'Analysis result')
        self.assertEqual(result.tokens_used, 100)

        dict_result = result.to_dict()
        self.assertEqual(dict_result['agent_name'], 'test_agent')
        self.assertTrue(dict_result['success'])
        self.assertEqual(dict_result['provider'], 'ollama')

    def test_step_result_failure(self):
        result = StepResult(
            agent_name='test_agent',
            success=False,
            error='API rate limit exceeded',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, 'API rate limit exceeded')
        self.assertIsNone(result.output)

        dict_result = result.to_dict()
        self.assertFalse(dict_result['success'])
        self.assertEqual(dict_result['error'], 'API rate limit exceeded')


class MockAIGateway:
    """Mock AI Gateway for testing."""

    def __init__(self, response_content='Mock AI response'):
        self._initialized = False
        self._response_content = response_content

    async def initialize(self):
        self._initialized = True

    async def chat(self, messages, provider=None, model=None, **kwargs):
        return AIResponse(
            content=self._response_content,
            model=model or 'mock-model',
            provider=provider or 'mock-provider',
            tokens_used=100,
            latency_ms=100,
        )

    async def health_check(self):
        return {'mock': True}


class PipelineAgentTest(TestCase):
    """Test PipelineAgent execution."""

    def setUp(self):
        self.config = AgentConfig(
            name='test_pipeline_agent',
            role='market_analyst',
            system_prompt='You are a test market analyst.',
            temperature=0.5,
            max_tokens=1000,
        )
        self.gateway = MockAIGateway('Pipeline analysis result')

    def test_pipeline_agent_execute(self):
        agent = PipelineAgent(self.config, self.gateway)
        context = {'symbol': 'BTC', 'price': 50000}

        result = asyncio.run(agent.execute(context))

        self.assertTrue(result.success)
        self.assertEqual(result.output, 'Pipeline analysis result')
        self.assertEqual(result.agent_name, 'test_pipeline_agent')
        self.assertEqual(result.tokens_used, 100)


class ConsensusAgentTest(TestCase):
    """Test ConsensusAgent execution."""

    def setUp(self):
        self.config = AgentConfig(
            name='test_consensus_agent',
            role='technical_analyst',
            system_prompt='You are a test technical analyst.',
        )
        self.gateway = MockAIGateway('Consensus analysis result')

    def test_consensus_agent_execute(self):
        agent = ConsensusAgent(self.config, self.gateway)
        context = {'symbol': 'BTC', 'indicators': 'RSI: 65'}

        result = asyncio.run(agent.execute(context))

        self.assertTrue(result.success)
        self.assertEqual(result.output, 'Consensus analysis result')


class DebateAgentTest(TestCase):
    """Test DebateAgent execution."""

    def setUp(self):
        self.config = AgentConfig(
            name='test_debate_agent',
            role='market_analyst',
            system_prompt='You are a test market analyst.',
        )
        self.gateway = MockAIGateway('Debate argument')

    def test_debate_agent_bullish(self):
        agent = DebateAgent(self.config, self.gateway, stance='bullish')
        context = {'symbol': 'BTC', 'price': 50000}

        result = asyncio.run(agent.execute(context))

        self.assertTrue(result.success)
        self.assertEqual(result.output['stance'], 'bullish')
        self.assertEqual(result.output['argument'], 'Debate argument')

    def test_debate_agent_bearish(self):
        agent = DebateAgent(self.config, self.gateway, stance='bearish')
        context = {'symbol': 'BTC', 'price': 50000}

        result = asyncio.run(agent.execute(context))

        self.assertTrue(result.success)
        self.assertEqual(result.output['stance'], 'bearish')


class AIOrchestratorTest(TestCase):
    """Test AIOrchestrator class."""

    def setUp(self):
        self.gateway = MockAIGateway('Orchestrator response')
        self.orchestrator = AIOrchestrator(self.gateway)

    def test_orchestrator_initialization(self):
        asyncio.run(self.orchestrator.initialize())
        self.assertTrue(self.gateway._initialized)

    def test_get_agent_config_not_found(self):
        config = self.orchestrator.get_agent_config('nonexistent_agent')
        self.assertIsNone(config)


class WorkflowPatternTest(TestCase):
    """Test WorkflowPattern enum."""

    def test_pattern_values(self):
        self.assertEqual(WorkflowPattern.PIPELINE.value, 'pipeline')
        self.assertEqual(WorkflowPattern.PARALLEL.value, 'parallel')
        self.assertEqual(WorkflowPattern.CONSENSUS.value, 'consensus')
        self.assertEqual(WorkflowPattern.DEBATE.value, 'debate')
        self.assertEqual(WorkflowPattern.HIERARCHICAL.value, 'hierarchical')


class AgentDefinitionModelTest(TestCase):
    """Test AgentDefinition model."""

    def test_create_agent_definition(self):
        agent = AgentDefinition.objects.create(
            name='test_agent',
            role='market_analyst',
            system_prompt='You are a test agent.',
            temperature=0.5,
            max_tokens=1000,
            capabilities=['price_analysis'],
            dependencies=[],
        )
        self.assertEqual(agent.name, 'test_agent')
        self.assertEqual(agent.role, 'market_analyst')
        self.assertTrue(agent.is_active)

    def test_agent_str_representation(self):
        agent = AgentDefinition.objects.create(
            name='market_analyst',
            role='market_analyst',
            system_prompt='System prompt.',
        )
        self.assertIn('market_analyst', str(agent))


class WorkflowModelTest(TestCase):
    """Test Workflow model."""

    def setUp(self):
        self.agent = AgentDefinition.objects.create(
            name='test_agent',
            role='market_analyst',
            system_prompt='System prompt.',
        )

    def test_create_workflow(self):
        workflow = Workflow.objects.create(
            name='test_workflow',
            description='A test workflow.',
            pattern='pipeline',
        )
        self.assertEqual(workflow.name, 'test_workflow')
        self.assertEqual(workflow.pattern, 'pipeline')

    def test_create_workflow_step(self):
        workflow = Workflow.objects.create(
            name='test_workflow',
            pattern='pipeline',
        )
        step = WorkflowStep.objects.create(
            workflow=workflow,
            agent=self.agent,
            step_order=1,
            output_key='analysis',
        )
        self.assertEqual(step.workflow, workflow)
        self.assertEqual(step.agent, self.agent)
        self.assertEqual(step.step_order, 1)

    def test_workflow_str_representation(self):
        workflow = Workflow.objects.create(
            name='test_workflow',
            pattern='pipeline',
        )
        self.assertIn('test_workflow', str(workflow))class OrchestratorPipelineIntegrationTest(TestCase):
    """Integration tests for orchestrator pipeline execution."""

    def setUp(self):
        self.gateway = MockAIGateway('Pipeline result')
        self.orchestrator = AIOrchestrator(self.gateway)

        # Create agent definitions in DB with unique names
        self.agent1 = AgentDefinition.objects.create(
            name='pipeline_analyst_1',
            role='market_analyst',
            system_prompt='You are analyst 1.',
        )
        self.agent2 = AgentDefinition.objects.create(
            name='pipeline_analyst_2',
            role='technical_analyst',
            system_prompt='You are analyst 2.',
        )

        # Load agents into cache
        self.orchestrator._agent_cache['pipeline_analyst_1'] = AgentConfig(
            name='pipeline_analyst_1', role='market_analyst', system_prompt='You are analyst 1.',
        )
        self.orchestrator._agent_cache['pipeline_analyst_2'] = AgentConfig(
            name='pipeline_analyst_2', role='technical_analyst', system_prompt='You are analyst 2.',
        )

        # Create workflow
        self.workflow = Workflow.objects.create(
            name='test_pipeline',
            pattern='pipeline',
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            agent=self.agent1,
            step_order=1,
            output_key='analysis_1',
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            agent=self.agent2,
            step_order=2,
            output_key='analysis_2',
        )

    def test_pipeline_execution_creates_workflow_execution(self):
        """Test that pipeline execution creates WorkflowExecution record."""
        result = asyncio.run(self.orchestrator.run_workflow(
            workflow_id=str(self.workflow.id),
            input_data={'symbol': 'BTC'},
        ))

        self.assertEqual(result['status'], 'completed')
        self.assertIn('execution_id', result)
        self.assertEqual(result['result']['pattern'], 'pipeline')

        # Verify execution record was created
        execution = WorkflowExecution.objects.get(id=result['execution_id'])
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(execution.workflow, self.workflow)

    def test_pipeline_execution_creates_agent_executions(self):
        """Test that pipeline execution creates AgentExecution records."""
        result = asyncio.run(self.orchestrator.run_workflow(
            workflow_id=str(self.workflow.id),
            input_data={'symbol': 'BTC'},
        ))

        # Verify agent execution records were created
        agent_execs = AgentExecution.objects.filter(
            workflow_execution__id=result['execution_id']
        )
        self.assertEqual(agent_execs.count(), 2)
        for ae in agent_execs:
            self.assertEqual(ae.status, 'completed')

    def test_pipeline_execution_failure_marks_execution_failed(self):
        """Test that pipeline failure marks execution as failed."""
        with patch.object(Workflow, 'objects') as mock_wf:
            mock_wf.get.side_effect = Workflow.DoesNotExist('Not found')
            result = asyncio.run(self.orchestrator.run_workflow(
                workflow_id='00000000-0000-0000-0000-000000000000',
                input_data={'symbol': 'BTC'},
            ))

        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)

    def test_pipeline_execution_clears_execution_on_completion(self):
        """Test that _execution is cleared after workflow completes."""
        asyncio.run(self.orchestrator.run_workflow(
            workflow_id=str(self.workflow.id),
            input_data={'symbol': 'BTC'},
        ))

        self.assertIsNone(self.orchestrator._execution)

    def test_pipeline_execution_clears_execution_on_failure(self):
        """Test that _execution is cleared after workflow failure."""
        with patch.object(Workflow, 'objects') as mock_wf:
            mock_wf.get.side_effect = Workflow.DoesNotExist('Not found')
            asyncio.run(self.orchestrator.run_workflow(
                workflow_id='00000000-0000-0000-0000-000000000000',
                input_data={'symbol': 'BTC'},
            ))

        self.assertIsNone(self.orchestrator._execution)


class OrchestratorParallelIntegrationTest(TestCase):
    """Integration tests for orchestrator parallel execution."""

    def setUp(self):
        self.gateway = MockAIGateway('Parallel result')
        self.orchestrator = AIOrchestrator(self.gateway)

        self.agent1 = AgentDefinition.objects.create(
            name='parallel_analyst_1',
            role='market_analyst',
            system_prompt='You are analyst 1.',
        )
        self.agent2 = AgentDefinition.objects.create(
            name='parallel_analyst_2',
            role='news_analyst',
            system_prompt='You are analyst 2.',
        )

        self.orchestrator._agent_cache['parallel_analyst_1'] = AgentConfig(
            name='parallel_analyst_1', role='market_analyst', system_prompt='You are analyst 1.',
        )
        self.orchestrator._agent_cache['parallel_analyst_2'] = AgentConfig(
            name='parallel_analyst_2', role='news_analyst', system_prompt='You are analyst 2.',
        )

        self.workflow = Workflow.objects.create(
            name='test_parallel',
            pattern='parallel',
        )
        WorkflowStep.objects.create(
            workflow=self.workflow, agent=self.agent1, step_order=1,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow, agent=self.agent2, step_order=2,
        )

    def test_parallel_execution(self):
        """Test parallel execution runs all steps."""
        result = asyncio.run(self.orchestrator.run_workflow(
            workflow_id=str(self.workflow.id),
            input_data={'symbol': 'BTC'},
        ))

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['result']['pattern'], 'parallel')
        self.assertEqual(len(result['result']['step_results']), 2)


class OrchestratorDebateIntegrationTest(TestCase):
    """Integration tests for orchestrator debate execution."""

    def setUp(self):
        self.gateway = MockAIGateway('Debate result')
        self.orchestrator = AIOrchestrator(self.gateway)

        self.agent1 = AgentDefinition.objects.create(
            name='debate_bull',
            role='market_analyst',
            system_prompt='You are bullish.',
        )
        self.agent2 = AgentDefinition.objects.create(
            name='debate_bear',
            role='market_analyst',
            system_prompt='You are bearish.',
        )

        self.orchestrator._agent_cache['debate_bull'] = AgentConfig(
            name='debate_bull', role='market_analyst', system_prompt='You are bullish.',
        )
        self.orchestrator._agent_cache['debate_bear'] = AgentConfig(
            name='debate_bear', role='market_analyst', system_prompt='You are bearish.',
        )

        self.workflow = Workflow.objects.create(
            name='test_debate',
            pattern='debate',
        )
        WorkflowStep.objects.create(
            workflow=self.workflow, agent=self.agent1, step_order=1,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow, agent=self.agent2, step_order=2,
        )

    def test_debate_execution(self):
        """Test debate execution produces moderator synthesis."""
        result = asyncio.run(self.orchestrator.run_workflow(
            workflow_id=str(self.workflow.id),
            input_data={'symbol': 'BTC'},
        ))

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['result']['pattern'], 'debate')
        self.assertIn('moderator_synthesis', result['result'])
        self.assertIn('debates', result['result'])
        self.assertEqual(len(result['result']['debates']), 2)


class SingleAgentExecutionTest(TestCase):
    """Test running a single agent directly."""

    def setUp(self):
        self.gateway = MockAIGateway('Single agent result')
        self.orchestrator = AIOrchestrator(self.gateway)
        self.orchestrator._agent_cache['single_test_agent'] = AgentConfig(
            name='single_test_agent', role='market_analyst',
            system_prompt='You are a test agent.',
        )

    def test_run_single_agent(self):
        """Test running a single agent."""
        result = asyncio.run(self.orchestrator.run_single_agent(
            agent_name='single_test_agent',
            input_data={'symbol': 'BTC'},
        ))

        self.assertTrue(result['success'])
        self.assertEqual(result['output'], 'Single agent result')

    def test_run_single_agent_not_found(self):
        """Test running a non-existent agent."""
        result = asyncio.run(self.orchestrator.run_single_agent(
            agent_name='nonexistent',
            input_data={'symbol': 'BTC'},
        ))

        self.assertIn('error', result)


class WorkflowHistoryTest(TestCase):
    """Test workflow history retrieval."""

    def setUp(self):
        self.gateway = MockAIGateway()
        self.orchestrator = AIOrchestrator(self.gateway)

    def test_get_workflow_history(self):
        """Test workflow history retrieval."""
        agent = AgentDefinition.objects.create(
            name='history_test_agent',
            role='market_analyst',
            system_prompt='Prompt',
        )
        workflow = Workflow.objects.create(
            name='test_wf_history', pattern='pipeline',
        )

        # Create execution records
        for i in range(3):
            WorkflowExecution.objects.create(
                workflow=workflow,
                status='completed',
                input_data={'i': i},
            )

        history = asyncio.run(self.orchestrator.get_workflow_history(
            workflow_id=str(workflow.id), limit=2,
        ))

        self.assertEqual(len(history), 2)
        for entry in history:
            self.assertIn('id', entry)
            self.assertIn('status', entry)

    def test_get_workflow_history_empty(self):
        """Test workflow history with no executions."""
        workflow = Workflow.objects.create(
            name='test_wf_empty', pattern='pipeline',
        )

        history = asyncio.run(self.orchestrator.get_workflow_history(
            workflow_id=str(workflow.id), limit=10,
        ))

        self.assertEqual(len(history), 0)

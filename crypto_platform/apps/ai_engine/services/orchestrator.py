"""AI Orchestrator - Multi-agent coordination system."""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from ..providers.base import PromptMessage, AIResponse
from ..providers.provider_manager import provider_manager
from ..prompts import prompt_library
from ..models import (
    AgentDefinition, Workflow, WorkflowStep,
    WorkflowExecution, AgentExecution
)

logger = logging.getLogger(__name__)


class WorkflowPattern(Enum):
    """Workflow execution patterns."""
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    CONSENSUS = "consensus"
    DEBATE = "debate"
    HIERARCHICAL = "hierarchical"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    role: str
    system_prompt: str
    provider: str = None
    model: str = None
    temperature: float = 0.7
    max_tokens: int = 2000
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StepResult:
    """Result from a single agent step."""
    agent_name: str
    success: bool
    output: Any = None
    error: str = None
    provider: str = None
    model: str = None
    tokens_used: int = 0
    latency_ms: int = 0

    def to_dict(self) -> Dict:
        return {
            'agent_name': self.agent_name,
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'provider': self.provider,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'latency_ms': self.latency_ms,
        }


class BaseAgent:
    """Base class for all agents in the orchestrator."""

    def __init__(self, config: AgentConfig, ai_gateway):
        self.config = config
        self.ai_gateway = ai_gateway

    async def execute(self, context: Dict) -> StepResult:
        """Execute the agent's task."""
        raise NotImplementedError

    async def _generate(self, messages: List[PromptMessage]) -> AIResponse:
        """Generate AI response."""
        return await self.ai_gateway.chat(
            messages=messages,
            provider=self.config.provider,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )


class PipelineAgent(BaseAgent):
    """Agent that processes input sequentially."""

    async def execute(self, context: Dict) -> StepResult:
        try:
            # Build messages with system prompt and context
            messages = [
                PromptMessage(role='system', content=self.config.system_prompt),
                PromptMessage(role='user', content=json.dumps(context, default=str))
            ]

            response = await self._generate(messages)

            return StepResult(
                agent_name=self.config.name,
                success=True,
                output=response.content,
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                latency_ms=response.latency_ms,
            )
        except Exception as e:
            logger.error(f"Agent {self.config.name} failed: {e}")
            return StepResult(
                agent_name=self.config.name,
                success=False,
                error=str(e),
            )


class ConsensusAgent(BaseAgent):
    """Agent that participates in consensus decision-making."""

    async def execute(self, context: Dict) -> StepResult:
        try:
            # Add consensus-specific instructions
            consensus_prompt = f"""You are participating in a consensus decision-making process.
Your role is to provide your expert opinion based on your specialization.

{self.config.system_prompt}

Input from other agents or data sources:
{json.dumps(context, default=str)}

Provide your analysis and recommendation. Be specific and justify your reasoning."""

            messages = [
                PromptMessage(role='user', content=consensus_prompt)
            ]

            response = await self._generate(messages)

            return StepResult(
                agent_name=self.config.name,
                success=True,
                output=response.content,
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                latency_ms=response.latency_ms,
            )
        except Exception as e:
            logger.error(f"Consensus agent {self.config.name} failed: {e}")
            return StepResult(
                agent_name=self.config.name,
                success=False,
                error=str(e),
            )


class DebateAgent(BaseAgent):
    """Agent that participates in debate-style analysis."""

    def __init__(self, config: AgentConfig, ai_gateway, stance: str = 'neutral'):
        super().__init__(config, ai_gateway)
        self.stance = stance

    async def execute(self, context: Dict) -> StepResult:
        try:
            debate_prompt = f"""You are participating in a debate analysis.
Your assigned stance is: {self.stance}

{self.config.system_prompt}

Topic/Context:
{json.dumps(context, default=str)}

Provide your argument for your assigned stance. Be persuasive and cite evidence."""

            messages = [
                PromptMessage(role='user', content=debate_prompt)
            ]

            response = await self._generate(messages)

            return StepResult(
                agent_name=self.config.name,
                success=True,
                output={
                    'stance': self.stance,
                    'argument': response.content,
                },
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                latency_ms=response.latency_ms,
            )
        except Exception as e:
            logger.error(f"Debate agent {self.config.name} failed: {e}")
            return StepResult(
                agent_name=self.config.name,
                success=False,
                error=str(e),
            )


class AIOrchestrator:
    """Main orchestrator for multi-agent coordination."""

    def __init__(self, ai_gateway):
        self.ai_gateway = ai_gateway
        self._agent_cache: Dict[str, AgentConfig] = {}
        self._execution: Optional[WorkflowExecution] = None

    async def initialize(self):
        """Initialize orchestrator with configured agents."""
        await self.ai_gateway.initialize()
        await self._load_agents()
        logger.info("AI Orchestrator initialized")

    async def _load_agents(self):
        """Load agent definitions from database."""
        def _fetch():
            return list(AgentDefinition.objects.filter(is_active=True))

        agents = await asyncio.to_thread(_fetch)

        for agent in agents:
            config = AgentConfig(
                name=agent.name,
                role=agent.role,
                system_prompt=agent.system_prompt,
                provider=agent.preferred_provider or None,
                model=agent.preferred_model or None,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                capabilities=agent.capabilities,
                dependencies=agent.dependencies,
            )
            self._agent_cache[agent.name] = config

        logger.info(f"Loaded {len(self._agent_cache)} agent definitions")

    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name."""
        return self._agent_cache.get(name)

    async def run_workflow(
        self,
        workflow_id: str,
        input_data: Dict,
        context: Dict = None,
    ) -> Dict:
        """Run a workflow by ID."""
        def _fetch_workflow():
            return Workflow.objects.get(id=workflow_id)

        workflow = await asyncio.to_thread(_fetch_workflow)

        # Create execution record
        def _create_execution():
            return WorkflowExecution.objects.create(
                workflow=workflow,
                input_data=input_data,
                status='running',
                started_at=datetime.now(),
            )

        execution = await asyncio.to_thread(_create_execution)
        self._execution = execution

        try:
            # Load workflow steps
            def _fetch_steps():
                return list(WorkflowStep.objects.filter(
                    workflow=workflow
                ).select_related('agent').order_by('step_order'))

            steps = await asyncio.to_thread(_fetch_steps)

            # Execute based on pattern
            pattern = WorkflowPattern(workflow.pattern)
            result = await self._execute_pattern(
                pattern=pattern,
                steps=steps,
                input_data=input_data,
                context=context or {},
                workflow=workflow,
            )

            # Update execution record
            def _update_execution():
                execution.status = 'completed'
                execution.output_data = result
                execution.completed_at = datetime.now()
                execution.total_tokens = sum(
                    r.get('tokens_used', 0) for r in result.get('step_results', [])
                )
                execution.total_latency_ms = sum(
                    r.get('latency_ms', 0) for r in result.get('step_results', [])
                )
                execution.save()

            await asyncio.to_thread(_update_execution)

            return {
                'execution_id': str(execution.id),
                'status': 'completed',
                'result': result,
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

            def _update_failed():
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.completed_at = datetime.now()
                execution.save()

            await asyncio.to_thread(_update_failed)

            return {
                'execution_id': str(execution.id),
                'status': 'failed',
                'error': str(e),
            }
        finally:
            self._execution = None

    async def _execute_pattern(
        self,
        pattern: WorkflowPattern,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
        workflow: Workflow,
    ) -> Dict:
        """Execute steps based on workflow pattern."""
        if pattern == WorkflowPattern.PIPELINE:
            return await self._execute_pipeline(steps, input_data, context)
        elif pattern == WorkflowPattern.PARALLEL:
            return await self._execute_parallel(steps, input_data, context)
        elif pattern == WorkflowPattern.CONSENSUS:
            return await self._execute_consensus(steps, input_data, context)
        elif pattern == WorkflowPattern.DEBATE:
            return await self._execute_debate(steps, input_data, context)
        elif pattern == WorkflowPattern.HIERARCHICAL:
            return await self._execute_hierarchical(steps, input_data, context)
        else:
            return await self._execute_pipeline(steps, input_data, context)

    async def _execute_pipeline(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
    ) -> Dict:
        """Execute steps sequentially, passing output to next step."""
        step_results = []
        current_input = {**input_data, **context}

        for step in steps:
            agent_config = self._agent_cache.get(step.agent.name)
            if not agent_config:
                step_results.append(StepResult(
                    agent_name=step.agent.name,
                    success=False,
                    error=f"Agent config not found: {step.agent.name}",
                ).to_dict())
                continue

            # Map input based on step configuration
            mapped_input = self._map_input(step.input_mapping, current_input)

            # Create agent execution record
            agent_exec = await self._create_agent_execution(step)

            # Execute agent
            agent = PipelineAgent(agent_config, self.ai_gateway)
            result = await agent.execute(mapped_input)

            # Update agent execution record
            await self._update_agent_execution(agent_exec, result)

            step_results.append(result.to_dict())

            # Update current input for next step
            if result.success and step.output_key:
                current_input[step.output_key] = result.output
            elif result.success:
                current_input[f"{step.agent.name}_output"] = result.output

            if not result.success and not step.is_optional:
                break

        return {
            'pattern': 'pipeline',
            'step_results': step_results,
            'final_output': current_input,
        }

    async def _execute_parallel(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
    ) -> Dict:
        """Execute all steps in parallel."""
        step_results = []
        tasks = []

        for step in steps:
            agent_config = self._agent_cache.get(step.agent.name)
            if not agent_config:
                step_results.append(StepResult(
                    agent_name=step.agent.name,
                    success=False,
                    error=f"Agent config not found: {step.agent.name}",
                ).to_dict())
                continue

            mapped_input = self._map_input(step.input_mapping, {**input_data, **context})
            agent = PipelineAgent(agent_config, self.ai_gateway)
            tasks.append(agent.execute(mapped_input))

        # Create agent execution records before execution
        valid_steps = [s for s in steps if self._agent_cache.get(s.agent.name)]
        agent_execs = []
        for step in valid_steps:
            agent_exec = await self._create_agent_execution(step)
            agent_execs.append(agent_exec)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update agent execution records with results
        for i, result in enumerate(results):
            if i < len(agent_execs):
                if isinstance(result, Exception):
                    await self._update_agent_execution(agent_execs[i], StepResult(
                        agent_name=valid_steps[i].agent.name,
                        success=False,
                        error=str(result),
                    ))
                    step_results.append(StepResult(
                        agent_name=valid_steps[i].agent.name,
                        success=False,
                        error=str(result),
                    ).to_dict())
                else:
                    await self._update_agent_execution(agent_execs[i], result)
                    step_results.append(result.to_dict())

        # Merge all outputs
        final_output = {**input_data}
        for r in step_results:
            if r.get('success'):
                final_output[f"{r['agent_name']}_output"] = r.get('output')

        return {
            'pattern': 'parallel',
            'step_results': step_results,
            'final_output': final_output,
        }

    async def _execute_consensus(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
    ) -> Dict:
        """Execute steps in consensus mode - all agents analyze, then synthesize."""
        # First, collect all agent opinions in parallel
        opinions = []
        tasks = []
        valid_steps = []

        for step in steps:
            agent_config = self._agent_cache.get(step.agent.name)
            if not agent_config:
                continue

            valid_steps.append(step)
            mapped_input = self._map_input(step.input_mapping, {**input_data, **context})
            agent = ConsensusAgent(agent_config, self.ai_gateway)
            tasks.append(agent.execute(mapped_input))

        # Create agent execution records before execution
        agent_execs = []
        for step in valid_steps:
            agent_exec = await self._create_agent_execution(step)
            agent_execs.append(agent_exec)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update agent execution records with results
        for i, result in enumerate(results):
            if i < len(agent_execs):
                if isinstance(result, Exception):
                    await self._update_agent_execution(agent_execs[i], StepResult(
                        agent_name=valid_steps[i].agent.name,
                        success=False,
                        error=str(result),
                    ))
                    opinions.append({'error': str(result)})
                elif result.success:
                    await self._update_agent_execution(agent_exec, result)
                    opinions.append({
                        'agent': result.agent_name,
                        'opinion': result.output,
                    })

        # Synthesize consensus
        synthesis_prompt = f"""You are synthesizing multiple expert opinions into a consensus view.

Expert Opinions:
{json.dumps(opinions, default=str)}

Original Input:
{json.dumps(input_data, default=str)}

Provide a balanced consensus that:
1. Identifies common themes
2. Highlights areas of disagreement
3. Provides a final unified recommendation"""

        messages = [
            PromptMessage(role='user', content=synthesis_prompt)
        ]

        synthesis_response = await self.ai_gateway.chat(messages)

        return {
            'pattern': 'consensus',
            'opinions': opinions,
            'synthesis': synthesis_response.content,
            'step_results': [r.to_dict() for r in results if not isinstance(r, Exception)],
        }

    async def _execute_debate(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
    ) -> Dict:
        """Execute debate-style analysis with opposing stances."""
        stances = ['bullish', 'bearish', 'neutral']
        debates = []

        for i, step in enumerate(steps):
            agent_config = self._agent_cache.get(step.agent.name)
            if not agent_config:
                continue

            stance = stances[i % len(stances)]
            mapped_input = self._map_input(step.input_mapping, {**input_data, **context})
            agent = DebateAgent(agent_config, self.ai_gateway, stance=stance)
            # Create agent execution record
            agent_exec = await self._create_agent_execution(step)
            result = await agent.execute(mapped_input)
            # Update agent execution record
            await self._update_agent_execution(agent_exec, result)

            if result.success:
                debates.append(result.output)

        # Moderator synthesis (direct AI call, not an agent step)
        moderator_prompt = f"""You are a debate moderator synthesizing opposing views.

Debate Arguments:
{json.dumps(debates, default=str)}

Original Topic:
{json.dumps(input_data, default=str)}

Provide:
1. Summary of each position
2. Strengths and weaknesses of each argument
3. Balanced final assessment"""

        messages = [
            PromptMessage(role='user', content=moderator_prompt)
        ]

        moderator_response = await self.ai_gateway.chat(messages)

        return {
            'pattern': 'debate',
            'debates': debates,
            'moderator_synthesis': moderator_response.content,
        }

    async def _execute_hierarchical(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        context: Dict,
    ) -> Dict:
        """Execute hierarchical workflow with coordinator."""
        step_results = []

        # Find coordinator agent
        coordinator_step = None
        worker_steps = []

        for step in steps:
            if step.agent.role == 'coordinator':
                coordinator_step = step
            else:
                worker_steps.append(step)

        if not coordinator_step:
            return await self._execute_pipeline(steps, input_data, context)

        # Coordinator plans the work
        coordinator_config = self._agent_cache.get(coordinator_step.agent.name)
        if coordinator_config:
            plan_prompt = f"""You are a coordinator planning task execution.

Available workers: {[s.agent.name for s in worker_steps]}
Input data: {json.dumps(input_data, default=str)}

Create a plan specifying:
1. Which workers to use
2. What each worker should do
3. Execution order (parallel or sequential)"""

            messages = [
                PromptMessage(role='user', content=plan_prompt)
            ]

            plan_response = await self.ai_gateway.chat(messages)

            # Filter to valid worker steps
            valid_worker_steps = []
            worker_tasks = []
            for step in worker_steps:
                agent_config = self._agent_cache.get(step.agent.name)
                if agent_config:
                    valid_worker_steps.append(step)
                    mapped_input = self._map_input(step.input_mapping, {**input_data, **context})
                    agent = PipelineAgent(agent_config, self.ai_gateway)
                    worker_tasks.append(agent.execute(mapped_input))

            # Create agent execution records before execution
            worker_execs = []
            for step in valid_worker_steps:
                agent_exec = await self._create_agent_execution(step)
                worker_execs.append(agent_exec)

            worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

            # Update agent execution records with results
            for i, result in enumerate(worker_results):
                if i < len(worker_execs):
                    if isinstance(result, Exception):
                        await self._update_agent_execution(worker_execs[i], StepResult(
                            agent_name=valid_worker_steps[i].agent.name,
                            success=False,
                            error=str(result),
                        ))
                    else:
                        await self._update_agent_execution(worker_execs[i], result)

            # Coordinator synthesizes results
            worker_outputs = []
            for r in worker_results:
                if isinstance(r, Exception):
                    worker_outputs.append({'error': str(r)})
                elif r.success:
                    worker_outputs.append({
                        'agent': r.agent_name,
                        'output': r.output,
                    })

            synthesize_prompt = f"""Based on the work completed by your team:

Worker Outputs:
{json.dumps(worker_outputs, default=str)}

Original Input:
{json.dumps(input_data, default=str)}

Provide a final coordinated response."""

            messages = [
                PromptMessage(role='user', content=synthesize_prompt)
            ]

            final_response = await self.ai_gateway.chat(messages)

            return {
                'pattern': 'hierarchical',
                'plan': plan_response.content,
                'worker_results': worker_outputs,
                'final_synthesis': final_response.content,
            }

        return {'pattern': 'hierarchical', 'error': 'No coordinator found'}

    def _map_input(self, mapping: Dict, context: Dict) -> Dict:
        """Map input based on step configuration."""
        if not mapping:
            return context

        mapped = {}
        for key, source in mapping.items():
            if source.startswith('$'):
                # Reference to context variable
                var_name = source[1:]
                mapped[key] = context.get(var_name)
            else:
                mapped[key] = source

        return mapped if mapped else context

    async def _create_agent_execution(self, step: WorkflowStep) -> Optional[AgentExecution]:
        """Create an agent execution record."""
        if not self._execution:
            return None

        try:
            def _create():
                return AgentExecution.objects.create(
                    workflow_execution=self._execution,
                    step=step,
                    agent=step.agent,
                    status='running',
                    input_data={},
                    started_at=datetime.now(),
                )
            return await asyncio.to_thread(_create)
        except Exception as e:
            logger.error(f"Failed to create agent execution: {e}")
            return None

    async def _update_agent_execution(
        self,
        agent_exec: Optional[AgentExecution],
        result: StepResult,
    ):
        """Update an agent execution record with results."""
        if not agent_exec:
            return

        try:
            def _update():
                agent_exec.status = 'completed' if result.success else 'failed'
                agent_exec.output_data = result.output if result.success else {}
                agent_exec.error_message = result.error or ''
                agent_exec.provider = result.provider or ''
                agent_exec.model = result.model or ''
                agent_exec.tokens_used = result.tokens_used
                agent_exec.latency_ms = result.latency_ms
                agent_exec.completed_at = datetime.now()
                agent_exec.save()
            await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Failed to update agent execution: {e}")

    async def run_single_agent(
        self,
        agent_name: str,
        input_data: Dict,
        context: Dict = None,
    ) -> Dict:
        """Run a single agent directly."""
        agent_config = self._agent_cache.get(agent_name)
        if not agent_config:
            return {'error': f'Agent not found: {agent_name}'}

        full_context = {**(context or {}), **input_data}
        agent = PipelineAgent(agent_config, self.ai_gateway)
        result = await agent.execute(full_context)

        return result.to_dict()

    async def get_workflow_history(self, workflow_id: str, limit: int = 10) -> List[Dict]:
        """Get workflow execution history."""
        def _fetch():
            return list(WorkflowExecution.objects.filter(
                workflow_id=workflow_id
            ).order_by('-created_at')[:limit])

        executions = await asyncio.to_thread(_fetch)

        return [
            {
                'id': str(e.id),
                'status': e.status,
                'started_at': e.started_at.isoformat() if e.started_at else None,
                'completed_at': e.completed_at.isoformat() if e.completed_at else None,
                'total_tokens': e.total_tokens,
                'total_latency_ms': e.total_latency_ms,
            }
            for e in executions
        ]


# Global orchestrator instance (initialized with ai_gateway)
_orchestrator: Optional[AIOrchestrator] = None


async def get_orchestrator(ai_gateway) -> AIOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator(ai_gateway)
        await _orchestrator.initialize()
    return _orchestrator

"""AI Engine views."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    AIProvider, AIModel, AIRequest, AIMemory,
    AgentDefinition, Workflow, WorkflowStep,
    WorkflowExecution, AgentExecution
)
from .serializers import (
    AIProviderSerializer, AIModelSerializer,
    AIRequestSerializer, AIMemorySerializer,
    AIAnalysisSerializer, AIChatSerializer,
    AgentDefinitionSerializer, WorkflowSerializer,
    WorkflowStepSerializer, WorkflowExecutionSerializer,
    AgentExecutionSerializer, OrchestratorRequestSerializer,
    SingleAgentRequestSerializer
)
from .services.ai_gateway import ai_gateway
from .services.orchestrator import get_orchestrator
from .providers.base import PromptMessage
from .prompts import prompt_library
import asyncio


class AIProviderViewSet(viewsets.ModelViewSet):
    """Manage AI providers."""
    queryset = AIProvider.objects.all()
    serializer_class = AIProviderSerializer
    filterset_fields = ['provider_type', 'is_active']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available providers."""
        asyncio.run(ai_gateway.initialize())
        providers = ai_gateway.manager.get_available_providers()
        return Response(providers)

    @action(detail=False, methods=['get'])
    def health(self, request):
        """Check provider health."""
        asyncio.run(ai_gateway.initialize())
        health = asyncio.run(ai_gateway.health_check())
        return Response(health)


class AIModelViewSet(viewsets.ModelViewSet):
    """Manage AI models."""
    queryset = AIModel.objects.select_related('provider').all()
    serializer_class = AIModelSerializer
    filterset_fields = ['provider', 'is_active']


class AIRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """View AI requests."""
    queryset = AIRequest.objects.all()
    serializer_class = AIRequestSerializer
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class AIMemoryViewSet(viewsets.ModelViewSet):
    """Manage AI memory."""
    queryset = AIMemory.objects.all()
    serializer_class = AIMemorySerializer
    filterset_fields = ['category']
    search_fields = ['content']

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search AI memory."""
        query = request.data.get('query', '')
        category = request.data.get('category')
        limit = request.data.get('limit', 10)

        results = asyncio.run(ai_gateway.search_memory(query, category, limit))
        return Response(results)


class AIAnalysisViewSet(viewsets.ViewSet):
    """AI analysis endpoint."""

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Run AI analysis."""
        serializer = AIAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            response = asyncio.run(ai_gateway.analyze(
                prompt_name=data['prompt_name'],
                variables=data['variables'],
                provider=data.get('provider'),
                model=data.get('model'),
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2000),
            ))

            return Response({
                'content': response.content,
                'model': response.model,
                'provider': response.provider,
                'tokens_used': response.tokens_used,
                'latency_ms': response.latency_ms,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def chat(self, request):
        """Direct AI chat."""
        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            messages = [
                PromptMessage(role=m['role'], content=m['content'])
                for m in data['messages']
            ]

            response = asyncio.run(ai_gateway.chat(
                messages=messages,
                provider=data.get('provider'),
                model=data.get('model'),
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2000),
            ))

            return Response({
                'content': response.content,
                'model': response.model,
                'provider': response.provider,
                'tokens_used': response.tokens_used,
                'latency_ms': response.latency_ms,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def prompts(self, request):
        """List available prompts."""
        prompts = prompt_library.list_prompts()
        return Response(prompts)


class AgentDefinitionViewSet(viewsets.ModelViewSet):
    """Manage AI agent definitions."""
    queryset = AgentDefinition.objects.all()
    serializer_class = AgentDefinitionSerializer
    filterset_fields = ['role', 'is_active']
    search_fields = ['name', 'description']


class WorkflowViewSet(viewsets.ModelViewSet):
    """Manage AI workflows."""
    queryset = Workflow.objects.prefetch_related('steps__agent').all()
    serializer_class = WorkflowSerializer
    filterset_fields = ['pattern', 'is_active']
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a workflow."""
        workflow = self.get_object()
        serializer = OrchestratorRequestSerializer(data={
            'workflow_id': str(workflow.id),
            **request.data
        })
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            orchestrator = asyncio.run(get_orchestrator(ai_gateway))
            result = asyncio.run(orchestrator.run_workflow(
                workflow_id=str(workflow.id),
                input_data=data['input_data'],
                context=data.get('context', {}),
            ))
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get workflow execution history."""
        workflow = self.get_object()
        limit = request.query_params.get('limit', 10)

        try:
            orchestrator = asyncio.run(get_orchestrator(ai_gateway))
            history = asyncio.run(orchestrator.get_workflow_history(
                workflow_id=str(workflow.id),
                limit=int(limit)
            ))
            return Response(history)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WorkflowStepViewSet(viewsets.ModelViewSet):
    """Manage workflow steps."""
    queryset = WorkflowStep.objects.select_related('agent', 'workflow').all()
    serializer_class = WorkflowStepSerializer
    filterset_fields = ['workflow', 'agent']


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """View workflow executions."""
    queryset = WorkflowExecution.objects.select_related('workflow').all()
    serializer_class = WorkflowExecutionSerializer
    filterset_fields = ['workflow', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """View agent executions."""
    queryset = AgentExecution.objects.select_related('agent', 'workflow_execution').all()
    serializer_class = AgentExecutionSerializer
    filterset_fields = ['agent', 'status']
    ordering_fields = ['started_at']
    ordering = ['-started_at']


class OrchestratorViewSet(viewsets.ViewSet):
    """AI Orchestrator endpoint."""

    @action(detail=False, methods=['get'])
    def agents(self, request):
        """List available agents from orchestrator cache."""
        try:
            orchestrator = asyncio.run(get_orchestrator(ai_gateway))
            agents = [
                {
                    'name': config.name,
                    'role': config.role,
                    'capabilities': config.capabilities,
                }
                for config in orchestrator._agent_cache.values()
            ]
            return Response(agents)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def patterns(self, request):
        """List available workflow patterns."""
        patterns = [
            {'name': 'pipeline', 'description': 'Sequential execution, output feeds next step'},
            {'name': 'parallel', 'description': 'All agents run simultaneously'},
            {'name': 'consensus', 'description': 'All agents analyze, then synthesize consensus'},
            {'name': 'debate', 'description': 'Agents take opposing stances, moderator synthesizes'},
            {'name': 'hierarchical', 'description': 'Coordinator plans, workers execute'},
        ]
        return Response(patterns)

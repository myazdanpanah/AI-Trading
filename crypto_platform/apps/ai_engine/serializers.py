"""AI Engine serializers."""
from rest_framework import serializers
from .models import (
    AIProvider, AIModel, AIRequest, AIMemory,
    AgentDefinition, Workflow, WorkflowStep,
    WorkflowExecution, AgentExecution
)


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = '__all__'
        extra_kwargs = {'api_key': {'write_only': True}}


class AIModelSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = AIModel
        fields = '__all__'


class AIRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequest
        fields = '__all__'


class AIMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMemory
        fields = '__all__'


class AIAnalysisSerializer(serializers.Serializer):
    """Serializer for AI analysis requests."""
    prompt_name = serializers.CharField()
    variables = serializers.DictField()
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    temperature = serializers.FloatField(default=0.7, min_value=0, max_value=2)
    max_tokens = serializers.IntegerField(default=2000, min_value=100, max_value=10000)


class AIChatSerializer(serializers.Serializer):
    """Serializer for AI chat requests."""
    messages = serializers.ListField(child=serializers.DictField())
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    temperature = serializers.FloatField(default=0.7)
    max_tokens = serializers.IntegerField(default=2000)


# Orchestrator Serializers

class AgentDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for Agent definitions."""
    class Meta:
        model = AgentDefinition
        fields = '__all__'


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Serializer for Workflow steps."""
    agent_name = serializers.CharField(source='agent.name', read_only=True)

    class Meta:
        model = WorkflowStep
        fields = '__all__'


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow definitions."""
    steps = WorkflowStepSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = '__all__'


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """Serializer for Workflow execution."""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = '__all__'


class AgentExecutionSerializer(serializers.ModelSerializer):
    """Serializer for Agent execution."""
    agent_name = serializers.CharField(source='agent.name', read_only=True)

    class Meta:
        model = AgentExecution
        fields = '__all__'


class OrchestratorRequestSerializer(serializers.Serializer):
    """Serializer for orchestrator requests."""
    workflow_id = serializers.UUIDField()
    input_data = serializers.DictField()
    context = serializers.DictField(required=False, default=dict)


class SingleAgentRequestSerializer(serializers.Serializer):
    """Serializer for single agent requests."""
    agent_name = serializers.CharField()
    input_data = serializers.DictField()
    context = serializers.DictField(required=False, default=dict)

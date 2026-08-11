from django.contrib import admin
from .models import (
    AIProvider, AIModel, AIRequest, AIMemory,
    AgentDefinition, Workflow, WorkflowStep,
    WorkflowExecution, AgentExecution
)


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'priority', 'created_at']
    list_filter = ['provider_type', 'is_active']
    search_fields = ['name']


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_id', 'context_size', 'is_active']
    list_filter = ['provider', 'is_active']
    search_fields = ['name']


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ['status', 'tokens_used', 'latency_ms', 'created_at']
    list_filter = ['status']
    ordering = ['-created_at']


@admin.register(AIMemory)
class AIMemoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'content', 'created_at']
    list_filter = ['category']
    search_fields = ['content']


@admin.register(AgentDefinition)
class AgentDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'preferred_provider', 'preferred_model', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'pattern', 'is_active', 'max_iterations', 'timeout_seconds']
    list_filter = ['pattern', 'is_active']
    search_fields = ['name', 'description']


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'agent', 'step_order', 'output_key', 'is_optional']
    list_filter = ['workflow', 'agent']
    ordering = ['workflow', 'step_order']


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'status', 'started_at', 'completed_at', 'total_tokens']
    list_filter = ['status', 'workflow']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(AgentExecution)
class AgentExecutionAdmin(admin.ModelAdmin):
    list_display = ['agent', 'workflow_execution', 'status', 'provider', 'model', 'tokens_used']
    list_filter = ['status', 'agent']
    ordering = ['-started_at']
    readonly_fields = ['id']

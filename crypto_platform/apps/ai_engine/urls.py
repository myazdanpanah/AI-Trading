from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIProviderViewSet, AIModelViewSet,
    AIRequestViewSet, AIMemoryViewSet,
    AIAnalysisViewSet,
    AgentDefinitionViewSet, WorkflowViewSet,
    WorkflowStepViewSet, WorkflowExecutionViewSet,
    AgentExecutionViewSet, OrchestratorViewSet
)

router = DefaultRouter()
router.register(r'providers', AIProviderViewSet)
router.register(r'models', AIModelViewSet)
router.register(r'requests', AIRequestViewSet)
router.register(r'memory', AIMemoryViewSet)
router.register(r'analysis', AIAnalysisViewSet, basename='analysis')
router.register(r'agents', AgentDefinitionViewSet)
router.register(r'workflows', WorkflowViewSet)
router.register(r'workflow-steps', WorkflowStepViewSet)
router.register(r'workflow-executions', WorkflowExecutionViewSet)
router.register(r'agent-executions', AgentExecutionViewSet)
router.register(r'orchestrator', OrchestratorViewSet, basename='orchestrator')

urlpatterns = [
    path('', include(router.urls)),
]

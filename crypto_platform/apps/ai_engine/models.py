"""AI Engine models."""
import uuid
from django.db import models


class AIProvider(models.Model):
    """AI provider configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider_type = models.CharField(
        max_length=20,
        choices=[
            ('ollama', 'Ollama'),
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('openrouter', 'OpenRouter'),
            ('localai', 'LocalAI'),
        ]
    )
    base_url = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI provider'
        verbose_name_plural = 'AI providers'
        db_table = 'ai_providers'
        ordering = ['-priority']

    def __str__(self):
        return self.name


class AIModel(models.Model):
    """AI model configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    model_id = models.CharField(max_length=100)
    context_size = models.IntegerField(default=4096)
    cost_per_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    speed_score = models.IntegerField(default=50)
    quality_score = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI model'
        verbose_name_plural = 'AI models'
        db_table = 'ai_models'

    def __str__(self):
        return f"{self.provider.name} - {self.name}"


class AIRequest(models.Model):
    """AI request logging."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    prompt = models.TextField()
    response = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI request'
        verbose_name_plural = 'AI requests'
        db_table = 'ai_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Request {self.id} - {self.status}"


class AIMemory(models.Model):
    """AI memory with vector embeddings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    embedding = models.JSONField(null=True, blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('market_situation', 'Market Situation'),
            ('signal', 'Signal'),
            ('pattern', 'Pattern'),
            ('strategy', 'Strategy'),
            ('mistake', 'Mistake'),
        ]
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI memory'
        verbose_name_plural = 'AI memories'
        db_table = 'ai_memory'
        ordering = ['-created_at']

    def __str__(self):
        return f"Memory: {self.content[:50]}..."


class AgentDefinition(models.Model):
    """AI Agent definition for orchestration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('market_analyst', 'Market Analyst'),
            ('news_analyst', 'News Analyst'),
            ('technical_analyst', 'Technical Analyst'),
            ('sentiment_analyst', 'Sentiment Analyst'),
            ('risk_analyst', 'Risk Analyst'),
            ('signal_generator', 'Signal Generator'),
            ('portfolio_manager', 'Portfolio Manager'),
            ('coordinator', 'Coordinator'),
            ('critic', 'Critic/Reviewer'),
        ]
    )
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    preferred_provider = models.CharField(max_length=50, blank=True)
    preferred_model = models.CharField(max_length=100, blank=True)
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    capabilities = models.JSONField(default=list, help_text='List of agent capabilities')
    dependencies = models.JSONField(default=list, help_text='Agent names this agent depends on')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agent definition'
        verbose_name_plural = 'Agent definitions'
        db_table = 'ai_agent_definitions'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Workflow(models.Model):
    """AI Workflow definition for multi-agent coordination."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    pattern = models.CharField(
        max_length=30,
        choices=[
            ('pipeline', 'Pipeline'),
            ('parallel', 'Parallel'),
            ('consensus', 'Consensus'),
            ('debate', 'Debate'),
            ('hierarchical', 'Hierarchical'),
            ('custom', 'Custom'),
        ],
        default='pipeline'
    )
    agents = models.ManyToManyField(AgentDefinition, through='WorkflowStep')
    is_active = models.BooleanField(default=True)
    max_iterations = models.IntegerField(default=5, help_text='Max iterations for iterative workflows')
    timeout_seconds = models.IntegerField(default=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'
        db_table = 'ai_workflows'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_pattern_display()})"


class WorkflowStep(models.Model):
    """Workflow step linking agents to workflows."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name='workflow_steps')
    step_order = models.IntegerField(default=0)
    input_mapping = models.JSONField(
        default=dict,
        help_text='Map step inputs to workflow variables or previous step outputs'
    )
    output_key = models.CharField(
        max_length=100, blank=True,
        help_text='Key to store this step output in workflow context'
    )
    is_optional = models.BooleanField(default=False)
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=2)

    class Meta:
        verbose_name = 'Workflow step'
        verbose_name_plural = 'Workflow steps'
        db_table = 'ai_workflow_steps'
        ordering = ['workflow', 'step_order']

    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_order}: {self.agent.name}"


class WorkflowExecution(models.Model):
    """Workflow execution tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    total_tokens = models.IntegerField(default=0)
    total_latency_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workflow execution'
        verbose_name_plural = 'Workflow executions'
        db_table = 'ai_workflow_executions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.workflow.name} - {self.status} ({self.created_at})"


class AgentExecution(models.Model):
    """Individual agent execution within a workflow."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='agent_executions')
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='executions')
    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped'),
        ],
        default='pending'
    )
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    provider = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=100, blank=True)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Agent execution'
        verbose_name_plural = 'Agent executions'
        db_table = 'ai_agent_executions'
        ordering = ['started_at']

    def __str__(self):
        return f"{self.agent.name} - {self.status}"

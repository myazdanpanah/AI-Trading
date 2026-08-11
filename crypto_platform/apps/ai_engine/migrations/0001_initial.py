"""Initial migration for AI Engine models."""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AIProvider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('provider_type', models.CharField(choices=[('ollama', 'Ollama'), ('openai', 'OpenAI'), ('anthropic', 'Anthropic'), ('openrouter', 'OpenRouter'), ('localai', 'LocalAI')], max_length=20)),
                ('base_url', models.URLField(blank=True)),
                ('api_key', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'AI provider',
                'verbose_name_plural': 'AI providers',
                'db_table': 'ai_providers',
                'ordering': ['-priority'],
            },
        ),
        migrations.CreateModel(
            name='AIModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('model_id', models.CharField(max_length=100)),
                ('context_size', models.IntegerField(default=4096)),
                ('cost_per_1k_tokens', models.DecimalField(decimal_places=6, default=0, max_digits=10)),
                ('speed_score', models.IntegerField(default=50)),
                ('quality_score', models.IntegerField(default=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='models', to='ai_engine.aiprovider')),
            ],
            options={
                'verbose_name': 'AI model',
                'verbose_name_plural': 'AI models',
                'db_table': 'ai_models',
            },
        ),
        migrations.CreateModel(
            name='AIRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('prompt', models.TextField()),
                ('response', models.TextField(blank=True)),
                ('tokens_used', models.IntegerField(default=0)),
                ('latency_ms', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('model', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ai_engine.aimodel')),
            ],
            options={
                'verbose_name': 'AI request',
                'verbose_name_plural': 'AI requests',
                'db_table': 'ai_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AIMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('embedding', models.JSONField(blank=True, null=True)),
                ('category', models.CharField(choices=[('market_situation', 'Market Situation'), ('signal', 'Signal'), ('pattern', 'Pattern'), ('strategy', 'Strategy'), ('mistake', 'Mistake')], max_length=50)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'AI memory',
                'verbose_name_plural': 'AI memories',
                'db_table': 'ai_memory',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentDefinition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('role', models.CharField(choices=[('market_analyst', 'Market Analyst'), ('news_analyst', 'News Analyst'), ('technical_analyst', 'Technical Analyst'), ('sentiment_analyst', 'Sentiment Analyst'), ('risk_analyst', 'Risk Analyst'), ('signal_generator', 'Signal Generator'), ('portfolio_manager', 'Portfolio Manager'), ('coordinator', 'Coordinator'), ('critic', 'Critic/Reviewer')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('system_prompt', models.TextField()),
                ('preferred_provider', models.CharField(blank=True, max_length=50)),
                ('preferred_model', models.CharField(blank=True, max_length=100)),
                ('temperature', models.FloatField(default=0.7)),
                ('max_tokens', models.IntegerField(default=2000)),
                ('capabilities', models.JSONField(default=list, help_text='List of agent capabilities')),
                ('dependencies', models.JSONField(default=list, help_text='Agent names this agent depends on')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Agent definition',
                'verbose_name_plural': 'Agent definitions',
                'db_table': 'ai_agent_definitions',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('pattern', models.CharField(choices=[('pipeline', 'Pipeline'), ('parallel', 'Parallel'), ('consensus', 'Consensus'), ('debate', 'Debate'), ('hierarchical', 'Hierarchical'), ('custom', 'Custom')], default='pipeline', max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('max_iterations', models.IntegerField(default=5, help_text='Max iterations for iterative workflows')),
                ('timeout_seconds', models.IntegerField(default=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Workflow',
                'verbose_name_plural': 'Workflows',
                'db_table': 'ai_workflows',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('step_order', models.IntegerField(default=0)),
                ('input_mapping', models.JSONField(default=dict, help_text='Map step inputs to workflow variables or previous step outputs')),
                ('output_key', models.CharField(blank=True, help_text='Key to store this step output in workflow context', max_length=100)),
                ('is_optional', models.BooleanField(default=False)),
                ('retry_on_failure', models.BooleanField(default=True)),
                ('max_retries', models.IntegerField(default=2)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_steps', to='ai_engine.agentdefinition')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='ai_engine.workflow')),
            ],
            options={
                'verbose_name': 'Workflow step',
                'verbose_name_plural': 'Workflow steps',
                'db_table': 'ai_workflow_steps',
                'ordering': ['workflow', 'step_order'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowExecution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('input_data', models.JSONField(default=dict)),
                ('output_data', models.JSONField(default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(null=True)),
                ('completed_at', models.DateTimeField(null=True)),
                ('total_tokens', models.IntegerField(default=0)),
                ('total_latency_ms', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='ai_engine.workflow')),
            ],
            options={
                'verbose_name': 'Workflow execution',
                'verbose_name_plural': 'Workflow executions',
                'db_table': 'ai_workflow_executions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentExecution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('skipped', 'Skipped')], default='pending', max_length=20)),
                ('input_data', models.JSONField(default=dict)),
                ('output_data', models.JSONField(default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('provider', models.CharField(blank=True, max_length=50)),
                ('model', models.CharField(blank=True, max_length=100)),
                ('tokens_used', models.IntegerField(default=0)),
                ('latency_ms', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(null=True)),
                ('completed_at', models.DateTimeField(null=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='ai_engine.agentdefinition')),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='ai_engine.workflowstep')),
                ('workflow_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_executions', to='ai_engine.workflowexecution')),
            ],
            options={
                'verbose_name': 'Agent execution',
                'verbose_name_plural': 'Agent executions',
                'db_table': 'ai_agent_executions',
                'ordering': ['started_at'],
            },
        ),
        migrations.AddField(
            model_name='workflow',
            name='agents',
            field=models.ManyToManyField(through='ai_engine.WorkflowStep', to='ai_engine.agentdefinition'),
        ),
    ]

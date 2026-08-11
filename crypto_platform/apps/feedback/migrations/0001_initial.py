"""Initial migration for feedback loop app."""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('signals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('symbol', models.CharField(db_index=True, max_length=20)),
                ('timeframe', models.CharField(max_length=10)),
                ('price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('technical_indicators', models.JSONField(default=dict, help_text='RSI, MACD, EMA, etc.')),
                ('sentiment_data', models.JSONField(default=dict, help_text='Fear/Greed, social sentiment')),
                ('news_summary', models.TextField(blank=True)),
                ('embedding', models.JSONField(default=list, help_text='Vector embedding for similarity search')),
                ('market_condition', models.CharField(blank=True, help_text='trending, ranging, volatile', max_length=50)),
                ('dominant_factor', models.CharField(blank=True, help_text='technical, sentiment, news', max_length=50)),
                ('confidence_at_time', models.FloatField(default=0.5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'market memory',
                'verbose_name_plural': 'market memories',
                'db_table': 'market_memories',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PatternMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pattern_type', models.CharField(choices=[('successful_long', 'Successful Long'), ('successful_short', 'Successful Short'), ('failed_long', 'Failed Long'), ('failed_short', 'Failed Short'), ('reversal', 'Reversal Pattern'), ('breakout', 'Breakout Pattern'), ('continuation', 'Continuation Pattern')], max_length=30)),
                ('symbol', models.CharField(db_index=True, max_length=20)),
                ('timeframe', models.CharField(max_length=10)),
                ('conditions', models.JSONField(default=dict, help_text='Market conditions when pattern occurred')),
                ('indicators', models.JSONField(default=dict, help_text='Technical indicators at pattern time')),
                ('sentiment_state', models.JSONField(default=dict, help_text='Sentiment indicators')),
                ('avg_return', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('win_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('sample_size', models.IntegerField(default=0)),
                ('avg_confidence', models.FloatField(default=0.5)),
                ('embedding', models.JSONField(default=list, help_text='Vector embedding for pattern matching')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'pattern memory',
                'verbose_name_plural': 'pattern memories',
                'db_table': 'pattern_memories',
                'ordering': ['-avg_return'],
            },
        ),
        migrations.CreateModel(
            name='LearningInsight',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('insight_type', models.CharField(choices=[('weight_adjustment', 'Weight Adjustment'), ('strategy_recommendation', 'Strategy Recommendation'), ('risk_alert', 'Risk Alert'), ('performance_analysis', 'Performance Analysis'), ('market_regime_change', 'Market Regime Change'), ('factor_importance', 'Factor Importance Change')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('confidence', models.FloatField(default=0.5, help_text='AI confidence in this insight')),
                ('impact_score', models.FloatField(default=0.5, help_text='Expected impact on future performance')),
                ('related_symbols', models.JSONField(default=list)),
                ('related_factors', models.JSONField(default=list)),
                ('supporting_evidence', models.JSONField(default=list, help_text='Data points supporting this insight')),
                ('was_implemented', models.BooleanField(default=False)),
                ('implementation_result', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'learning insight',
                'verbose_name_plural': 'learning insights',
                'db_table': 'learning_insights',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FeedbackCycle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cycle_type', models.CharField(choices=[('daily', 'Daily Review'), ('weekly', 'Weekly Review'), ('signal_based', 'Signal-Based'), ('regime_change', 'Regime Change'), ('manual', 'Manual Trigger')], max_length=30)),
                ('signals_evaluated', models.IntegerField(default=0)),
                ('signals_correct', models.IntegerField(default=0)),
                ('insights_generated', models.IntegerField(default=0)),
                ('weights_adjusted', models.BooleanField(default=False)),
                ('pre_cycle_accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('post_cycle_accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('summary', models.TextField(blank=True)),
                ('recommendations', models.JSONField(default=list)),
                ('status', models.CharField(choices=[('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='running', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'feedback cycle',
                'verbose_name_plural': 'feedback cycles',
                'db_table': 'feedback_cycles',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='SignalMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('signal_direction', models.CharField(max_length=20)),
                ('signal_confidence', models.IntegerField(default=50)),
                ('entry_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('stop_loss', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('take_profit', models.JSONField(default=list)),
                ('exit_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('actual_return', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('actual_return_percent', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('was_correct', models.BooleanField(default=False)),
                ('max_favorable', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('max_adverse', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('holding_period_hours', models.IntegerField(default=0)),
                ('factors_at_creation', models.JSONField(default=dict, help_text='All factor scores when signal was created')),
                ('lesson_learned', models.TextField(blank=True, help_text='AI-generated lesson from this signal')),
                ('similar_past_signals', models.JSONField(default=list, help_text='IDs of similar past signals')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('evaluated_at', models.DateTimeField(blank=True, null=True)),
                ('market_memory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='feedback.marketmemory')),
                ('signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memories', to='signals.signal')),
            ],
            options={
                'verbose_name': 'signal memory',
                'verbose_name_plural': 'signal memories',
                'db_table': 'signal_memories',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='marketmemory',
            index=models.Index(fields=['symbol', 'timeframe'], name='market_memo_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='marketmemory',
            index=models.Index(fields=['market_condition'], name='market_memo_condit_idx'),
        ),
    ]

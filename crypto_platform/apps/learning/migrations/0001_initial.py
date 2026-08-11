"""Initial migration for learning app."""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SignalResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('exit_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('profit_loss', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('profit_loss_percent', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('success', models.BooleanField(default=False)),
                ('duration_hours', models.IntegerField(default=0)),
                ('market_condition', models.CharField(blank=True, max_length=50)),
                ('evaluated_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('signal', models.ForeignKey(on_delete=models.CASCADE, related_name='results', to='signals.signal')),
            ],
            options={
                'verbose_name': 'signal result',
                'verbose_name_plural': 'signal results',
                'db_table': 'signal_results',
                'ordering': ['-evaluated_at'],
            },
        ),
        migrations.CreateModel(
            name='ModelPerformance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('model_name', models.CharField(max_length=100)),
                ('accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('precision_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('recall', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('f1_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('total_predictions', models.IntegerField(default=0)),
                ('correct_predictions', models.IntegerField(default=0)),
                ('date', models.DateField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'model performance',
                'verbose_name_plural': 'model performance',
                'db_table': 'model_performance',
                'unique_together': {('model_name', 'date')},
            },
        ),
        migrations.CreateModel(
            name='StrategyWeight',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('component', models.CharField(max_length=50, unique=True)),
                ('weight', models.DecimalField(decimal_places=2, default=10, max_digits=5)),
                ('performance_score', models.DecimalField(decimal_places=2, default=50, max_digits=5)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'strategy weight',
                'verbose_name_plural': 'strategy weights',
                'db_table': 'strategy_weights',
            },
        ),
        migrations.CreateModel(
            name='BacktestResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('strategy_name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=20)),
                ('timeframe', models.CharField(max_length=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('total_trades', models.IntegerField(default=0)),
                ('winning_trades', models.IntegerField(default=0)),
                ('losing_trades', models.IntegerField(default=0)),
                ('win_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('profit_factor', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('max_drawdown', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('sharpe_ratio', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('total_return', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('parameters', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'backtest result',
                'verbose_name_plural': 'backtest results',
                'db_table': 'learning_backtest_results',
                'ordering': ['-created_at'],
            },
        ),
    ]

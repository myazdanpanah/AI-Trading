"""Feedback Loop models - AI memory, similarity search, and self-improvement."""
import uuid
from django.db import models


class MarketMemory(models.Model):
    """Store market situations with vector embeddings for similarity search."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    
    # Market state snapshot
    price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    technical_indicators = models.JSONField(default=dict, help_text='RSI, MACD, EMA, etc.')
    sentiment_data = models.JSONField(default=dict, help_text='Fear/Greed, social sentiment')
    news_summary = models.TextField(blank=True)
    
    # Vector embedding for similarity search (768 dimensions for sentence-transformers)
    embedding = models.JSONField(default=list, help_text='Vector embedding for similarity search')
    
    # Context metadata
    market_condition = models.CharField(max_length=50, blank=True, help_text='trending, ranging, volatile')
    dominant_factor = models.CharField(max_length=50, blank=True, help_text='technical, sentiment, news')
    confidence_at_time = models.FloatField(default=0.5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'market memory'
        verbose_name_plural = 'market memories'
        db_table = 'market_memories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['symbol', 'timeframe']),
            models.Index(fields=['market_condition']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {self.market_condition}"


class SignalMemory(models.Model):
    """Store signal outcomes for learning from past decisions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='memories')
    market_memory = models.ForeignKey(MarketMemory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Signal snapshot at creation time
    signal_direction = models.CharField(max_length=20)
    signal_confidence = models.IntegerField(default=50)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.JSONField(default=list)
    
    # Outcome
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    actual_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    actual_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    was_correct = models.BooleanField(default=False)
    max_favorable = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_adverse = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    holding_period_hours = models.IntegerField(default=0)
    
    # Learning metadata
    factors_at_creation = models.JSONField(default=dict, help_text='All factor scores when signal was created')
    lesson_learned = models.TextField(blank=True, help_text='AI-generated lesson from this signal')
    similar_past_signals = models.JSONField(default=list, help_text='IDs of similar past signals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'signal memory'
        verbose_name_plural = 'signal memories'
        db_table = 'signal_memories'
        ordering = ['-created_at']

    def __str__(self):
        return f"Signal {self.signal_id} - {'Win' if self.was_correct else 'Loss'}"


class PatternMemory(models.Model):
    """Store successful and failed patterns for strategy improvement."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_type = models.CharField(
        max_length=30,
        choices=[
            ('successful_long', 'Successful Long'),
            ('successful_short', 'Successful Short'),
            ('failed_long', 'Failed Long'),
            ('failed_short', 'Failed Short'),
            ('reversal', 'Reversal Pattern'),
            ('breakout', 'Breakout Pattern'),
            ('continuation', 'Continuation Pattern'),
        ]
    )
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    
    # Pattern characteristics
    conditions = models.JSONField(default=dict, help_text='Market conditions when pattern occurred')
    indicators = models.JSONField(default=dict, help_text='Technical indicators at pattern time')
    sentiment_state = models.JSONField(default=dict, help_text='Sentiment indicators')
    
    # Performance metrics
    avg_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sample_size = models.IntegerField(default=0)
    avg_confidence = models.FloatField(default=0.5)
    
    # Embedding for similarity
    embedding = models.JSONField(default=list, help_text='Vector embedding for pattern matching')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'pattern memory'
        verbose_name_plural = 'pattern memories'
        db_table = 'pattern_memories'
        ordering = ['-avg_return']

    def __str__(self):
        return f"{self.pattern_type} - {self.symbol} ({self.sample_size} samples)"


class LearningInsight(models.Model):
    """Store AI-generated insights and recommendations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    insight_type = models.CharField(
        max_length=30,
        choices=[
            ('weight_adjustment', 'Weight Adjustment'),
            ('strategy_recommendation', 'Strategy Recommendation'),
            ('risk_alert', 'Risk Alert'),
            ('performance_analysis', 'Performance Analysis'),
            ('market_regime_change', 'Market Regime Change'),
            ('factor_importance', 'Factor Importance Change'),
        ]
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Impact and confidence
    confidence = models.FloatField(default=0.5, help_text='AI confidence in this insight')
    impact_score = models.FloatField(default=0.5, help_text='Expected impact on future performance')
    
    # Related data
    related_symbols = models.JSONField(default=list)
    related_factors = models.JSONField(default=list)
    supporting_evidence = models.JSONField(default=list, help_text='Data points supporting this insight')
    
    # Action taken
    was_implemented = models.BooleanField(default=False)
    implementation_result = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'learning insight'
        verbose_name_plural = 'learning insights'
        db_table = 'learning_insights'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.insight_type}: {self.title}"


class CandleData(models.Model):
    """Store OHLCV candle data for AI training and analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    
    # OHLCV data
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Technical indicators at this candle
    indicators = models.JSONField(default=dict, help_text='RSI, MACD, EMA, VWAP, etc.')
    
    # Pattern and context
    pattern = models.CharField(max_length=50, blank=True, help_text='Detected candle pattern')
    market_condition = models.CharField(max_length=50, blank=True)
    
    # Price change from previous candle
    price_change = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    price_change_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    volume_change_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Source
    source = models.CharField(max_length=50, default='binance', help_text='binance, coingecko, etc.')
    
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'candle data'
        verbose_name_plural = 'candle data'
        db_table = 'candle_data'
        ordering = ['-timestamp']
        unique_together = ['symbol', 'timeframe', 'timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.timeframe} @ {self.timestamp}"


class TrainingSample(models.Model):
    """AI training samples linking signals to outcomes with candle context."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal_memory = models.ForeignKey('SignalMemory', on_delete=models.CASCADE, related_name='training_samples')
    candle_data = models.ForeignKey(CandleData, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Input features for AI training
    input_features = models.JSONField(default=dict, help_text='Features used to make the prediction')
    
    # Expected output (what actually happened)
    actual_outcome = models.CharField(max_length=20, help_text='buy, sell, hold - what happened')
    actual_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Candle context at signal creation
    candle_open = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    candle_high = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    candle_low = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    candle_close = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    candle_volume = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Subsequent candles (for pattern learning)
    next_candles = models.JSONField(default=list, help_text='Next N candles after signal for pattern learning')
    
    # Training metadata
    was_correct = models.BooleanField(default=False)
    model_version = models.CharField(max_length=50, default='v1')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'training sample'
        verbose_name_plural = 'training samples'
        db_table = 'training_samples'
        ordering = ['-created_at']

    def __str__(self):
        return f"Sample for {self.signal_memory} - {'Correct' if self.was_correct else 'Wrong'}"


class FeedbackCycle(models.Model):
    """Track the complete feedback loop cycles."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle_type = models.CharField(
        max_length=30,
        choices=[
            ('daily', 'Daily Review'),
            ('weekly', 'Weekly Review'),
            ('signal_based', 'Signal-Based'),
            ('regime_change', 'Regime Change'),
            ('manual', 'Manual Trigger'),
        ]
    )
    
    # Cycle metrics
    signals_evaluated = models.IntegerField(default=0)
    signals_correct = models.IntegerField(default=0)
    insights_generated = models.IntegerField(default=0)
    weights_adjusted = models.BooleanField(default=False)
    
    # Performance comparison
    pre_cycle_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    post_cycle_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # AI summary
    summary = models.TextField(blank=True)
    recommendations = models.JSONField(default=list)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='running'
    )
    error_message = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'feedback cycle'
        verbose_name_plural = 'feedback cycles'
        db_table = 'feedback_cycles'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.cycle_type} - {self.status} at {self.started_at}"

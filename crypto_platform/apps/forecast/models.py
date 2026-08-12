"""Forecast models - Price predictions and verification tracking."""
from django.db import models
from django.utils import timezone


class PriceForecast(models.Model):
    """A single price forecast prediction."""
    
    SYMBOL_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('SOL', 'Solana'),
        ('BNB', 'BNB'),
        ('XRP', 'XRP'),
    ]
    
    DIRECTION_CHOICES = [
        ('UP', 'Up'),
        ('DOWN', 'Down'),
        ('SIDEWAYS', 'Sideways'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Forecast details
    symbol = models.CharField(max_length=10, choices=SYMBOL_CHOICES, default='BTC')
    current_price = models.FloatField(help_text='Price at time of forecast')
    predicted_price = models.FloatField(help_text='Predicted price at target time')
    predicted_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    confidence = models.FloatField(help_text='Confidence score 0-1')
    
    # Technical factors used
    technical_score = models.FloatField(default=50)
    regime_score = models.FloatField(default=50)
    momentum_score = models.FloatField(default=50)
    volatility_score = models.FloatField(default=50)
    
    # Timing
    forecast_time = models.DateTimeField(default=timezone.now)
    target_time = models.DateTimeField(help_text='When prediction should be checked')
    
    # Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    actual_price = models.FloatField(null=True, blank=True)
    actual_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, null=True, blank=True)
    price_error_pct = models.FloatField(null=True, blank=True)
    direction_correct = models.BooleanField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Scoring
    points_earned = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'price_forecasts'
        ordering = ['-forecast_time']
        indexes = [
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['forecast_time']),
            models.Index(fields=['target_time']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.predicted_direction} {self.confidence:.0%} @ ${self.predicted_price:,.2f}"
    
    def calculate_points(self):
        """Calculate points based on prediction accuracy."""
        if self.status != 'VERIFIED':
            return 0
        
        points = 0
        
        # Direction correct: +10 points
        if self.direction_correct:
            points += 10
            
            # Bonus for confidence when correct
            points += int(self.confidence * 5)
            
            # Bonus for accuracy
            if self.price_error_pct is not None:
                error = abs(self.price_error_pct)
                if error < 1:
                    points += 15  # Very accurate
                elif error < 3:
                    points += 10  # Good accuracy
                elif error < 5:
                    points += 5   # Decent accuracy
        else:
            # Wrong direction: lose points
            points -= 5
            
            # Less penalty for low confidence
            points += int((1 - self.confidence) * 3)
        
        self.points_earned = points
        self.save(update_fields=['points_earned'])
        return points


class ForecastCycle(models.Model):
    """Tracks each 6-hour forecast cycle."""
    
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    cycle_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    
    # Results
    forecasts_created = models.IntegerField(default=0)
    forecasts_verified = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0)
    avg_confidence = models.FloatField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Learning adjustments
    weights_before = models.JSONField(default=dict, help_text='Model weights before this cycle')
    weights_after = models.JSONField(default=dict, help_text='Model weights after learning')
    adjustments_made = models.JSONField(default=list, help_text='List of weight adjustments')
    
    execution_time_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'forecast_cycles'
        ordering = ['-cycle_time']
    
    def __str__(self):
        return f"Cycle {self.cycle_time.strftime('%Y-%m-%d %H:%M')} - {self.status}"


class ModelWeight(models.Model):
    """Tracks model weights that evolve over time through the feedback loop."""
    
    symbol = models.CharField(max_length=10, default='BTC')
    
    # Factor weights (should sum to 1.0)
    technical_weight = models.FloatField(default=0.35)
    sentiment_weight = models.FloatField(default=0.15)
    news_weight = models.FloatField(default=0.10)
    ai_weight = models.FloatField(default=0.25)
    macro_weight = models.FloatField(default=0.15)
    
    # Performance tracking
    total_predictions = models.IntegerField(default=0)
    correct_predictions = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0)
    
    # Confidence calibration
    avg_confidence_when_correct = models.FloatField(default=0.5)
    avg_confidence_when_wrong = models.FloatField(default=0.5)
    
    # Learning rate
    adjustment_count = models.IntegerField(default=0)
    last_adjustment = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'model_weights'
        unique_together = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} weights: T={self.technical_weight:.2f} S={self.sentiment_weight:.2f} N={self.news_weight:.2f} AI={self.ai_weight:.2f} M={self.macro_weight:.2f}"
    
    def update_accuracy(self, correct: bool):
        """Update accuracy tracking."""
        self.total_predictions += 1
        if correct:
            self.correct_predictions += 1
        self.accuracy_rate = (self.correct_predictions / self.total_predictions * 100) if self.total_predictions > 0 else 0
        self.save(update_fields=['total_predictions', 'correct_predictions', 'accuracy_rate'])
    
    def get_weights_dict(self):
        """Return weights as a dictionary."""
        return {
            'technical': self.technical_weight,
            'sentiment': self.sentiment_weight,
            'news': self.news_weight,
            'ai': self.ai_weight,
            'macro': self.macro_weight,
        }

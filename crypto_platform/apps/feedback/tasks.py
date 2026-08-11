"""Feedback Loop Celery tasks for automated feedback cycles."""
import logging
from celery import shared_task
from datetime import datetime as datetime_class
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='feedback.run_daily_cycle')
def run_daily_feedback_cycle(self):
    """Run daily feedback cycle - analyze recent signals and generate insights."""
    from .services import FeedbackOrchestrator
    
    try:
        logger.info("Starting daily feedback cycle")
        result = FeedbackOrchestrator.run_feedback_cycle(
            cycle_type='daily',
            lookback_days=1,
        )
        logger.info(f"Daily feedback cycle completed: {result.get('cycle_id')}")
        return result
    except Exception as e:
        logger.error(f"Daily feedback cycle failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, name='feedback.run_weekly_cycle')
def run_weekly_feedback_cycle(self):
    """Run weekly feedback cycle - comprehensive analysis and weight adjustments."""
    from .services import FeedbackOrchestrator
    
    try:
        logger.info("Starting weekly feedback cycle")
        result = FeedbackOrchestrator.run_feedback_cycle(
            cycle_type='weekly',
            lookback_days=7,
        )
        logger.info(f"Weekly feedback cycle completed: {result.get('cycle_id')}")
        return result
    except Exception as e:
        logger.error(f"Weekly feedback cycle failed: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=3)


@shared_task(bind=True, name='feedback.record_signal_outcome')
def record_signal_outcome_task(self, signal_id, exit_price, profit_loss_percent, holding_period_hours=0):
    """Record a signal outcome for learning."""
    from .models import SignalMemory, MarketMemory
    from signals.models import Signal
    
    try:
        signal = Signal.objects.get(id=signal_id)
        
        # Find associated market memory
        market_memory = MarketMemory.objects.filter(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
        ).order_by('-created_at').first()
        
        signal_memory = SignalMemory.objects.create(
            signal=signal,
            market_memory=market_memory,
            signal_direction=signal.direction,
            signal_confidence=signal.confidence,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            exit_price=exit_price,
            actual_return=Decimal('0'),
            actual_return_percent=Decimal(str(profit_loss_percent)),
            was_correct=profit_loss_percent > 0,
            holding_period_hours=holding_period_hours,
            factors_at_creation={
                'technical_score': float(signal.technical_score),
                'sentiment_score': float(signal.sentiment_score),
                'news_score': float(signal.news_score),
                'ai_score': float(signal.ai_score),
                'macro_score': float(signal.macro_score),
                'composite_score': float(signal.composite_score),
            },
            evaluated_at=datetime_class.now(),
        )
        
        logger.info(f"Recorded signal outcome: {signal_id} - {'Win' if signal_memory.was_correct else 'Loss'}")
        return {'signal_memory_id': str(signal_memory.id), 'was_correct': signal_memory.was_correct}
    except Exception as e:
        logger.error(f"Failed to record signal outcome: {e}")
        raise


@shared_task(bind=True, name='feedback.generate_market_memory')
def generate_market_memory_task(self, symbol, timeframe, price, market_data):
    """Generate a market memory embedding for future similarity search."""
    from .models import MarketMemory
    from .services import SimilaritySearchService
    
    try:
        embedding = SimilaritySearchService.calculate_embedding(market_data)
        
        memory = MarketMemory.objects.create(
            symbol=symbol,
            timeframe=timeframe,
            price=price,
            volume=market_data.get('volume', 0),
            technical_indicators=market_data.get('technical_indicators', {}),
            sentiment_data=market_data.get('sentiment_data', {}),
            news_summary=market_data.get('news_summary', ''),
            embedding=embedding,
            market_condition=market_data.get('market_condition', ''),
            dominant_factor=market_data.get('dominant_factor', ''),
            confidence_at_time=market_data.get('confidence', 0.5),
        )
        
        logger.info(f"Generated market memory for {symbol} {timeframe}")
        return {'memory_id': str(memory.id)}
    except Exception as e:
        logger.error(f"Failed to generate market memory: {e}")
        raise


@shared_task(bind=True, name='feedback.cleanup_old_memories')
def cleanup_old_memories(self, days_to_keep=90):
    """Clean up old market memories to save database space."""
    from .models import MarketMemory, SignalMemory
    from datetime import timedelta
    
    try:
        cutoff_date = datetime_class.now() - timedelta(days=days_to_keep)
        
        # Keep memories that have been used in signal outcomes
        used_memory_ids = SignalMemory.objects.values_list('market_memory_id', flat=True).distinct()
        
        deleted_count, _ = MarketMemory.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(
            id__in=used_memory_ids
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old market memories")
        return {'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"Failed to cleanup old memories: {e}")
        raise


@shared_task(bind=True, name='feedback.auto_record_expired_signals')
def auto_record_expired_signals(self):
    """Automatically record outcomes for expired signals.
    
    This task runs periodically to check for signals that have expired
    and records their outcomes for the learning system.
    """
    from .models import SignalMemory
    from signals.models import Signal
    from datetime import timedelta
    
    try:
        # Find active signals that have expired (expires_at < now)
        expired_signals = Signal.objects.filter(
            is_active=True,
            expires_at__lt=datetime_class.now(),
            expires_at__isnull=False,
        ).exclude(
            id__in=SignalMemory.objects.values_list('signal_id', flat=True)
        )[:50]  # Process 50 at a time
        
        recorded_count = 0
        for signal in expired_signals:
            try:
                # Get current price from market data
                from market.models import Candle
                
                latest_candle = Candle.objects.filter(
                    symbol=signal.symbol,
                    timeframe=signal.timeframe,
                ).order_by('-timestamp').first()
                
                if latest_candle:
                    exit_price = latest_candle.close
                    
                    # Calculate profit/loss
                    if signal.direction in ('buy', 'strong_buy'):
                        profit_loss_percent = float((exit_price - signal.entry_price) / signal.entry_price * 100)
                    else:
                        profit_loss_percent = float((signal.entry_price - exit_price) / signal.entry_price * 100)
                    
                    # Calculate holding period
                    holding_hours = int((datetime_class.now() - signal.created_at).total_seconds() / 3600)
                    
                    # Record the outcome
                    record_signal_outcome_task.delay(
                        signal_id=str(signal.id),
                        exit_price=float(exit_price),
                        profit_loss_percent=profit_loss_percent,
                        holding_period_hours=holding_hours,
                    )
                    
                    # Mark signal as inactive
                    signal.is_active = False
                    signal.save(update_fields=['is_active'])
                    
                    recorded_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to record expired signal {signal.id}: {e}")
                continue
        
        logger.info(f"Auto-recorded {recorded_count} expired signal outcomes")
        return {'recorded_count': recorded_count}
    except Exception as e:
        logger.error(f"Failed to auto-record expired signals: {e}")
        raise

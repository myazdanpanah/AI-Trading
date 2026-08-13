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


@shared_task(bind=True, name='feedback.collect_candles')
def collect_candles_task(self, symbols=None, timeframe='1h', limit=100):
    """Collect candle data for AI training."""
    from .services.candle_collector import candle_collector
    
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    
    results = []
    for symbol in symbols:
        try:
            result = candle_collector.collect_candles(symbol, timeframe, limit)
            results.append(result)
            logger.info(f"Collected candles for {symbol}: {result.get('stored', 0)} new")
        except Exception as e:
            logger.error(f"Failed to collect candles for {symbol}: {e}")
            results.append({'symbol': symbol, 'error': str(e)})
    
    # Create training samples from recent signal memories
    from .models import SignalMemory, TrainingSample
    from apps.feedback.services.candle_collector import candle_collector
    
    recent_memories = SignalMemory.objects.filter(
        evaluated_at__isnull=False,
        training_samples__isnull=True
    )[:20]
    
    samples_created = 0
    for memory in recent_memories:
        try:
            candle_collector.create_training_sample(memory)
            samples_created += 1
        except Exception as e:
            logger.warning(f"Failed to create training sample: {e}")
    
    return {
        'candles_collected': sum(r.get('stored', 0) for r in results if 'stored' in r),
        'training_samples_created': samples_created,
        'symbols': symbols,
    }


@shared_task(bind=True, name='feedback.record_signal_outcome')
def record_signal_outcome_task(self, signal_id, exit_price, profit_loss_percent, holding_period_hours=0):
    """Record a signal outcome for learning."""
    from .models import SignalMemory, MarketMemory
    from apps.signals.models import Signal
    
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


@shared_task(bind=True, name='signals.generate_hourly')
def generate_signals_hourly(self):
    """Generate new signals for all watchlist symbols every hour."""
    try:
        logger.info("Starting hourly signal generation")
        from apps.signals.services import SignalGenerator
        from apps.signals.services.signal_evaluator import SignalEvaluator
        from apps.market.services.unified_data import fetch_market_data
        from apps.technical_analysis.services.indicator_engine import IndicatorEngine
        from apps.journal.services.journal_writer import fetch_fear_greed_index
        
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']
        generated = 0
        
        for symbol in symbols:
            try:
                # Fetch live data
                market = fetch_market_data(symbol)
                closes = market['closes'][-50:]
                highs = market['highs'][-50:]
                lows = market['lows'][-50:]
                volumes = market['volumes'][-50:]
                current_price = market['current_price']
                
                # Run indicators
                indicators = IndicatorEngine.calculate_all_indicators(
                    [{'close': c, 'high': h, 'low': l, 'volume': v}
                     for c, h, l, v in zip(closes, highs, lows, volumes)]
                )
                
                # Build technical data
                rsi_data = indicators.get('rsi_14', {})
                macd_data = indicators.get('macd', {})
                ema9 = indicators.get('ema_9', {})
                ema21 = indicators.get('ema_21', {})
                ema50 = indicators.get('ema_50', {})
                vwap_data = indicators.get('vwap', {})
                ichimoku_data = indicators.get('ichimoku', {})
                atr_data = indicators.get('atr_14', {})
                
                if ema9.get('signal') == 'bullish' and ema21.get('signal') == 'bullish':
                    trend = 'strong_uptrend'
                elif ema9.get('signal') == 'bullish' or ema50.get('signal') == 'bullish':
                    trend = 'uptrend'
                elif ema9.get('signal') == 'bearish' and ema21.get('signal') == 'bearish':
                    trend = 'strong_downtrend'
                elif ema9.get('signal') == 'bearish' or ema50.get('signal') == 'bearish':
                    trend = 'downtrend'
                else:
                    trend = 'neutral'
                
                technical_data = {
                    'rsi': rsi_data.get('value', 50),
                    'macd_signal': macd_data.get('trend', 'neutral'),
                    'trend': trend,
                    'vwap_signal': vwap_data.get('signal', 'neutral'),
                    'vwap_deviation': vwap_data.get('deviation', 0),
                    'ichimoku_signal': ichimoku_data.get('signal', 'neutral'),
                    'volume_signal': 'normal',
                    'sr_signal': 'neutral',
                    'volatility': atr_data.get('percent', 2),
                    'atr': atr_data.get('value', current_price * 0.02),
                }
                
                # Gather ALL data sources (news, social, macro, AI)
                from apps.signals.services.data_enricher import SignalDataEnricher
                enriched = SignalDataEnricher.enrich(
                    symbol=symbol,
                    technical_data=technical_data,
                    current_price=float(current_price),
                )
                sentiment_data = enriched['sentiment_data']
                news_data = enriched['news_data']
                macro_data = enriched['macro_data']
                ai_data = enriched['ai_data']
                
                logger.info(f"{symbol} enriched: news={news_data.get('article_count',0)} articles, "
                           f"ai={ai_data.get('prediction','?')}, macro={macro_data.get('market_regime','?')}")
                
                # Generate signal with ALL 5 factors
                gen = SignalGenerator()
                result = gen.generate_signal(
                    symbol=symbol, timeframe='1h',
                    technical_data=technical_data,
                    sentiment_data=sentiment_data,
                    news_data=news_data,
                    ai_data=ai_data,
                    macro_data=macro_data,
                    current_price=current_price,
                )
                
                # Save to database
                from apps.signals.models import Signal, SignalReason, SignalGenerationRequest
                from django.db import transaction
                
                with transaction.atomic():
                    entry_price_val = result.get('entry_price', 0) or 0
                    stop_loss_val = result.get('stop_loss', 0) or entry_price_val * 0.97
                    
                    signal = Signal.objects.create(
                        symbol=result['symbol'],
                        direction=result['direction'],
                        confidence=result['confidence'],
                        risk_score=result['risk_score'],
                        entry_price=float(entry_price_val),
                        stop_loss=float(stop_loss_val),
                        take_profit=result.get('take_profit', []),
                        timeframe=result['timeframe'],
                        technical_score=result['factor_scores'].get('technical', 0),
                        sentiment_score=result['factor_scores'].get('sentiment', 0),
                        news_score=result['factor_scores'].get('news', 0),
                        ai_score=result['factor_scores'].get('ai', 0),
                        macro_score=result['factor_scores'].get('macro', 0),
                        composite_score=result['composite_score'],
                        is_active=True,
                    )
                    
                    for reason in result.get('reasons', []):
                        SignalReason.objects.create(
                            signal=signal,
                            reason_type=reason.get('type', 'technical'),
                            description=reason.get('description', ''),
                            confidence=reason.get('confidence', 50),
                        )
                
                generated += 1
                logger.info(f"Generated {symbol} signal: {result['direction']} ({result['confidence']}%)")
                
            except Exception as e:
                logger.error(f"Failed to generate signal for {symbol}: {e}")
                continue
        
        logger.info(f"Hourly generation complete: {generated}/{len(symbols)} signals generated")
        return {'generated': generated, 'total': len(symbols)}
    except Exception as e:
        logger.error(f"Hourly signal generation failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, name='signals.adjust_weights_daily')
def adjust_weights_daily(self):
    """Adjust signal generator weights based on performance data."""
    try:
        logger.info("Starting daily weight adjustment")
        from apps.signals.services.weight_adjuster import WeightAdjuster
        
        result = WeightAdjuster.adjust_weights(lookback_days=30)
        
        logger.info(f"Weight adjustment complete: {result.get('status')}, "
                    f"weights changed: {result.get('weights_changed', False)}")
        
        return result
    except Exception as e:
        logger.error(f"Daily weight adjustment failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, name='feedback.evaluate_signals_hourly')
def evaluate_signals_hourly(self):
    """Evaluate pending signals every hour and record outcomes for learning."""
    try:
        logger.info("Starting hourly signal evaluation")
        from apps.signals.services.signal_evaluator import SignalEvaluator
        
        results = SignalEvaluator.evaluate_pending_signals(min_age_hours=1)
        
        logger.info(f"Hourly evaluation complete: {results['evaluated']} signals evaluated, "
                    f"{results['wins']} wins, {results['losses']} losses, "
                    f"win rate: {results['win_rate']:.1f}%")
        
        return results
    except Exception as e:
        logger.error(f"Hourly signal evaluation failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, name='feedback.auto_record_expired_signals')
def auto_record_expired_signals(self):
    """Automatically record outcomes for expired signals.
    
    This task runs periodically to check for signals that have expired
    and records their outcomes for the learning system.
    """
    from .models import SignalMemory
    from apps.signals.models import Signal
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
                from apps.market.models import Candle
                
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

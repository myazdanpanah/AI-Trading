"""Price Forecaster - Generates price predictions using technical analysis and model weights."""
import time
import logging
from datetime import timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction

from apps.technical_analysis.services.indicator_engine import IndicatorEngine
from apps.market.services.unified_data import fetch_market_data, fetch_ticker
from ..models import PriceForecast, ForecastCycle, ModelWeight

logger = logging.getLogger(__name__)


class PriceForecaster:
    """Generates price forecasts every 6 hours using technical analysis + learned weights."""
    
    # Forecast horizons
    FORECAST_HORIZONS = {
        'short': 6,    # 6 hours
        'medium': 24,  # 24 hours  
        'long': 72,    # 72 hours (3 days)
    }
    
    @classmethod
    def run_forecast_cycle(cls, symbols: List[str] = None) -> Dict:
        """
        Run a complete forecast cycle for all symbols.
        This is called every 6 hours.
        """
        start = time.time()
        
        if symbols is None:
            symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']
        
        cycle = ForecastCycle.objects.create(
            cycle_time=timezone.now(),
            status='RUNNING',
        )
        
        try:
            forecasts = []
            
            for symbol in symbols:
                try:
                    symbol_forecasts = cls._forecast_symbol(symbol)
                    forecasts.extend(symbol_forecasts)
                except Exception as e:
                    logger.error(f"Failed to forecast {symbol}: {e}")
                    continue
            
            # Save all forecasts in a transaction
            with transaction.atomic():
                for f in forecasts:
                    f.save()
            
            # Update cycle
            cycle.forecasts_created = len(forecasts)
            cycle.avg_confidence = sum(f.confidence for f in forecasts) / len(forecasts) if forecasts else 0
            cycle.status = 'COMPLETED'
            cycle.execution_time_ms = int((time.time() - start) * 1000)
            cycle.save()
            
            return {
                'status': 'success',
                'cycle_id': cycle.id,
                'forecasts_created': len(forecasts),
                'symbols': symbols,
                'execution_time_ms': cycle.execution_time_ms,
                'forecasts': [cls._forecast_to_dict(f) for f in forecasts],
            }
            
        except Exception as e:
            cycle.status = 'FAILED'
            cycle.error_message = str(e)
            cycle.save()
            logger.error(f"Forecast cycle failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @classmethod
    def _forecast_symbol(cls, symbol: str) -> List[PriceForecast]:
        """Generate forecasts for a single symbol."""
        forecasts = []
        
        # Fetch market data
        market = fetch_market_data(symbol)
        closes = market['closes']
        highs = market['highs']
        lows = market['lows']
        volumes = market['volumes']
        current_price = market['current_price']
        
        if len(closes) < 50:
            logger.warning(f"Not enough data for {symbol}: {len(closes)} candles")
            return []
        
        # Run technical analysis
        from apps.trading_skills.services.skills_engine import analyze_technical
        technical = analyze_technical(closes, highs, lows)
        
        # Calculate indicators
        all_indicators = IndicatorEngine.calculate_all_indicators(
            [{'close': c, 'high': h, 'low': l, 'volume': v}
             for c, h, l, v in zip(closes[-100:], highs[-100:], lows[-100:], volumes[-100:])]
        )
        
        # Get model weights for this symbol
        model_weights = cls._get_model_weights(symbol)
        
        # Calculate composite score
        tech_score = technical.get('overall_score', 50)
        trend_score = technical.get('trend', {}).get('score', 50)
        momentum_score = technical.get('momentum', {}).get('score', 50)
        volatility_score = technical.get('volatility', {}).get('score', 50)
        
        # VWAP and Ichimoku adjustments
        vwap = all_indicators.get('vwap', {})
        ichimoku = all_indicators.get('ichimoku', {})
        
        vwap_adjustment = 0
        if vwap.get('signal') == 'bullish':
            vwap_adjustment = 5
        elif vwap.get('signal') == 'bearish':
            vwap_adjustment = -5
        
        ichimoku_adjustment = 0
        if ichimoku.get('signal') == 'strong_bullish':
            ichimoku_adjustment = 8
        elif ichimoku.get('signal') == 'bullish':
            ichimoku_adjustment = 4
        elif ichimoku.get('signal') == 'strong_bearish':
            ichimoku_adjustment = -8
        elif ichimoku.get('signal') == 'bearish':
            ichimoku_adjustment = -4
        
        # Weighted composite score
        composite_score = (
            tech_score * model_weights.technical_weight +
            trend_score * 0.2 +
            momentum_score * 0.15 +
            volatility_score * 0.1
        ) + vwap_adjustment + ichimoku_adjustment
        
        composite_score = max(0, min(100, composite_score))
        
        # Calculate predicted prices for each horizon
        atr = cls._calculate_atr(closes, highs, lows, period=14)
        atr_pct = atr / current_price if current_price > 0 else 0.02
        
        for horizon_name, horizon_hours in cls.FORECAST_HORIZONS.items():
            # Determine direction and magnitude
            if composite_score >= 65:
                direction = 'UP'
                magnitude = (composite_score - 50) / 100 * atr_pct * (horizon_hours / 6)
                confidence = min(0.9, 0.5 + (composite_score - 50) / 100 * 0.8)
            elif composite_score <= 35:
                direction = 'DOWN'
                magnitude = (50 - composite_score) / 100 * atr_pct * (horizon_hours / 6)
                confidence = min(0.9, 0.5 + (50 - composite_score) / 100 * 0.8)
            else:
                direction = 'SIDEWAYS'
                magnitude = atr_pct * 0.3 * (horizon_hours / 6)
                confidence = 0.4 + (1 - abs(composite_score - 50) / 50) * 0.2
            
            predicted_price = current_price * (1 + magnitude if direction == 'UP' else 1 - magnitude if direction == 'DOWN' else 1)
            
            forecast = PriceForecast(
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                predicted_direction=direction,
                confidence=confidence,
                technical_score=tech_score,
                regime_score=composite_score,
                momentum_score=momentum_score,
                volatility_score=volatility_score,
                forecast_time=timezone.now(),
                target_time=timezone.now() + timedelta(hours=horizon_hours),
                status='PENDING',
            )
            forecasts.append(forecast)
        
        return forecasts
    
    @classmethod
    def _get_model_weights(cls, symbol: str) -> ModelWeight:
        """Get or create model weights for a symbol."""
        weights, created = ModelWeight.objects.get_or_create(
            symbol=symbol,
            defaults={
                'technical_weight': 0.35,
                'sentiment_weight': 0.15,
                'news_weight': 0.10,
                'ai_weight': 0.25,
                'macro_weight': 0.15,
            }
        )
        return weights
    
    @classmethod
    def _calculate_atr(cls, closes, highs, lows, period=14):
        """Calculate Average True Range."""
        if len(closes) < period + 1:
            return closes[-1] * 0.02 if closes else 0
        
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_ranges.append(max(high_low, high_close, low_close))
        
        return sum(true_ranges[-period:]) / period if true_ranges else 0
    
    @classmethod
    def _forecast_to_dict(cls, forecast: PriceForecast) -> Dict:
        """Convert forecast to dictionary."""
        return {
            'id': forecast.id,
            'symbol': forecast.symbol,
            'current_price': forecast.current_price,
            'predicted_price': forecast.predicted_price,
            'direction': forecast.predicted_direction,
            'confidence': forecast.confidence,
            'scores': {
                'technical': forecast.technical_score,
                'regime': forecast.regime_score,
                'momentum': forecast.momentum_score,
                'volatility': forecast.volatility_score,
            },
            'forecast_time': forecast.forecast_time.isoformat(),
            'target_time': forecast.target_time.isoformat(),
            'status': forecast.status,
        }

"""Forecast Verifier - Checks predictions against real market data."""
import time
import logging
from typing import Dict, List
from django.utils import timezone
from django.db import transaction

from apps.market.services.unified_data import fetch_ticker
from ..models import PriceForecast, ForecastCycle

logger = logging.getLogger(__name__)


class ForecastVerifier:
    """Verifies forecast predictions against actual market data."""
    
    @classmethod
    def verify_pending_forecasts(cls) -> Dict:
        """
        Check all pending forecasts that have passed their target time.
        Returns verification results.
        """
        start = time.time()
        
        now = timezone.now()
        
        # Get all pending forecasts past their target time
        pending = PriceForecast.objects.filter(
            status='PENDING',
            target_time__lte=now,
        )
        
        if not pending.exists():
            return {
                'status': 'no_pending',
                'message': 'No forecasts ready for verification',
            }
        
        # Group by symbol to minimize API calls
        symbol_groups = {}
        for forecast in pending:
            if forecast.symbol not in symbol_groups:
                symbol_groups[forecast.symbol] = []
            symbol_groups[forecast.symbol].append(forecast)
        
        results = {
            'verified': 0,
            'correct': 0,
            'incorrect': 0,
            'accuracy_rate': 0,
            'details': [],
        }
        
        with transaction.atomic():
            for symbol, forecasts in symbol_groups.items():
                try:
                    # Get current price for this symbol
                    ticker = fetch_ticker(symbol)
                    actual_price = ticker.get('price', 0)
                    
                    if actual_price <= 0:
                        logger.warning(f"Could not get price for {symbol}")
                        continue
                    
                    for forecast in forecasts:
                        verification = cls._verify_forecast(forecast, actual_price)
                        results['details'].append(verification)
                        results['verified'] += 1
                        
                        if verification['direction_correct']:
                            results['correct'] += 1
                        else:
                            results['incorrect'] += 1
                            
                except Exception as e:
                    logger.error(f"Failed to verify {symbol} forecasts: {e}")
                    continue
        
        # Calculate accuracy
        if results['verified'] > 0:
            results['accuracy_rate'] = (results['correct'] / results['verified']) * 100
        
        results['execution_time_ms'] = int((time.time() - start) * 1000)
        results['status'] = 'success'
        
        return results
    
    @classmethod
    def _verify_forecast(cls, forecast: PriceForecast, actual_price: float) -> Dict:
        """Verify a single forecast against actual price."""
        # Calculate actual direction
        price_change = actual_price - forecast.current_price
        pct_change = (price_change / forecast.current_price * 100) if forecast.current_price > 0 else 0
        
        if pct_change > 0.5:
            actual_direction = 'UP'
        elif pct_change < -0.5:
            actual_direction = 'DOWN'
        else:
            actual_direction = 'SIDEWAYS'
        
        # Check if direction was correct
        direction_correct = (forecast.predicted_direction == actual_direction)
        
        # Calculate price error
        price_error = abs(actual_price - forecast.predicted_price)
        price_error_pct = (price_error / forecast.current_price * 100) if forecast.current_price > 0 else 0
        
        # Update forecast
        forecast.actual_price = actual_price
        forecast.actual_direction = actual_direction
        forecast.price_error_pct = price_error_pct
        forecast.direction_correct = direction_correct
        forecast.status = 'VERIFIED'
        forecast.verified_at = timezone.now()
        
        # Calculate points
        forecast.calculate_points()
        
        return {
            'forecast_id': forecast.id,
            'symbol': forecast.symbol,
            'predicted_direction': forecast.predicted_direction,
            'actual_direction': actual_direction,
            'direction_correct': direction_correct,
            'predicted_price': forecast.predicted_price,
            'actual_price': actual_price,
            'price_error_pct': price_error_pct,
            'confidence': forecast.confidence,
            'points_earned': forecast.points_earned,
        }
    
    @classmethod
    def get_accuracy_stats(cls, symbol: str = None, days: int = 30) -> Dict:
        """Get accuracy statistics for verified forecasts."""
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days)
        query = PriceForecast.objects.filter(
            status='VERIFIED',
            verified_at__gte=cutoff,
        )
        
        if symbol:
            query = query.filter(symbol=symbol)
        
        total = query.count()
        correct = query.filter(direction_correct=True).count()
        
        if total == 0:
            return {
                'total': 0,
                'correct': 0,
                'accuracy_rate': 0,
                'avg_confidence': 0,
                'avg_error_pct': 0,
                'total_points': 0,
            }
        
        from django.db.models import Avg, Sum
        stats = query.aggregate(
            avg_confidence=Avg('confidence'),
            avg_error=Avg('price_error_pct'),
            total_points=Sum('points_earned'),
        )
        
        return {
            'total': total,
            'correct': correct,
            'accuracy_rate': (correct / total * 100),
            'avg_confidence': stats['avg_confidence'] or 0,
            'avg_error_pct': stats['avg_error'] or 0,
            'total_points': stats['total_points'] or 0,
        }

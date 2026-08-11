"""Performance Tracker - Signal outcome tracking and analysis."""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Sum, Q, F

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks signal outcomes, calculates performance metrics,
    and provides analysis for strategy improvement.
    """
    
    def __init__(self):
        self.metrics_cache = {}
    
    def record_signal_outcome(
        self,
        signal_id: str,
        exit_price: Decimal,
        profit_loss: Decimal,
        profit_loss_percent: Decimal,
        success: bool,
        duration_hours: int,
        market_condition: str = '',
        notes: str = '',
    ) -> Dict:
        """
        Record the outcome of a trading signal.
        
        Returns:
            Dict with recorded outcome details
        """
        from ..models import SignalResult
        
        signal_result = SignalResult.objects.create(
            signal_id=signal_id,
            exit_price=exit_price,
            profit_loss=profit_loss,
            profit_loss_percent=profit_loss_percent,
            success=success,
            duration_hours=duration_hours,
            market_condition=market_condition,
            notes=notes,
        )
        
        logger.info(f"Recorded signal outcome: {signal_id} - {'Win' if success else 'Loss'}")
        
        return {
            'id': str(signal_result.id),
            'signal_id': str(signal_id),
            'exit_price': float(exit_price),
            'profit_loss': float(profit_loss),
            'profit_loss_percent': float(profit_loss_percent),
            'success': success,
            'duration_hours': duration_hours,
            'evaluated_at': signal_result.evaluated_at.isoformat(),
        }
    
    def get_signal_performance(
        self,
        symbol: str = None,
        timeframe: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict:
        """
        Calculate performance metrics for signals.
        
        Returns:
            Dict with comprehensive performance metrics
        """
        from ..models import SignalResult
        from signals.models import Signal
        
        # Build query
        query = Q()
        if symbol:
            query &= Q(signal__symbol=symbol)
        if timeframe:
            query &= Q(signal__timeframe=timeframe)
        if start_date:
            query &= Q(evaluated_at__gte=start_date)
        if end_date:
            query &= Q(evaluated_at__lte=end_date)
        
        results = SignalResult.objects.filter(query)
        
        # Calculate metrics
        total = results.count()
        if total == 0:
            return self._empty_metrics()
        
        wins = results.filter(success=True).count()
        losses = results.filter(success=False).count()
        
        avg_profit = results.aggregate(avg=Avg('profit_loss_percent'))['avg'] or Decimal('0')
        avg_win = results.filter(success=True).aggregate(avg=Avg('profit_loss_percent'))['avg'] or Decimal('0')
        avg_loss = results.filter(success=False).aggregate(avg=Avg('profit_loss_percent'))['avg'] or Decimal('0')
        
        total_profit = results.aggregate(total=Sum('profit_loss'))['total'] or Decimal('0')
        avg_duration = results.aggregate(avg=Avg('duration_hours'))['avg'] or 0
        
        win_rate = (wins / total * 100) if total > 0 else Decimal('0')
        
        # Calculate profit factor
        gross_profit = results.filter(success=True).aggregate(total=Sum('profit_loss'))['total'] or Decimal('0')
        gross_loss = abs(results.filter(success=False).aggregate(total=Sum('profit_loss'))['total'] or Decimal('0'))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else Decimal('0')
        
        # Calculate expectancy
        expectancy = (
            (Decimal(str(win_rate)) / 100 * avg_win) +
            ((100 - Decimal(str(win_rate))) / 100 * avg_loss)
        )
        
        # Calculate max consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive(results, success=True)
        max_consecutive_losses = self._calculate_max_consecutive(results, success=False)
        
        return {
            'total_signals': total,
            'wins': wins,
            'losses': losses,
            'win_rate': float(win_rate),
            'avg_profit_percent': float(avg_profit),
            'avg_win_percent': float(avg_win),
            'avg_loss_percent': float(avg_loss),
            'total_profit': float(total_profit),
            'profit_factor': float(profit_factor),
            'expectancy': float(expectancy),
            'avg_duration_hours': float(avg_duration),
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
        }
    
    def get_performance_by_factor(
        self,
        factor: str,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict:
        """
        Analyze performance by a specific factor (symbol, timeframe, market_condition).
        
        Returns:
            Dict with performance breakdown by factor values
        """
        from ..models import SignalResult
        from signals.models import Signal
        
        query = Q()
        if start_date:
            query &= Q(evaluated_at__gte=start_date)
        if end_date:
            query &= Q(evaluated_at__lte=end_date)
        
        # Get results with signal data
        results = SignalResult.objects.filter(query).select_related('signal')
        
        breakdown = {}
        for result in results:
            if factor == 'symbol':
                key = result.signal.symbol
            elif factor == 'timeframe':
                key = result.signal.timeframe
            elif factor == 'market_condition':
                key = result.market_condition or 'unknown'
            elif factor == 'direction':
                key = result.signal.direction
            else:
                continue
            
            if key not in breakdown:
                breakdown[key] = {
                    'total': 0, 'wins': 0, 'losses': 0,
                    'total_profit': Decimal('0'),
                }
            
            breakdown[key]['total'] += 1
            if result.success:
                breakdown[key]['wins'] += 1
            else:
                breakdown[key]['losses'] += 1
            breakdown[key]['total_profit'] += result.profit_loss
        
        # Calculate win rates
        for key in breakdown:
            data = breakdown[key]
            data['win_rate'] = float(
                (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            )
            data['total_profit'] = float(data['total_profit'])
        
        return breakdown
    
    def get_daily_performance(
        self,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get daily performance metrics for the last N days.
        
        Returns:
            List of daily performance records
        """
        from ..models import SignalResult
        
        start_date = datetime.now() - timedelta(days=days)
        results = SignalResult.objects.filter(
            evaluated_at__gte=start_date
        ).order_by('evaluated_at')
        
        daily = {}
        for result in results:
            day = result.evaluated_at.date().isoformat()
            if day not in daily:
                daily[day] = {
                    'date': day,
                    'total': 0, 'wins': 0, 'losses': 0,
                    'profit': Decimal('0'),
                }
            
            daily[day]['total'] += 1
            if result.success:
                daily[day]['wins'] += 1
            else:
                daily[day]['losses'] += 1
            daily[day]['profit'] += result.profit_loss
        
        # Convert to list
        result_list = []
        for day, data in sorted(daily.items()):
            data['win_rate'] = float(
                (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            )
            data['profit'] = float(data['profit'])
            result_list.append(data)
        
        return result_list
    
    def _calculate_max_consecutive(self, results, success: bool) -> int:
        """Calculate max consecutive wins or losses."""
        max_count = 0
        current_count = 0
        
        for result in results.order_by('evaluated_at'):
            if result.success == success:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no data available."""
        return {
            'total_signals': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'avg_profit_percent': 0,
            'avg_win_percent': 0,
            'avg_loss_percent': 0,
            'total_profit': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'avg_duration_hours': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
        }

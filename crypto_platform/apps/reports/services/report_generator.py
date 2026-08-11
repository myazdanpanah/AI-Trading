"""Advanced report generation service for analytics and reporting."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from dataclasses import dataclass, asdict
from django.db.models import Avg

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """A section within a report."""
    title: str
    content: Dict[str, Any]
    chart_data: Optional[List[Dict]] = None


@dataclass
class PerformanceReport:
    """Performance analysis report."""
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    signals: Dict[str, Any]
    portfolio: Dict[str, Any]
    risk_analysis: Dict[str, Any)
    recommendations: List[str]


@dataclass
class SignalReport:
    """Signal analysis report."""
    total_signals: int
    win_rate: float
    avg_confidence: float
    best_performing: List[Dict]
    worst_performing: List[Dict]
    factor_analysis: Dict[str, Any]


class ReportGenerator:
    """Generate various analytics reports."""
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.start_date = datetime.now() - timedelta(days=lookback_days)
    
    def generate_performance_report(
        self,
        symbol: Optional[str] = None
    ) -> PerformanceReport:
        """Generate comprehensive performance report."""
        from apps.learning.services import PerformanceTracker
        from apps.signals.models import Signal, SignalPerformance
        
        tracker = PerformanceTracker()
        
        # Get signal performance
        signal_perf = tracker.get_signal_performance(
            symbol=symbol,
            start_date=self.start_date,
        )
        
        # Get portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(symbol)
        
        # Risk analysis
        risk_analysis = self._analyze_risk(symbol)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(signal_perf, risk_analysis)
        
        return PerformanceReport(
            period_start=self.start_date,
            period_end=datetime.now(),
            summary=signal_perf.get('overall', {}),
            signals=signal_perf,
            portfolio=portfolio_metrics,
            risk_analysis=risk_analysis,
            recommendations=recommendations,
        )
    
    def generate_signal_report(
        self,
        symbol: Optional[str] = None
    ) -> SignalReport:
        """Generate signal analysis report."""
        from apps.signals.models import Signal, SignalPerformance
        from django.db.models import Avg, Count, F
        
        queryset = Signal.objects.filter(
            created_at__gte=self.start_date
        )
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        # Calculate metrics
        total = queryset.count()
        if total == 0:
            return SignalReport(
                total_signals=0,
                win_rate=0,
                avg_confidence=0,
                best_performing=[],
                worst_performing=[],
                factor_analysis={},
            )
        
        # Get performance data
        performances = SignalPerformance.objects.filter(
            signal__in=queryset
        )
        
        wins = performances.filter(success=True).count()
        win_rate = wins / total if total > 0 else 0
        
        avg_confidence = queryset.aggregate(
            avg_confidence=Avg('confidence')
        )['avg_confidence'] or 0
        
        # Best and worst performing
        best = list(queryset.order_by('-confidence')[:5].values(
            'symbol', 'direction', 'confidence', 'created_at'
        ))
        
        worst = list(queryset.order_by('confidence')[:5].values(
            'symbol', 'direction', 'confidence', 'created_at'
        ))
        
        # Factor analysis
        factor_analysis = self._analyze_factors(queryset)
        
        return SignalReport(
            total_signals=total,
            win_rate=win_rate,
            avg_confidence=float(avg_confidence),
            best_performing=best,
            worst_performing=worst,
            factor_analysis=factor_analysis,
        )
    
    def generate_sentiment_report(
        self,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate sentiment analysis report."""
        from apps.sentiment.models import SentimentData
        from apps.sentiment.services import SentimentAggregator
        
        aggregator = SentimentAggregator()
        
        # Get sentiment data
        sentiment_data = SentimentData.objects.filter(
            created_at__gte=self.start_date
        )
        
        if symbol:
            sentiment_data = sentiment_data.filter(symbol=symbol)
        
        # Aggregate sentiment
        avg_sentiment = sentiment_data.aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0
        
        # Fear & Greed Index
        fear_greed = aggregator.get_fear_greed_index()
        
        return {
            'period': {
                'start': self.start_date.isoformat(),
                'end': datetime.now().isoformat(),
            },
            'average_sentiment': float(avg_sentiment),
            'fear_greed_index': fear_greed,
            'data_points': sentiment_data.count(),
        }
    
    def _calculate_portfolio_metrics(
        self,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics."""
        from apps.signals.models import PortfolioPosition
        
        positions = PortfolioPosition.objects.filter(
            is_active=True,
            created_at__gte=self.start_date,
        )
        
        if symbol:
            positions = positions.filter(symbol=symbol)
        
        total_value = sum(
            float(p.quantity or 0) * float(p.current_price or 0)
            for p in positions
        )
        
        total_pnl = sum(
            float(p.unrealized_pnl or 0)
            for p in positions
        )
        
        return {
            'total_positions': positions.count(),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'roi_percent': (total_pnl / total_value * 100) if total_value > 0 else 0,
        }
    
    def _analyze_risk(
        self,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze portfolio risk."""
        from apps.signals.models import PortfolioPosition, Signal
        
        # Get recent signals for risk assessment
        signals = Signal.objects.filter(
            created_at__gte=self.start_date
        )
        
        if symbol:
            signals = signals.filter(symbol=symbol)
        
        avg_risk = signals.aggregate(
            avg_risk=Avg('risk_score')
        )['avg_risk'] or 0
        
        return {
            'average_risk_score': float(avg_risk),
            'risk_level': self._risk_level_from_score(float(avg_risk)),
            'max_drawdown': 0,  # TODO: Implement
            'volatility': 0,  # TODO: Implement
        }
    
    def _analyze_factors(
        self,
        queryset
    ) -> Dict[str, Any]:
        """Analyze factor performance."""
        from django.db.models import Avg
        
        return queryset.aggregate(
            avg_technical=Avg('technical_score'),
            avg_sentiment=Avg('sentiment_score'),
            avg_news=Avg('news_score'),
            avg_ai=Avg('ai_score'),
            avg_macro=Avg('macro_score'),
        )
    
    def _risk_level_from_score(self, score: float) -> str:
        """Convert risk score to risk level."""
        if score < 30:
            return 'low'
        elif score < 60:
            return 'medium'
        elif score < 80:
            return 'high'
        else:
            return 'critical'
    
    def _generate_recommendations(
        self,
        signal_perf: Dict,
        risk_analysis: Dict
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        win_rate = signal_perf.get('overall', {}).get('win_rate', 0)
        
        if win_rate < 0.5:
            recommendations.append(
                'Consider reducing position sizes or improving signal quality'
            )
        
        risk_level = risk_analysis.get('risk_level', 'medium')
        if risk_level in ['high', 'critical']:
            recommendations.append(
                'Portfolio risk is elevated - consider hedging or reducing exposure'
            )
        
        return recommendations


class ReportExporter:
    """Export reports to various formats."""
    
    @staticmethod
    def to_json(report: Any) -> str:
        """Export report to JSON."""
        import json
        from datetime import datetime
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if isinstance(obj, Decimal):
                    return float(obj)
                return super().default(obj)
        
        if hasattr(report, '__dataclass_fields__'):
            return json.dumps(asdict(report), cls=DateTimeEncoder, indent=2)
        return json.dumps(report, cls=DateTimeEncoder, indent=2)
    
    @staticmethod
    def to_csv(report: Any) -> str:
        """Export report to CSV."""
        import csv
        import io
        
        output = io.StringIO()
        
        if hasattr(report, '__dataclass_fields__'):
            data = asdict(report)
        else:
            data = report
        
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Metric', 'Value'])
        
        # Write data
        for key, value in data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    writer.writerow([f'{key}.{k}', v])
            else:
                writer.writerow([key, value])
        
        return output.getvalue()

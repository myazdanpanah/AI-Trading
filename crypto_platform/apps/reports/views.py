"""Report views - API endpoints for analytics reports."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .services.report_generator import ReportGenerator, ReportExporter

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Reports'], summary='List available reports'),
    create=extend_schema(tags=['Reports'], summary='Create a new report'),
    retrieve=extend_schema(tags=['Reports'], summary='Get a specific report'),
    update=extend_schema(tags=['Reports'], summary='Update a report'),
    partial_update=extend_schema(tags=['Reports'], summary='Partial update a report'),
    destroy=extend_schema(tags=['Reports'], summary='Delete a report'),
    performance=extend_schema(tags=['Reports'], summary='Generate performance report'),
    signals=extend_schema(tags=['Reports'], summary='Generate signal analysis report'),
    sentiment=extend_schema(tags=['Reports'], summary='Generate sentiment analysis report'),
    export=extend_schema(tags=['Reports'], summary='Export report to specified format'),
)
class ReportViewSet(viewsets.ViewSet):
    """ViewSet for report generation and management."""
    
    @action(detail=False, methods=['post'])
    def performance(self, request):
        """Generate performance report."""
        try:
            lookback_days = int(request.data.get('lookback_days', 30))
            symbol = request.data.get('symbol')
            
            generator = ReportGenerator(lookback_days=lookback_days)
            report = generator.generate_performance_report(symbol=symbol)
            
            return Response({
                'report': {
                    'period_start': report.period_start.isoformat(),
                    'period_end': report.period_end.isoformat(),
                    'summary': report.summary,
                    'signals': report.signals,
                    'portfolio': report.portfolio,
                    'risk_analysis': report.risk_analysis,
                    'recommendations': report.recommendations,
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def signals(self, request):
        """Generate signal analysis report."""
        try:
            lookback_days = int(request.data.get('lookback_days', 30))
            symbol = request.data.get('symbol')
            
            generator = ReportGenerator(lookback_days=lookback_days)
            report = generator.generate_signal_report(symbol=symbol)
            
            return Response({
                'report': {
                    'total_signals': report.total_signals,
                    'win_rate': report.win_rate,
                    'avg_confidence': report.avg_confidence,
                    'best_performing': report.best_performing,
                    'worst_performing': report.worst_performing,
                    'factor_analysis': report.factor_analysis,
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate signal report: {e}")
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def sentiment(self, request):
        """Generate sentiment analysis report."""
        try:
            lookback_days = int(request.data.get('lookback_days', 30))
            symbol = request.data.get('symbol')
            
            generator = ReportGenerator(lookback_days=lookback_days)
            report = generator.generate_sentiment_report(symbol=symbol)
            
            return Response({'report': report})
        except Exception as e:
            logger.error(f"Failed to generate sentiment report: {e}")
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export report to specified format."""
        try:
            report_type = request.data.get('report_type', 'performance')
            export_format = request.data.get('format', 'json')
            lookback_days = int(request.data.get('lookback_days', 30))
            symbol = request.data.get('symbol')
            
            generator = ReportGenerator(lookback_days=lookback_days)
            
            if report_type == 'performance':
                report = generator.generate_performance_report(symbol=symbol)
            elif report_type == 'signals':
                report = generator.generate_signal_report(symbol=symbol)
            elif report_type == 'sentiment':
                report = generator.generate_sentiment_report(symbol=symbol)
            else:
                return Response(
                    {'error': f'Unknown report type: {report_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Export to format
            if export_format == 'json':
                content = ReportExporter.to_json(report)
                content_type = 'application/json'
                file_ext = 'json'
            elif export_format == 'csv':
                content = ReportExporter.to_csv(report)
                content_type = 'text/csv'
                file_ext = 'csv'
            else:
                return Response(
                    {'error': f'Unknown format: {export_format}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from django.http import HttpResponse
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.{file_ext}"'
            
            return response
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return Response(
                {'error': f'Failed to export report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

"""Analytics views."""
from rest_framework import viewsets
from .models import Indicator, TechnicalPattern, CPRAnalysis, SmartMoneyEvent
from .serializers import IndicatorSerializer, TechnicalPatternSerializer, CPRAnalysisSerializer, SmartMoneyEventSerializer


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    filterset_fields = ['symbol', 'indicator_name', 'timeframe']


class TechnicalPatternViewSet(viewsets.ModelViewSet):
    queryset = TechnicalPattern.objects.all()
    serializer_class = TechnicalPatternSerializer
    filterset_fields = ['symbol', 'pattern']


class CPRAnalysisViewSet(viewsets.ModelViewSet):
    queryset = CPRAnalysis.objects.all()
    serializer_class = CPRAnalysisSerializer
    filterset_fields = ['symbol', 'timeframe']


class SmartMoneyEventViewSet(viewsets.ModelViewSet):
    queryset = SmartMoneyEvent.objects.all()
    serializer_class = SmartMoneyEventSerializer
    filterset_fields = ['symbol', 'event_type']

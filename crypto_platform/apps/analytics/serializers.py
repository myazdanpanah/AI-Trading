"""Analytics serializers."""
from rest_framework import serializers
from .models import Indicator, TechnicalPattern, CPRAnalysis, SmartMoneyEvent


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = '__all__'


class TechnicalPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalPattern
        fields = '__all__'


class CPRAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPRAnalysis
        fields = '__all__'


class SmartMoneyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartMoneyEvent
        fields = '__all__'

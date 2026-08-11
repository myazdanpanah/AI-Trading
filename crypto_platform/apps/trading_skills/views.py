"""API views for trading skills."""
import time
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import RegimeAnalysis, SignalReview, SkillUsageLog
from .services.skills_engine import TradingSkillsEngine


engine = TradingSkillsEngine()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def skill_definitions(request):
    """List all available trading skills."""
    return Response(engine.get_skill_definitions())


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_regime_analysis(request):
    """Run crypto regime analysis from provided market data."""
    start = time.time()

    market_data = request.data.get("market_data", {})
    if not market_data:
        return Response(
            {"error": "market_data is required. Provide series, funding, and dominance_series."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    import asyncio
    result = asyncio.run(engine.run_crypto_regime_analysis(market_data))

    # Save to database
    RegimeAnalysis.objects.create(
        composite_score=result.get("composite", {}).get("score"),
        zone=result.get("composite", {}).get("zone", "UNKNOWN"),
        guidance=result.get("composite", {}).get("guidance", ""),
        components=result.get("components", {}),
        exposure_posture=result.get("exposure", {}),
        universe_size=result.get("metadata", {}).get("universe_size", 0),
    )

    # Log usage
    SkillUsageLog.objects.create(
        skill_name="crypto_regime_analyzer",
        input_params={"universe_size": len(market_data.get("series", {}))},
        output_summary={"score": result.get("composite", {}).get("score"), "zone": result.get("composite", {}).get("zone")},
        execution_time_ms=int((time.time() - start) * 1000),
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_position_sizer(request):
    """Calculate position size."""
    start = time.time()

    params = request.data
    required = ["account_size", "risk_pct", "entry_price", "stop_loss_price"]
    missing = [f for f in required if f not in params]
    if missing:
        return Response(
            {"error": f"Missing required fields: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = engine.run_position_sizer(params)

    SkillUsageLog.objects.create(
        skill_name="position_sizer",
        input_params=params,
        output_summary={"position_size": result.get("position_size")},
        execution_time_ms=int((time.time() - start) * 1000),
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_technical_analysis(request):
    """Run technical analysis on price data."""
    start = time.time()

    closes = request.data.get("closes", [])
    highs = request.data.get("highs")
    lows = request.data.get("lows")

    if len(closes) < 20:
        return Response(
            {"error": "Need at least 20 data points for technical analysis"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = engine.run_technical_analysis(closes, highs, lows)

    SkillUsageLog.objects.create(
        skill_name="technical_analyst",
        input_params={"data_points": len(closes)},
        output_summary={"overall_score": result.get("overall_score")},
        execution_time_ms=int((time.time() - start) * 1000),
    )

    return Response(result)


class RegimeAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """View past regime analyses."""
    queryset = RegimeAnalysis.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RegimeAnalysis.objects.all()[:50]


class SignalReviewViewSet(viewsets.ModelViewSet):
    """Manage signal postmortem reviews."""
    queryset = SignalReview.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SignalReview.objects.filter(symbol=self.request.query_params.get('symbol', '')) \
            if self.request.query_params.get('symbol') \
            else SignalReview.objects.all()[:50]

    def perform_create(self, serializer):
        serializer.save()

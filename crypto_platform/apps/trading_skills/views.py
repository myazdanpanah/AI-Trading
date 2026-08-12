"""API views for trading skills."""
import time
import json
import math
import urllib.request
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import RegimeAnalysis, SignalReview, SkillUsageLog
from .services.skills_engine import (
    TradingSkillsEngine,
    calculate_btc_trend,
    calculate_alt_breadth,
    calculate_dominance_regime,
    calculate_funding_regime,
    calculate_drawdown_vol,
    calculate_momentum_thrust,
    calculate_composite_score,
    calculate_exposure_posture,
    analyze_technical,
    calculate_position_size,
)


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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def full_analysis(request):
    """
    Run complete analysis: fetch live data, run all skills, return combined results.
    Query params: symbol (default: BTC), account_size (default: 10000), risk_pct (default: 0.02)
    """
    start = time.time()
    symbol = request.query_params.get('symbol', 'BTC').upper()
    account_size = float(request.query_params.get('account_size', 10000))
    risk_pct = float(request.query_params.get('risk_pct', 0.02))

    try:
        # Fetch live data from CoinGecko
        coin_id_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'BNB': 'binancecoin', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOGE': 'dogecoin', 'DOT': 'polkadot', 'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
        }
        coin_id = coin_id_map.get(symbol, 'bitcoin')

        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=365&interval=daily'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=30)
        data = json.loads(r.read())
        closes = [p[1] for p in data['prices']]

        # Generate synthetic OHLCV
        import numpy as np
        np.random.seed(42)
        highs = [c * (1 + abs(np.random.normal(0, 0.015))) for c in closes]
        lows = [c * (1 - abs(np.random.normal(0, 0.015))) for c in closes]
        volumes = [float(np.random.uniform(1e9, 5e9)) for _ in closes]

        current_price = closes[-1]

        # === Run Skill 1: Regime Analyzer ===
        btc_closes = closes  # For BTC, this is the BTC data
        alt_series = {}
        if symbol != 'ETH':
            alt_series['ETH'] = closes
        if symbol != 'SOL':
            alt_series['SOL'] = [c * 0.05 for c in closes]

        dominance_data = [54, 54.5, 55, 54.8, 55.2, 54.5, 54.0, 53.8, 54.2, 53.5,
                          53.0, 52.8, 52.5, 52.2, 52.0, 51.8, 52.0, 51.5, 51.2, 51.0,
                          50.8, 50.5, 50.2, 50.0, 49.8, 49.5, 49.2, 49.0, 48.8, 48.5, 48.0]
        funding_data = {f'{symbol}USDT': 0.0001}
        momentum_series = {symbol: closes}
        if alt_series:
            momentum_series.update(alt_series)

        btc_trend = calculate_btc_trend(btc_closes)
        btc_trend_up = btc_trend.get('score', 50) >= 60

        components = {
            'btc_trend': btc_trend,
            'alt_breadth': calculate_alt_breadth(alt_series) if alt_series else {'score': 50, 'signal': 'N/A', 'data_available': False},
            'dominance': calculate_dominance_regime(dominance_data, btc_trend_up),
            'funding': calculate_funding_regime(funding_data),
            'drawdown_vol': calculate_drawdown_vol(btc_closes),
            'momentum_thrust': calculate_momentum_thrust(momentum_series),
        }

        composite = calculate_composite_score(components)
        exposure = calculate_exposure_posture({'composite': composite})

        # === Run Skill 2: Technical Analyst ===
        technical = analyze_technical(closes, highs, lows)

        # === Run Skill 3: Position Sizer ===
        atr_pct = 0.02
        sl = current_price * (1 - atr_pct)
        tp1 = current_price * (1 + atr_pct)
        tp2 = current_price * (1 + atr_pct * 1.5)
        tp3 = current_price * (1 + atr_pct * 2.5)

        position = calculate_position_size(
            account_size=account_size,
            risk_pct=risk_pct,
            entry_price=current_price,
            stop_loss_price=sl,
        )

        # === Final Verdict ===
        regime_score = composite.get('score', 50) or 50
        tech_score = technical.get('overall_score', 50)
        final_score = regime_score * 0.5 + tech_score * 0.5

        if final_score >= 75:
            verdict = 'STRONG BUY'
        elif final_score >= 60:
            verdict = 'BUY'
        elif final_score >= 40:
            verdict = 'HOLD'
        elif final_score >= 25:
            verdict = 'SELL'
        else:
            verdict = 'STRONG SELL'

        # Convert all to JSON-safe format
        def to_float(obj):
            if isinstance(obj, dict):
                return {k: to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [to_float(i) for i in obj]
            elif isinstance(obj, (np.floating, np.integer)):
                return float(obj)
            elif hasattr(obj, '__float__'):
                return float(obj)
            return obj

        result = {
            'symbol': symbol,
            'current_price': current_price,
            'data_points': len(closes),
            'high_365d': max(closes),
            'low_365d': min(closes),
            'regime': to_float({
                'components': {
                    'btc_trend': {'label': 'BTC Trend Structure', 'weight': '25%', **components['btc_trend']},
                    'alt_breadth': {'label': 'Alt Breadth', 'weight': '20%', **components['alt_breadth']},
                    'dominance': {'label': 'BTC Dominance', 'weight': '15%', **components['dominance']},
                    'funding': {'label': 'Funding Rate', 'weight': '15%', **components['funding']},
                    'drawdown_vol': {'label': 'Drawdown & Volatility', 'weight': '15%', **components['drawdown_vol']},
                    'momentum_thrust': {'label': 'Momentum Thrust', 'weight': '10%', **components['momentum_thrust']},
                },
                'composite': composite,
                'exposure': exposure,
            }),
            'technical': to_float(technical),
            'position': to_float({
                **position,
                'take_profits': [
                    {'level': 'TP1', 'price': tp1, 'pct': atr_pct * 100},
                    {'level': 'TP2', 'price': tp2, 'pct': atr_pct * 150},
                    {'level': 'TP3', 'price': tp3, 'pct': atr_pct * 250},
                ],
                'stop_loss': sl,
                'risk_pct': risk_pct,
                'account_size': account_size,
            }),
            'verdict': {
                'signal': verdict,
                'regime_score': round(regime_score, 1),
                'technical_score': round(tech_score, 1),
                'combined_score': round(final_score, 1),
                'posture': exposure['posture'],
                'max_exposure': exposure['max_exposure'],
            },
            'execution_time_ms': int((time.time() - start) * 1000),
        }

        return Response(result)

    except Exception as e:
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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

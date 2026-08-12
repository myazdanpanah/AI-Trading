"""API views for trading skills."""
import time
import json
import math
import urllib.request
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import RegimeAnalysis, SignalReview, SkillUsageLog
from apps.technical_analysis.services.indicator_engine import IndicatorEngine
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

def _fetch_market_data(symbol: str, coin_id: str = None, max_retries: int = 3):
    """Fetch market data using unified data service (Binance -> CoinGecko fallback)."""
    from apps.market.services.unified_data import fetch_market_data
    return fetch_market_data(symbol)


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
        # Fetch live data (Binance first, CoinGecko fallback)
        from apps.market.services.unified_data import fetch_market_data
        market = fetch_market_data(symbol)
        closes = market['closes']
        highs = market['highs']
        lows = market['lows']
        volumes = market['volumes']
        current_price = market['current_price']

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

        # === Calculate VWAP + Ichimoku (new indicators) ===
        all_indicators = IndicatorEngine.calculate_all_indicators(
            [{'close': c, 'high': h, 'low': l, 'volume': v}
             for c, h, l, v in zip(closes, highs, lows, volumes)]
        )
        vwap = all_indicators.get('vwap', {})
        ichimoku = all_indicators.get('ichimoku', {})

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

        # === Incorporate Feedback Performance Data ===
        feedback_adjustment = 0
        factor_performance = {}
        historical_win_rate = 0
        historical_signals = 0
        try:
            from apps.feedback.services.learning_agent import LearningAgent
            analysis_result = LearningAgent.analyze_performance(
                lookback_days=30, symbol=symbol, min_signals=1
            )
            if analysis_result.get('status') == 'complete':
                overall = analysis_result.get('overall', {})
                historical_win_rate = overall.get('win_rate', 0)
                historical_signals = overall.get('total_signals', 0)
                factor_performance = analysis_result.get('factor_analysis', {})
                # If we have historical win rates, use them to weight factors
                if factor_performance:
                    tech_wr = factor_performance.get('technical', {}).get('win_rate', 50)
                    sentiment_wr = factor_performance.get('sentiment', {}).get('win_rate', 50)
                    # Boost or reduce confidence based on historical accuracy
                    if historical_win_rate > 60:
                        feedback_adjustment = 5  # System has been accurate, boost confidence
                    elif historical_win_rate < 40:
                        feedback_adjustment = -5  # System has been inaccurate, reduce confidence
        except Exception:
            pass  # No feedback data yet, continue with default weights

        # === Final Verdict with feedback-adjusted scoring ===
        regime_score = composite.get('score', 50) or 50
        tech_score = technical.get('overall_score', 50)
        base_score = regime_score * 0.5 + tech_score * 0.5
        final_score = max(0, min(100, base_score + feedback_adjustment))

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
        import numpy as np
        def to_float(obj):
            if isinstance(obj, dict):
                return {k: to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [to_float(i) for i in obj]
            elif isinstance(obj, bool):
                return obj
            elif isinstance(obj, (np.floating, np.integer)):
                return float(obj)
            elif hasattr(obj, '__float__'):
                return float(obj)
            return obj

        result = {
            'symbol': symbol,
            'current_price': current_price,
            'data_source': market.get('source', 'unknown'),
            'data_points': len(closes),
            'high_365d': max(closes),
            'low_365d': min(closes),
            'historical_performance': to_float({
                'win_rate': historical_win_rate,
                'total_signals': historical_signals,
                'feedback_adjustment': feedback_adjustment,
                'factor_performance': factor_performance,
                'has_history': historical_signals > 0,
            }),
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
            'technical': to_float({**technical, 'vwap': vwap, 'ichimoku': ichimoku}),
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
                'confidence_adjustment': feedback_adjustment,
                'historical_accuracy': historical_win_rate,
            },
            'execution_time_ms': int((time.time() - start) * 1000),
        }

        return Response(result)

    except Exception as e:
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def chat_with_ai(request):
    """Chat with AI about trading decisions."""
    question = request.data.get('question', '')
    symbol = request.data.get('symbol', 'BTC')
    model = request.data.get('model', 'gemma4:latest')
    temperature = request.data.get('temperature', 0.7)
    history = request.data.get('history', [])  # Conversation history
    
    if not question:
        return Response(
            {'error': 'Question is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    from .services.chatbot import TradingChatBot
    result = TradingChatBot.answer(question, symbol, model=model, temperature=temperature, history=history)
    
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_candlestick_analysis(request):
    """Run candlestick pattern analysis on price data."""
    start = time.time()

    closes = request.data.get('closes', [])
    highs = request.data.get('highs', [])
    lows = request.data.get('lows', [])
    opens = request.data.get('opens')
    volumes = request.data.get('volumes')

    if len(closes) < 20:
        return Response(
            {'error': 'Need at least 20 data points for candlestick analysis'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = engine.run_technical_analysis(closes, highs, lows)
    
    # Also run candlestick analysis
    from .services.candlestick_skill import CandlestickSkill
    candlestick_result = CandlestickSkill.analyze(closes, highs, lows, opens, volumes)
    
    # Combine results
    result['candlestick'] = candlestick_result
    result['execution_time_ms'] = int((time.time() - start) * 1000)

    SkillUsageLog.objects.create(
        skill_name='candlestick_analyst',
        input_params={'data_points': len(closes)},
        output_summary={
            'patterns_found': len(candlestick_result.get('patterns', [])),
            'signals': len(candlestick_result.get('signals', [])),
        },
        execution_time_ms=result['execution_time_ms'],
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

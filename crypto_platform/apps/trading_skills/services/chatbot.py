"""
Trading ChatBot - Answers user questions about buying/selling with confidence rates.

Uses all trading skills to provide informed responses:
- Technical Analysis (trend, momentum, volatility)
- Candlestick Patterns (T.A.E. framework)
- Regime Analysis (market conditions)
- Position Sizing (risk management)

Supports configurable LLM model via settings.
"""
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradingChatBot:
    """
    AI ChatBot for trading decisions.
    
    Analyzes user questions and provides:
    - Clear BUY/SELL/HOLD recommendation
    - Confidence rate (0-100%)
    - Supporting evidence from technical analysis
    - Risk warnings
    """
    
    # Keywords for intent detection
    BUY_KEYWORDS = ['buy', 'long', 'purchase', 'enter', 'go up', 'bullish', 'accumulate', 'dca']
    SELL_KEYWORDS = ['sell', 'short', 'exit', 'close', 'go down', 'bearish', 'dump', 'liquidate']
    HOLD_KEYWORDS = ['hold', 'wait', 'keep', 'maintain', 'nothing', 'stay']
    ANALYSIS_KEYWORDS = ['analyze', 'analysis', 'what do you think', 'opinion', 'signal', 'predict', 'forecast']
    
    @classmethod
    def _get_ollama_model_info(cls, model_name: str = None) -> Dict:
        """Get information about the Ollama model being used."""
        try:
            import httpx
            import os
            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                if models:
                    # If a specific model is requested, use it; otherwise use first available
                    if model_name:
                        # Find the requested model in available models
                        for m in models:
                            if m.get('name', '') == model_name or m.get('name', '').startswith(model_name.split(':')[0]):
                                return {
                                    'model_name': m.get('name', model_name),
                                    'model_size': m.get('size', 0),
                                    'total_models': len(models),
                                    'all_models': [m.get('name', '') for m in models],
                                }
                        # If requested model not found, use first available
                        return {
                            'model_name': models[0].get('name', model_name),
                            'model_size': models[0].get('size', 0),
                            'total_models': len(models),
                            'all_models': [m.get('name', '') for m in models],
                            'requested_model_not_found': True,
                        }
                    else:
                        return {
                            'model_name': models[0].get('name', 'unknown'),
                            'model_size': models[0].get('size', 0),
                            'total_models': len(models),
                            'all_models': [m.get('name', '') for m in models],
                        }
        except Exception:
            pass
        return {'model_name': model_name or 'unknown', 'total_models': 0}
    
    @classmethod
    def _generate_with_llm(cls, prompt: str, model: str, temperature: float = 0.7) -> Optional[str]:
        """Generate a response using the specified LLM model via Ollama."""
        try:
            import httpx
            import os
            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            
            response = httpx.post(
                f"{base_url}/api/generate",
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': 500,
                    }
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
        return None
    
    @classmethod
    def answer(cls, question: str, symbol: str = 'BTC', market_data: Dict = None, 
               model: str = 'gemma4:latest', temperature: float = 0.7) -> Dict:
        """
        Answer a user's trading question.
        
        Args:
            question: User's question (e.g., "Should I buy BTC now?")
            symbol: Trading pair (e.g., 'BTC', 'ETH')
            market_data: Optional pre-fetched market data
            model: Ollama model to use for generation (e.g., 'gemma4:latest')
            temperature: LLM temperature (0.0 = precise, 1.0 = creative)
            
        Returns:
            Response with recommendation, confidence, and analysis
        """
        start = time.time()
        
        # Detect intent
        intent = cls._detect_intent(question)
        
        # Get market analysis
        analysis = cls._get_analysis(symbol, market_data)
        
        # Generate response based on intent and analysis
        response = cls._generate_response(intent, symbol, analysis, question)
        
        # Calculate confidence
        confidence = cls._calculate_confidence(analysis, intent)
        
        # Get Ollama model info (using the selected model)
        model_info = cls._get_ollama_model_info(model)
        actual_model = model_info.get('model_name', model)
        
        # Try to enhance response with LLM if available
        llm_response = cls._generate_with_llm(
            f"You are a crypto trading expert. Based on the analysis below, provide a concise recommendation for {symbol}.\n\n"
            f"Analysis: {response['text']}\n\n"
            f"User Question: {question}\n\n"
            f"Provide your recommendation as {response['recommendation']} with {confidence}% confidence.",
            actual_model,
            temperature
        )
        
        # Use LLM response if available, otherwise use rule-based response
        final_answer = llm_response if llm_response else response['text']
        
        # Format response
        result = {
            'answer': final_answer,
            'recommendation': response['recommendation'],
            'confidence': confidence,
            'symbol': symbol,
            'analysis_summary': {
                'trend': analysis.get('trend', {}).get('bias', 'neutral'),
                'technical_score': analysis.get('technical', {}).get('overall_score', 50),
                'candlestick_score': analysis.get('candlestick', {}).get('overall_score', {}).get('overall', 50),
                'regime_zone': analysis.get('regime', {}).get('zone', 'UNKNOWN'),
            },
            'risk_factors': response.get('risks', []),
            'key_levels': response.get('levels', {}),
            'model_used': actual_model,
            'model_size': model_info.get('model_size', 0),
            'llm_enhanced': llm_response is not None,
            'execution_time_ms': int((time.time() - start) * 1000),
            'timestamp': datetime.now().isoformat(),
        }
        
        return result
    
    @classmethod
    def _detect_intent(cls, question: str) -> str:
        """Detect user's intent from question."""
        question_lower = question.lower()
        
        # Check for specific intent keywords
        buy_score = sum(1 for kw in cls.BUY_KEYWORDS if kw in question_lower)
        sell_score = sum(1 for kw in cls.SELL_KEYWORDS if kw in question_lower)
        hold_score = sum(1 for kw in cls.HOLD_KEYWORDS if kw in question_lower)
        analysis_score = sum(1 for kw in cls.ANALYSIS_KEYWORDS if kw in question_lower)
        
        # Determine primary intent
        if analysis_score > 0 and buy_score == 0 and sell_score == 0:
            return 'analysis'
        elif buy_score > sell_score and buy_score > hold_score:
            return 'buy'
        elif sell_score > buy_score and sell_score > hold_score:
            return 'sell'
        elif hold_score > 0:
            return 'hold'
        else:
            return 'analysis'  # Default to analysis
    
    @classmethod
    def _get_analysis(cls, symbol: str, market_data: Dict = None) -> Dict:
        """Get comprehensive market analysis using all skills."""
        from apps.market.services.unified_data import fetch_market_data
        from apps.trading_skills.services.skills_engine import (
            analyze_technical, 
            calculate_btc_trend,
            calculate_composite_score,
        )
        from apps.trading_skills.services.candlestick_skill import CandlestickSkill
        
        try:
            # Fetch market data
            if market_data is None:
                market = fetch_market_data(symbol)
                closes = market['closes']
                highs = market['highs']
                lows = market['lows']
            else:
                closes = market_data.get('closes', [])
                highs = market_data.get('highs', [])
                lows = market_data.get('lows', [])
            
            if len(closes) < 20:
                return {'error': 'Insufficient data'}
            
            # Technical Analysis
            technical = analyze_technical(closes, highs, lows)
            
            # Candlestick Analysis
            candlestick = CandlestickSkill.analyze(closes, highs, lows)
            
            # Trend Analysis
            trend = calculate_btc_trend(closes)
            
            # Regime Analysis (simplified)
            regime_score = 50
            if trend.get('score', 50) > 70:
                regime_score = 75
            elif trend.get('score', 50) < 30:
                regime_score = 25
            
            return {
                'closes': closes,
                'highs': highs,
                'lows': lows,
                'current_price': closes[-1],
                'technical': technical,
                'candlestick': candlestick,
                'trend': trend,
                'regime': {'zone': 'RISK_ON' if regime_score > 60 else 'RISK_OFF' if regime_score < 40 else 'NEUTRAL'},
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {'error': str(e)}
    
    @classmethod
    def _generate_response(cls, intent: str, symbol: str, analysis: Dict, question: str) -> Dict:
        """Generate response based on intent and analysis."""
        
        if 'error' in analysis:
            return {
                'text': f"I'm sorry, I couldn't analyze {symbol} right now. Please try again later.",
                'recommendation': 'HOLD',
                'risks': ['Unable to fetch market data'],
                'levels': {},
            }
        
        technical = analysis.get('technical', {})
        candlestick = analysis.get('candlestick', {})
        trend = analysis.get('trend', {})
        current_price = analysis.get('current_price', 0)
        
        tech_score = technical.get('overall_score', 50)
        candle_score = candlestick.get('overall_score', {}).get('overall', 50)
        trend_bias = trend.get('bias', 'neutral')
        
        # Determine recommendation based on scores
        combined_score = (tech_score * 0.4 + candle_score * 0.4 + trend.get('score', 50) * 0.2)
        
        if combined_score >= 65:
            recommendation = 'BUY'
            emoji = '🟢'
        elif combined_score <= 35:
            recommendation = 'SELL'
            emoji = '🔴'
        else:
            recommendation = 'HOLD'
            emoji = '🟡'
        
        # Override based on intent if scores are neutral
        if intent == 'buy' and combined_score > 45:
            recommendation = 'BUY'
            emoji = '🟢'
        elif intent == 'sell' and combined_score < 55:
            recommendation = 'SELL'
            emoji = '🔴'
        
        # Generate detailed response
        risks = []
        levels = {}
        
        # Technical details
        rsi = technical.get('momentum', {}).get('rsi', 50)
        if rsi > 70:
            risks.append(f"RSI overbought at {rsi:.1f}")
        elif rsi < 30:
            risks.append(f"RSI oversold at {rsi:.1f} (potential bounce)")
        
        # Trend details
        if trend_bias == 'bullish':
            trend_text = f"Price is above the {trend.get('ma_period', 200)}-period MA (bullish trend)"
        elif trend_bias == 'bearish':
            trend_text = f"Price is below the {trend.get('ma_period', 200)}-period MA (bearish trend)"
        else:
            trend_text = "Price is near the moving average (neutral trend)"
        
        # Candlestick details
        patterns = candlestick.get('patterns', [])
        if patterns:
            latest_pattern = patterns[-1]
            pattern_text = f"Latest candlestick pattern: {latest_pattern['name']} ({latest_pattern['direction']})"
        else:
            pattern_text = "No significant candlestick patterns detected"
        
        # Key levels
        aov = candlestick.get('area_of_value', {})
        if aov.get('nearest_support'):
            levels['support'] = aov['nearest_support']
        if aov.get('nearest_resistance'):
            levels['resistance'] = aov['nearest_resistance']
        
        # Entry/Stop/Target from candlestick
        signals = candlestick.get('signals', [])
        if signals:
            best_signal = max(signals, key=lambda s: s.get('strength', 0))
            levels['entry'] = best_signal.get('entry', current_price)
            levels['stop_loss'] = best_signal.get('stop_loss', current_price * 0.97)
            levels['take_profit'] = best_signal.get('take_profit', current_price * 1.06)
        
        # Build response text
        response_text = f"""**{emoji} {recommendation} Signal for {symbol}/USD**

**Current Price:** ${current_price:,.2f}

**Analysis:**
• **Trend:** {trend_text}
• **Technical Score:** {tech_score:.1f}/100
• **Candlestick Score:** {candle_score:.1f}/100
• **Pattern:** {pattern_text}

**Key Levels:**
"""
        
        if levels.get('support'):
            response_text += f"• Support: ${levels['support']:,.2f}\n"
        if levels.get('resistance'):
            response_text += f"• Resistance: ${levels['resistance']:,.2f}\n"
        if levels.get('entry'):
            response_text += f"• Entry: ${levels['entry']:,.2f}\n"
        if levels.get('stop_loss'):
            response_text += f"• Stop Loss: ${levels['stop_loss']:,.2f}\n"
        if levels.get('take_profit'):
            response_text += f"• Take Profit: ${levels['take_profit']:,.2f}\n"
        
        if risks:
            response_text += "\n**Risk Factors:**\n"
            for risk in risks:
                response_text += f"• ⚠️ {risk}\n"
        
        response_text += f"\n*Analysis based on technical indicators, candlestick patterns, and trend analysis.*"
        
        return {
            'text': response_text,
            'recommendation': recommendation,
            'risks': risks,
            'levels': levels,
        }
    
    @classmethod
    def _calculate_confidence(cls, analysis: Dict, intent: str) -> float:
        """Calculate confidence rate for the recommendation."""
        if 'error' in analysis:
            return 0.0
        
        technical = analysis.get('technical', {})
        candlestick = analysis.get('candlestick', {})
        trend = analysis.get('trend', {})
        
        # Base confidence from technical score
        tech_score = technical.get('overall_score', 50)
        candle_score = candlestick.get('overall_score', {}).get('overall', 50)
        trend_score = trend.get('score', 50)
        
        # Calculate confidence
        # Higher score divergence from 50 = higher confidence
        tech_confidence = abs(tech_score - 50) / 50
        candle_confidence = abs(candle_score - 50) / 50
        trend_confidence = abs(trend_score - 50) / 50
        
        # Weighted average
        confidence = (tech_confidence * 0.35 + candle_confidence * 0.35 + trend_confidence * 0.3) * 100
        
        # Adjust based on pattern confidence
        patterns = candlestick.get('patterns', [])
        if patterns:
            pattern_confidence = max(p.get('confidence', 0.5) for p in patterns[-3:])
            confidence = confidence * 0.7 + pattern_confidence * 30
        
        # Ensure confidence is between 20-95%
        confidence = max(20, min(95, confidence))
        
        return round(confidence, 1)

"""
Trading ChatBot - Answers user questions about buying/selling with confidence rates.

Uses all trading skills to provide informed responses:
- Technical Analysis (trend, momentum, volatility)
- Candlestick Patterns (T.A.E. framework)
- Regime Analysis (market conditions)
- Position Sizing (risk management)

Supports configurable LLM model via settings.
Responds in the same language as the user (English or Persian).
"""
import re
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
    
    # Persian keywords for intent detection
    PERSIAN_BUY_KEYWORDS = ['بخرم', 'بخر', 'خرید', ' long ', 'صعودی', 'وارد', 'accumulat', 'dca']
    PERSIAN_SELL_KEYWORDS = ['بفروشم', 'بفروش', 'فروش', ' short ', 'نزولی', 'خارج', 'بستن', 'liquidat']
    PERSIAN_HOLD_KEYWORDS = ['نگه', 'صبر', 'منتظر', 'هیچ', 'نگه دار']
    PERSIAN_ANALYSIS_KEYWORDS = ['تحلیل', 'نظر', 'signal', 'پیش بینی', 'forecast', 'چی فکر', 'چطور']
    
    # English keywords for intent detection
    ENGLISH_BUY_KEYWORDS = ['buy', 'long', 'purchase', 'enter', 'go up', 'bullish', 'accumulate', 'dca']
    ENGLISH_SELL_KEYWORDS = ['sell', 'short', 'exit', 'close', 'go down', 'bearish', 'dump', 'liquidate']
    ENGLISH_HOLD_KEYWORDS = ['hold', 'wait', 'keep', 'maintain', 'nothing', 'stay']
    ENGLISH_ANALYSIS_KEYWORDS = ['analyze', 'analysis', 'what do you think', 'opinion', 'signal', 'predict', 'forecast']
    
    @classmethod
    def _detect_language(cls, text: str) -> str:
        """Detect if the user is writing in English or Persian."""
        # Check for Persian characters (Arabic script range)
        persian_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
        total_alpha = len(re.findall(r'[a-zA-Z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
        
        if total_alpha == 0:
            return 'en'  # Default to English
        
        persian_ratio = persian_chars / total_alpha
        
        # If more than 30% Persian characters, treat as Persian
        if persian_ratio > 0.3:
            return 'fa'
        return 'en'
    
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
                    if model_name:
                        for m in models:
                            if m.get('name', '') == model_name or m.get('name', '').startswith(model_name.split(':')[0]):
                                return {
                                    'model_name': m.get('name', model_name),
                                    'model_size': m.get('size', 0),
                                    'total_models': len(models),
                                    'all_models': [m.get('name', '') for m in models],
                                }
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
    def _generate_with_llm(cls, prompt: str, model: str, temperature: float = 0.7, 
                           history: list = None, system_prompt: str = None) -> Optional[str]:
        """Generate a response using the specified LLM model via Ollama."""
        try:
            import httpx
            import os
            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            
            # Use chat API if we have conversation history
            if history and len(history) > 0:
                messages = []
                if system_prompt:
                    messages.append({'role': 'system', 'content': system_prompt})
                
                # Add conversation history
                for msg in history[-10:]:  # Last 10 messages for context
                    messages.append({
                        'role': msg.get('role', 'user'),
                        'content': msg.get('content', ''),
                    })
                
                # Add current prompt as user message
                messages.append({'role': 'user', 'content': prompt})
                
                response = httpx.post(
                    f"{base_url}/api/chat",
                    json={
                        'model': model,
                        'messages': messages,
                        'stream': False,
                        'options': {
                            'temperature': temperature,
                            'num_predict': 2000,  # Allow longer responses
                            'top_p': 0.9,
                            'repeat_penalty': 1.1,
                        }
                    },
                    timeout=50.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('message', {}).get('content', '')
            else:
                # Fallback to generate API for single prompts
                response = httpx.post(
                    f"{base_url}/api/generate",
                    json={
                        'model': model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': temperature,
                            'num_predict': 2000,
                            'top_p': 0.9,
                            'repeat_penalty': 1.1,
                        }
                    },
                    timeout=50.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '')
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
        return None
    
    @classmethod
    def answer(cls, question: str, symbol: str = 'BTC', market_data: Dict = None, 
               model: str = 'gemma4:latest', temperature: float = 0.7, 
               history: list = None, tab_context: Dict = None) -> Dict:
        """
        Answer a user's trading question.
        
        Args:
            question: User's question in English or Persian
            symbol: Trading pair (e.g., 'BTC', 'ETH')
            market_data: Optional pre-fetched market data
            model: Ollama model to use for generation
            temperature: LLM temperature (0.0 = precise, 1.0 = creative)
            
        Returns:
            Response with recommendation, confidence, and analysis
        """
        start = time.time()
        
        # Detect language
        language = cls._detect_language(question)
        
        # Detect intent
        intent = cls._detect_intent(question, language)
        
        # Get market analysis
        analysis = cls._get_analysis(symbol, market_data)
        
        # Generate response based on intent and analysis
        response = cls._generate_response(intent, symbol, analysis, question, language)
        
        # Calculate confidence
        confidence = cls._calculate_confidence(analysis, intent)
        
        # Get Ollama model info
        model_info = cls._get_ollama_model_info(model)
        actual_model = model_info.get('model_name', model)
        
        # Create a more conversational prompt for the LLM
        system_prompt = cls._get_system_prompt(language)
        
        # Build tab context string
        tab_info = ''
        if tab_context:
            tab_name = tab_context.get('tab_name', 'Dashboard')
            tab_desc = tab_context.get('tab_description', '')
            capabilities = tab_context.get('capabilities', [])
            tab_info = f"""
User is currently on the {tab_name} tab.
{tab_desc}
Capabilities available: {', '.join(capabilities)}
You can answer questions about this tab and any other tabs. If the user asks about something not on this tab, explain what's available elsewhere."""
        
        llm_prompt = f"""{system_prompt}

The user is asking about {symbol}/USD trading.{tab_info}

Current market data:
- Price: ${analysis.get('current_price', 'N/A'):,.2f}
- Trend: {analysis.get('trend', {}).get('bias', 'neutral')}
- Technical Score: {analysis.get('technical', {}).get('overall_score', 50)}/100
- Candlestick Score: {analysis.get('candlestick', {}).get('overall_score', {}).get('overall', 50)}/100
- RSI: {analysis.get('technical', {}).get('momentum', {}).get('rsi', 50)}
- Fear & Greed: {analysis.get('sentiment', {}).get('fear_greed_index', 50)}

My analysis suggests: {response['recommendation']} with {confidence}% confidence.

User's question: {question}

Respond naturally and conversationally in the same language as the user. Be helpful, explain your reasoning clearly, and provide actionable insights. Do not use markdown formatting - just write naturally like a knowledgeable friend would explain it. You can answer questions about any tab (Trading, Signals, Analysis, Journal, Feedback, Settings) - not just the current one."""

        # Try to enhance response with LLM if available
        llm_response = cls._generate_with_llm(llm_prompt, actual_model, temperature, history=history, system_prompt=system_prompt)
        
        # Use LLM response if available, otherwise use rule-based response
        final_answer = llm_response if llm_response else response['text']
        
        # Format response
        result = {
            'answer': final_answer,
            'recommendation': response['recommendation'],
            'confidence': confidence,
            'symbol': symbol,
            'language': language,
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
    def _get_system_prompt(cls, language: str) -> str:
        """Get the system prompt based on language."""
        if language == 'fa':
            return """تو یک متخصص ترید ارز دیجیتال هستی که به زبان فارسی صحبت می‌کنی.
تو باید:
- مثل یک دوست با تجربه صحبت کنی، نه مثل یک ربات
- از اصطلاحات ترید فارسی استفاده کنی (مثل خرید، فروش، سود، ضرر)
- تحلیلت را ساده و قابل فهم توضیح بدهی
- ریسک‌ها را صادقانه بگویی
- به سوال کاربر مستقیماً جواب بدهی
- از علائم و ایموجی استفاده کنی تا پاسخ جذاب‌تر شود
- پاسخ کوتاه و مفید باشد، نه خیلی طولانی"""
        else:
            return """You are a friendly and knowledgeable crypto trading expert who speaks naturally.
You should:
- Talk like a friend who has experience in trading, not like a robot
- Use casual, conversational language
- Explain your analysis in simple terms
- Be honest about risks
- Answer the user's question directly
- Use emojis to make responses engaging
- Keep responses concise but informative
- If the user asks a casual question, respond casually
- If they ask for detailed analysis, provide more detail"""
    
    @classmethod
    def _detect_intent(cls, question: str, language: str = 'en') -> str:
        """Detect user's intent from question."""
        question_lower = question.lower()
        
        if language == 'fa':
            buy_keywords = cls.PERSIAN_BUY_KEYWORDS
            sell_keywords = cls.PERSIAN_SELL_KEYWORDS
            hold_keywords = cls.PERSIAN_HOLD_KEYWORDS
            analysis_keywords = cls.PERSIAN_ANALYSIS_KEYWORDS
        else:
            buy_keywords = cls.ENGLISH_BUY_KEYWORDS
            sell_keywords = cls.ENGLISH_SELL_KEYWORDS
            hold_keywords = cls.ENGLISH_HOLD_KEYWORDS
            analysis_keywords = cls.ENGLISH_ANALYSIS_KEYWORDS
        
        # Check for specific intent keywords
        buy_score = sum(1 for kw in buy_keywords if kw in question_lower)
        sell_score = sum(1 for kw in sell_keywords if kw in sell_keywords)
        hold_score = sum(1 for kw in hold_keywords if kw in question_lower)
        analysis_score = sum(1 for kw in analysis_keywords if kw in question_lower)
        
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
    def _generate_response(cls, intent: str, symbol: str, analysis: Dict, question: str, language: str = 'en') -> Dict:
        """Generate response based on intent and analysis."""
        
        if 'error' in analysis:
            if language == 'fa':
                return {
                    'text': f"متأسفانه الان نمی‌تونم {symbol} رو تحلیل کنم. لطفاً بعداً دوباره امتحان کن.",
                    'recommendation': 'HOLD',
                    'risks': [' unable to fetch market data'],
                    'levels': {},
                }
            else:
                return {
                    'text': f"Sorry, I can't analyze {symbol} right now. Please try again later.",
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
            if language == 'fa':
                risks.append(f"RSI در منطقه اشباع خرید ({rsi:.1f})")
            else:
                risks.append(f"RSI overbought at {rsi:.1f}")
        elif rsi < 30:
            if language == 'fa':
                risks.append(f"RSI در منطقه اشباع فروش ({rsi:.1f}) - امکان برگشت وجود دارد")
            else:
                risks.append(f"RSI oversold at {rsi:.1f} (potential bounce)")
        
        # Trend details
        if trend_bias == 'bullish':
            if language == 'fa':
                trend_text = f"قیمت بالای میانگین متحرک {trend.get('ma_period', 200)} دوره‌ای است (روند صعودی)"
            else:
                trend_text = f"Price is above the {trend.get('ma_period', 200)}-period MA (bullish trend)"
        elif trend_bias == 'bearish':
            if language == 'fa':
                trend_text = f"قیمت زیر میانگین متحرک {trend.get('ma_period', 200)} دوره‌ای است (روند نزولی)"
            else:
                trend_text = f"Price is below the {trend.get('ma_period', 200)}-period MA (bearish trend)"
        else:
            if language == 'fa':
                trend_text = "قیمت نزدیک میانگین متحرک است (روند خنثی)"
            else:
                trend_text = "Price is near the moving average (neutral trend)"
        
        # Candlestick details
        patterns = candlestick.get('patterns', [])
        if patterns:
            latest_pattern = patterns[-1]
            if language == 'fa':
                pattern_text = f"آخرین الگوی کندل: {latest_pattern['name']} ({latest_pattern['direction']})"
            else:
                pattern_text = f"Latest candlestick pattern: {latest_pattern['name']} ({latest_pattern['direction']})"
        else:
            if language == 'fa':
                pattern_text = "الگوی خاصی شناسایی نشد"
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
        if language == 'fa':
            response_text = f"""{emoji} سیگنال {recommendation} برای {symbol}/USD

قیمت فعلی: ${current_price:,.2f}

تحلیل:
• روند: {trend_text}
• امتیاز تکنیکال: {tech_score:.1f}/100
• امتیاز کندل: {candle_score:.1f}/100
• الگو: {pattern_text}

سطوح کلیدی:
"""
        else:
            response_text = f"""{emoji} {recommendation} Signal for {symbol}/USD

Current Price: ${current_price:,.2f}

Analysis:
• Trend: {trend_text}
• Technical Score: {tech_score:.1f}/100
• Candlestick Score: {candle_score:.1f}/100
• Pattern: {pattern_text}

Key Levels:
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
            if language == 'fa':
                response_text += "\n⚠️ ریسک‌ها:\n"
            else:
                response_text += "\n⚠️ Risk Factors:\n"
            for risk in risks:
                response_text += f"• {risk}\n"
        
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

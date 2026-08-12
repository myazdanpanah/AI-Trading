"""Signal Generator - Multi-factor scoring engine for crypto trading signals."""
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Multi-factor scoring engine that generates trading signals by combining
    technical analysis, sentiment, news, AI predictions, and macro factors.
    """
    
    DEFAULT_WEIGHTS = {
        'technical': Decimal('0.35'),  # Increased: most reliable for crypto
        'sentiment': Decimal('0.15'),  # Decreased: noisy, lagging
        'news': Decimal('0.10'),       # Decreased: often priced in quickly
        'ai': Decimal('0.25'),         # Increased: pattern recognition strength
        'macro': Decimal('0.15'),      # Stable: BTC trend + DXY correlation
    }
    
    DIRECTION_THRESHOLDS = {
        'strong_buy': (75, 101),  # 101 to include 100
        'buy': (60, 75),
        'hold': (40, 60),
        'sell': (25, 40),
        'strong_sell': (0, 25),
    }
    
    def __init__(self):
        self.weights = self.DEFAULT_WEIGHTS.copy()
    
    def load_weights(self, factor_weights: List) -> None:
        """Load configurable weights from database."""
        for fw in factor_weights:
            if fw.is_active and fw.name in self.weights:
                self.weights[fw.name] = Decimal(str(fw.weight))
        
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        technical_data: Dict = None,
        sentiment_data: Dict = None,
        news_data: Dict = None,
        ai_data: Dict = None,
        macro_data: Dict = None,
        current_price: Decimal = None,
    ) -> Dict:
        """
        Generate a trading signal based on multi-factor analysis.
        
        Returns:
            Dict with signal details, scores, and reasoning
        """
        # Calculate individual factor scores
        scores = {
            'technical': self._score_technical(technical_data or {}),
            'sentiment': self._score_sentiment(sentiment_data or {}),
            'news': self._score_news(news_data or {}),
            'ai': self._score_ai(ai_data or {}),
            'macro': self._score_macro(macro_data or {}),
        }
        
        # Calculate composite score
        composite_score = sum(
            scores[factor] * weight
            for factor, weight in self.weights.items()
        )
        
        # Determine direction
        direction, confidence = self._determine_direction(composite_score)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            technical_data or {},
            sentiment_data or {},
            scores
        )
        
        # Generate reasoning
        reasons = self._generate_reasons(scores, technical_data or {}, sentiment_data or {})
        
        # Calculate entry/exit levels
        entry_levels = self._calculate_entry_levels(
            direction=direction,
            current_price=current_price or Decimal('0'),
            technical_data=technical_data or {},
        )
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'direction': direction,
            'confidence': confidence,
            'composite_score': float(composite_score),
            'risk_score': risk_score,
            'factor_scores': {k: float(v) for k, v in scores.items()},
            'weights_used': {k: float(v) for k, v in self.weights.items()},
            'reasons': reasons,
            'entry_price': entry_levels.get('entry_price'),
            'stop_loss': entry_levels.get('stop_loss'),
            'take_profit': entry_levels.get('take_profit'),
            'generated_at': datetime.now().isoformat(),
        }
        
        logger.info(f"Generated signal for {symbol}: {direction} (confidence={confidence}%)")
        return result
    
    def _score_technical(self, data: Dict) -> Decimal:
        """Score based on technical analysis data with VWAP + Ichimoku."""
        if not data:
            return Decimal('50')
        
        score = Decimal('50')
        
        # RSI scoring (stronger signals)
        rsi = data.get('rsi')
        if rsi is not None:
            if rsi < 25:
                score += Decimal('18')  # Extremely oversold
            elif rsi < 30:
                score += Decimal('12')  # Oversold
            elif rsi > 75:
                score -= Decimal('18')  # Extremely overbought
            elif rsi > 70:
                score -= Decimal('12')  # Overbought
            elif 45 <= rsi <= 55:
                score += Decimal('3')   # Neutral zone
        
        # MACD scoring
        macd_signal = data.get('macd_signal')
        if macd_signal:
            if macd_signal == 'bullish_crossover':
                score += Decimal('12')
            elif macd_signal == 'bearish_crossover':
                score -= Decimal('12')
            elif macd_signal == 'bullish':
                score += Decimal('6')
            elif macd_signal == 'bearish':
                score -= Decimal('6')
        
        # Trend scoring (stronger signals)
        trend = data.get('trend')
        if trend:
            if trend == 'strong_uptrend':
                score += Decimal('18')
            elif trend == 'uptrend':
                score += Decimal('12')
            elif trend == 'downtrend':
                score -= Decimal('12')
            elif trend == 'strong_downtrend':
                score -= Decimal('18')
        
        # Support/Resistance scoring
        sr_signal = data.get('sr_signal')
        if sr_signal:
            if sr_signal == 'near_support':
                score += Decimal('10')
            elif sr_signal == 'near_resistance':
                score -= Decimal('10')
        
        # Volume scoring
        volume_signal = data.get('volume_signal')
        if volume_signal:
            if volume_signal == 'high_volume_breakout':
                score += Decimal('8')
            elif volume_signal == 'low_volume':
                score -= Decimal('5')
        
        # VWAP scoring (NEW)
        vwap_signal = data.get('vwap_signal')
        if vwap_signal:
            vwap_deviation = data.get('vwap_deviation', 0)
            if vwap_signal == 'bullish' and vwap_deviation < -2:
                score += Decimal('10')  # Oversold vs VWAP
            elif vwap_signal == 'bullish':
                score += Decimal('5')
            elif vwap_signal == 'bearish' and vwap_deviation > 2:
                score -= Decimal('10')  # Overbought vs VWAP
            elif vwap_signal == 'bearish':
                score -= Decimal('5')
        
        # Ichimoku scoring (NEW)
        ichimoku_signal = data.get('ichimoku_signal')
        if ichimoku_signal:
            if ichimoku_signal == 'strong_bullish':
                score += Decimal('15')  # Above cloud + TK cross + bullish cloud
            elif ichimoku_signal == 'bullish':
                score += Decimal('8')
            elif ichimoku_signal == 'strong_bearish':
                score -= Decimal('15')
            elif ichimoku_signal == 'bearish':
                score -= Decimal('8')
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    def _score_sentiment(self, data: Dict) -> Decimal:
        """Score based on sentiment analysis data."""
        if not data:
            return Decimal('50')
        
        score = Decimal('50')
        
        # Fear & Greed Index
        fear_greed = data.get('fear_greed_index')
        if fear_greed is not None:
            if fear_greed < 25:
                score += Decimal('20')  # Extreme fear = contrarian bullish
            elif fear_greed < 40:
                score += Decimal('10')
            elif fear_greed > 75:
                score -= Decimal('20')  # Extreme greed = contrarian bearish
            elif fear_greed > 60:
                score -= Decimal('10')
        
        # Social sentiment
        social_sentiment = data.get('social_sentiment')
        if social_sentiment is not None:
            score += Decimal(str(max(-20, min(20, social_sentiment - 50))))
        
        # Whale activity
        whale_signal = data.get('whale_signal')
        if whale_signal:
            if whale_signal == 'accumulation':
                score += Decimal('10')
            elif whale_signal == 'distribution':
                score -= Decimal('10')
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    def _score_news(self, data: Dict) -> Decimal:
        """Score based on news analysis."""
        if not data:
            return Decimal('50')
        
        score = Decimal('50')
        
        # News sentiment
        news_sentiment = data.get('sentiment')
        if news_sentiment:
            if news_sentiment == 'positive':
                score += Decimal('15')
            elif news_sentiment == 'negative':
                score -= Decimal('15')
        
        # Impact score
        impact = data.get('impact_score')
        if impact is not None:
            score += Decimal(str(max(-15, min(15, impact - 50))))
        
        # Breaking news bonus
        if data.get('is_breaking'):
            score += Decimal('10') if data.get('sentiment') == 'positive' else Decimal('-10')
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    def _score_ai(self, data: Dict) -> Decimal:
        """Score based on AI model predictions."""
        if not data:
            return Decimal('50')
        
        score = Decimal('50')
        
        # AI prediction
        prediction = data.get('prediction')
        if prediction:
            confidence = Decimal(str(data.get('prediction_confidence') or 50))
            if prediction == 'bullish':
                score += (confidence / Decimal('100')) * Decimal('30')
            elif prediction == 'bearish':
                score -= (confidence / Decimal('100')) * Decimal('30')
        
        # Model consensus
        consensus = data.get('model_consensus')
        if consensus is not None:
            score += Decimal(str(max(-20, min(20, consensus - 50))))
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    def _score_macro(self, data: Dict) -> Decimal:
        """Score based on macro/economic factors."""
        if not data:
            return Decimal('50')
        
        score = Decimal('50')
        
        # BTC correlation
        btc_trend = data.get('btc_trend')
        if btc_trend:
            if btc_trend == 'bullish':
                score += Decimal('10')
            elif btc_trend == 'bearish':
                score -= Decimal('10')
        
        # Market regime
        market_regime = data.get('market_regime')
        if market_regime:
            if market_regime == 'risk_on':
                score += Decimal('10')
            elif market_regime == 'risk_off':
                score -= Decimal('10')
        
        # DXY (Dollar Index)
        dxy_trend = data.get('dxy_trend')
        if dxy_trend:
            if dxy_trend == 'weakening':
                score += Decimal('5')  # Weaker dollar = bullish crypto
            elif dxy_trend == 'strengthening':
                score -= Decimal('5')
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    def _determine_direction(self, composite_score: Decimal) -> Tuple[str, int]:
        """Determine signal direction and confidence from composite score."""
        score = float(composite_score)
        
        for direction, (low, high) in self.DIRECTION_THRESHOLDS.items():
            if low <= score < high:
                # Confidence is distance from midpoint
                midpoint = (low + high) / 2
                confidence = int(50 + abs(score - midpoint) * 2)
                return direction, min(95, max(10, confidence))
        
        return 'hold', 50
    
    def _calculate_risk_score(
        self,
        technical_data: Dict,
        sentiment_data: Dict,
        scores: Dict
    ) -> int:
        """Calculate risk score (0-100, higher = more risky)."""
        risk = 50
        
        # Volatility risk
        volatility = technical_data.get('volatility')
        if volatility:
            if volatility > 5:
                risk += 20
            elif volatility > 3:
                risk += 10
            elif volatility < 1:
                risk -= 10
        
        # Sentiment extremes increase risk
        fear_greed = sentiment_data.get('fear_greed_index')
        if fear_greed:
            if fear_greed < 20 or fear_greed > 80:
                risk += 15
        
        # Score disagreement increases risk
        score_values = list(scores.values())
        if score_values:
            score_range = max(score_values) - min(score_values)
            if score_range > 30:
                risk += 10
        
        return max(0, min(100, risk))
    
    def _generate_reasons(
        self,
        scores: Dict,
        technical_data: Dict,
        sentiment_data: Dict
    ) -> List[Dict]:
        """Generate human-readable reasons for the signal."""
        reasons = []
        
        # Technical reasons - always provide
        tech_score = float(scores.get('technical', 50))
        if tech_score > 65:
            reasons.append({
                'type': 'technical',
                'description': f"Strong technical indicators (score: {tech_score:.1f})",
                'confidence': int(tech_score),
            })
        elif tech_score < 35:
            reasons.append({
                'type': 'technical',
                'description': f"Weak technical indicators (score: {tech_score:.1f})",
                'confidence': int(100 - tech_score),
            })
        else:
            reasons.append({
                'type': 'technical',
                'description': f"Mixed technical signals (score: {tech_score:.1f}) - no clear direction",
                'confidence': 50,
            })
        
        # RSI reason
        rsi = technical_data.get('rsi')
        if rsi is not None:
            if rsi > 70:
                reasons.append({'type': 'technical', 'description': f"RSI overbought ({rsi:.0f}) - potential reversal", 'confidence': 70})
            elif rsi < 30:
                reasons.append({'type': 'technical', 'description': f"RSI oversold ({rsi:.0f}) - potential bounce", 'confidence': 70})
            elif 45 <= rsi <= 55:
                reasons.append({'type': 'technical', 'description': f"RSI neutral ({rsi:.0f}) - no momentum signal", 'confidence': 40})
        
        # Trend reason
        trend = technical_data.get('trend')
        if trend and trend != 'neutral':
            reasons.append({'type': 'technical', 'description': f"Trend: {trend.replace('_', ' ')}", 'confidence': 60})
        
        # VWAP reason
        vwap = technical_data.get('vwap_signal')
        if vwap and vwap != 'neutral':
            reasons.append({'type': 'technical', 'description': f"VWAP signal: {vwap} - price {'below' if vwap == 'bearish' else 'above'} VWAP", 'confidence': 55})
        
        # Sentiment reasons
        fear_greed = sentiment_data.get('fear_greed_index')
        if fear_greed is not None:
            if fear_greed < 25:
                reasons.append({
                    'type': 'sentiment',
                    'description': f"Extreme fear (F&G: {fear_greed}) - contrarian buy signal",
                    'confidence': 75,
                })
            elif fear_greed > 75:
                reasons.append({
                    'type': 'sentiment',
                    'description': f"Extreme greed (F&G: {fear_greed}) - caution advised",
                    'confidence': 75,
                })
            elif fear_greed < 40:
                reasons.append({'type': 'sentiment', 'description': f"Fear dominant (F&G: {fear_greed}) - market cautious", 'confidence': 55})
            elif fear_greed > 60:
                reasons.append({'type': 'sentiment', 'description': f"Greed dominant (F&G: {fear_greed}) - market optimistic", 'confidence': 55})
            else:
                reasons.append({'type': 'sentiment', 'description': f"Neutral sentiment (F&G: {fear_greed})", 'confidence': 40})
        
        # AI reasons
        ai_score = float(scores.get('ai', 50))
        if ai_score > 65:
            reasons.append({
                'type': 'ai',
                'description': f"AI models bullish (score: {ai_score:.1f})",
                'confidence': int(ai_score),
            })
        elif ai_score < 35:
            reasons.append({
                'type': 'ai',
                'description': f"AI models bearish (score: {ai_score:.1f})",
                'confidence': int(100 - ai_score),
            })
        
        # Macro reason
        macro_score = float(scores.get('macro', 50))
        if macro_score > 60:
            reasons.append({'type': 'macro', 'description': f"Favorable macro conditions (score: {macro_score:.1f})", 'confidence': int(macro_score)})
        elif macro_score < 40:
            reasons.append({'type': 'macro', 'description': f"Unfavorable macro conditions (score: {macro_score:.1f})", 'confidence': int(100 - macro_score)})
        
        return reasons
    
    def _calculate_entry_levels(
        self,
        direction: str,
        current_price: Decimal,
        technical_data: Dict
    ) -> Dict:
        """Calculate entry, stop loss, and take profit levels for ALL signals."""
        price = float(current_price) if current_price else 0
        if price <= 0:
            return {'entry_price': 0, 'stop_loss': 0, 'take_profit': []}
        
        atr_raw = technical_data.get('atr', price * 0.02)
        atr = float(atr_raw) if atr_raw else price * 0.02
        if atr <= 0:
            atr = price * 0.02
        
        entry_price = price
        
        if direction in ('buy', 'strong_buy'):
            stop_loss = price - (atr * 2)
            take_profit = [price + atr * 2, price + atr * 3, price + atr * 5]
        elif direction in ('sell', 'strong_sell'):
            stop_loss = price + (atr * 2)
            take_profit = [price - atr * 2, price - atr * 3, price - atr * 5]
        else:
            stop_loss = price - (atr * 2)
            take_profit = [price + atr * 2, price + atr * 3, price - atr * 2]
        
        return {
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': [round(tp, 2) for tp in take_profit],
        }

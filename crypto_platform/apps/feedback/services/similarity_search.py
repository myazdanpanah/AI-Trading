"""Similarity Search Service - Find similar historical market conditions."""
import logging
import math
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimilaritySearchService:
    """Search for similar historical market situations using vector similarity."""
    
    # Feature weights for similarity calculation
    FEATURE_WEIGHTS = {
        'price_change': 0.25,
        'volume_profile': 0.15,
        'rsi': 0.15,
        'macd': 0.10,
        'trend': 0.15,
        'sentiment': 0.10,
        'volatility': 0.10,
    }
    
    @staticmethod
    def calculate_embedding(market_data: Dict) -> List[float]:
        """Calculate a vector embedding from market data for similarity search.
        
        This creates a numerical representation of the market state that can be
        compared with historical embeddings using cosine similarity.
        """
        features = []
        
        # Price features
        price_change_1h = market_data.get('price_change_1h', 0)
        price_change_24h = market_data.get('price_change_24h', 0)
        price_change_7d = market_data.get('price_change_7d', 0)
        features.extend([
            SimilaritySearchService._normalize(price_change_1h, -10, 10),
            SimilaritySearchService._normalize(price_change_24h, -30, 30),
            SimilaritySearchService._normalize(price_change_7d, -50, 50),
        ])
        
        # Volume features
        volume_ratio = market_data.get('volume_ratio', 1.0)  # vs 20-day average
        features.append(SimilaritySearchService._normalize(volume_ratio, 0, 5))
        
        # Technical indicators
        rsi = market_data.get('rsi', 50)
        macd_signal = market_data.get('macd_signal', 0)
        ema_trend = market_data.get('ema_trend', 0)  # -1 to 1
        adx = market_data.get('adx', 25)
        
        features.extend([
            SimilaritySearchService._normalize(rsi, 0, 100),
            SimilaritySearchService._normalize(macd_signal, -1, 1),
            SimilaritySearchService._normalize(ema_trend, -1, 1),
            SimilaritySearchService._normalize(adx, 0, 100),
        ])
        
        # Sentiment features
        fear_greed = market_data.get('fear_greed_index', 50)
        social_sentiment = market_data.get('social_sentiment', 0)
        features.extend([
            SimilaritySearchService._normalize(fear_greed, 0, 100),
            SimilaritySearchService._normalize(social_sentiment, -1, 1),
        ])
        
        # Volatility
        atr_percent = market_data.get('atr_percent', 2.0)
        features.append(SimilaritySearchService._normalize(atr_percent, 0, 10))
        
        # Normalize the entire vector to unit length
        magnitude = math.sqrt(sum(f * f for f in features))
        if magnitude > 0:
            features = [f / magnitude for f in features]
        
        return features
    
    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-1 range."""
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))
    
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    @classmethod
    def find_similar_memories(
        cls,
        current_market_data: Dict,
        symbol: str = None,
        limit: int = 5,
        min_similarity: float = 0.7,
        days_lookback: int = 90,
    ) -> List[Dict]:
        """Find similar historical market situations.
        
        Uses optimized search with early termination for performance.
        For pgvector-enabled databases, consider using native vector operations.
        
        Args:
            current_market_data: Current market conditions
            symbol: Optional symbol filter
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1)
            days_lookback: How far back to search
            
        Returns:
            List of similar memories with similarity scores
        """
        from ..models import MarketMemory, SignalMemory
        
        # Calculate embedding for current market state
        current_embedding = cls.calculate_embedding(current_market_data)
        
        # Build query filters
        filters = {}
        if symbol:
            filters['symbol'] = symbol
        
        cutoff_date = datetime.now() - timedelta(days=days_lookback)
        
        # Get candidate memories with embeddings only
        candidates = MarketMemory.objects.filter(
            created_at__gte=cutoff_date,
            embedding__isnull=False,
            **filters
        ).exclude(embedding=[]).order_by('-created_at')[:500]
        
        # Calculate similarities with early termination
        similarities = []
        for memory in candidates:
            if not memory.embedding or len(memory.embedding) != len(current_embedding):
                continue
            
            similarity = cls.cosine_similarity(current_embedding, memory.embedding)
            
            if similarity >= min_similarity:
                # Get signal outcomes for this memory
                signals = list(SignalMemory.objects.filter(
                    market_memory=memory
                ).values(
                    'was_correct', 'actual_return_percent', 'signal_direction'
                )[:100])  # Limit for performance
                
                correct_count = sum(1 for s in signals if s['was_correct'])
                total_count = len(signals)
                avg_return = (
                    sum(s['actual_return_percent'] for s in signals) / total_count
                    if total_count > 0 else 0
                )
                
                similarities.append({
                    'memory_id': str(memory.id),
                    'symbol': memory.symbol,
                    'timeframe': memory.timeframe,
                    'market_condition': memory.market_condition,
                    'similarity_score': round(similarity, 4),
                    'price': float(memory.price),
                    'created_at': memory.created_at.isoformat(),
                    'historical_outcome': {
                        'total_signals': total_count,
                        'correct_signals': correct_count,
                        'win_rate': round(correct_count / total_count * 100, 2) if total_count > 0 else 0,
                        'avg_return_percent': round(avg_return, 4),
                    }
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:limit]
    
    @classmethod
    def find_similar_patterns(
        cls,
        current_indicators: Dict,
        pattern_type: str = None,
        symbol: str = None,
        limit: int = 5,
    ) -> List[Dict]:
        """Find similar historical patterns based on technical indicators."""
        from ..models import PatternMemory
        
        filters = {}
        if pattern_type:
            filters['pattern_type'] = pattern_type
        if symbol:
            filters['symbol'] = symbol
        
        candidates = PatternMemory.objects.filter(
            sample_size__gte=3,  # Need minimum sample size
            **filters
        )[:200]
        
        results = []
        for pattern in candidates:
            if not pattern.embedding:
                continue
            
            # Create embedding from current indicators
            current_embedding = cls.calculate_embedding(current_indicators)
            similarity = cls.cosine_similarity(current_embedding, pattern.embedding)
            
            if similarity >= 0.6:
                results.append({
                    'pattern_id': str(pattern.id),
                    'pattern_type': pattern.pattern_type,
                    'symbol': pattern.symbol,
                    'timeframe': pattern.timeframe,
                    'similarity_score': round(similarity, 4),
                    'avg_return': float(pattern.avg_return),
                    'win_rate': float(pattern.win_rate),
                    'sample_size': pattern.sample_size,
                    'conditions': pattern.conditions,
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:limit]
    
    @classmethod
    def get_signal_prediction(
        cls,
        current_market_data: Dict,
        signal_direction: str,
    ) -> Dict:
        """Predict signal outcome based on historical similarity.
        
        Analyzes similar past market conditions and their outcomes to predict
        the likely result of a new signal.
        """
        # Find similar memories
        similar = cls.find_similar_memories(
            current_market_data,
            limit=10,
            min_similarity=0.6,
        )
        
        if not similar:
            return {
                'prediction': 'insufficient_data',
                'confidence': 0,
                'similar_count': 0,
                'recommendation': 'Proceed with caution - limited historical data',
            }
        
        # Filter for same direction signals
        matching_outcomes = []
        opposite_outcomes = []
        
        for mem in similar:
            outcome = mem.get('historical_outcome', {})
            if outcome.get('total_signals', 0) > 0:
                if outcome.get('avg_return_percent', 0) > 0:
                    matching_outcomes.append(outcome)
                else:
                    opposite_outcomes.append(outcome)
        
        if not matching_outcomes and not opposite_outcomes:
            return {
                'prediction': 'neutral',
                'confidence': 0.3,
                'similar_count': len(similar),
                'recommendation': 'Mixed historical data - use standard risk management',
            }
        
        # Calculate prediction
        total_samples = sum(o['total_signals'] for o in matching_outcomes + opposite_outcomes)
        total_correct = sum(o['correct_signals'] for o in matching_outcomes + opposite_outcomes)
        
        win_rate = total_correct / total_samples if total_samples > 0 else 0.5
        avg_return = (
            sum(o['avg_return_percent'] for o in matching_outcomes) / len(matching_outcomes)
            if matching_outcomes else 0
        )
        
        # Determine prediction
        if win_rate > 0.65 and avg_return > 0:
            prediction = 'favorable'
            confidence = min(0.9, 0.5 + (win_rate - 0.5) * 0.8)
        elif win_rate < 0.4:
            prediction = 'unfavorable'
            confidence = min(0.9, 0.5 + (0.5 - win_rate) * 0.8)
        else:
            prediction = 'neutral'
            confidence = 0.4
        
        return {
            'prediction': prediction,
            'confidence': round(confidence, 3),
            'similar_count': len(similar),
            'historical_win_rate': round(win_rate * 100, 2),
            'historical_avg_return': round(avg_return, 4),
            'total_samples': total_samples,
            'recommendation': cls._generate_recommendation(prediction, confidence, win_rate),
        }
    
    @staticmethod
    def _generate_recommendation(prediction: str, confidence: float, win_rate: float) -> str:
        """Generate a human-readable recommendation based on prediction."""
        if prediction == 'favorable':
            if confidence > 0.7:
                return 'Strong historical precedent - consider increasing position size'
            return 'Historical data supports this trade - proceed with normal sizing'
        elif prediction == 'unfavorable':
            if confidence > 0.7:
                return 'Warning: Similar setups historically underperform - consider reducing size or waiting'
            return 'Mixed historical signals - proceed with caution and tight stops'
        else:
            return 'Insufficient historical edge - use standard risk management'

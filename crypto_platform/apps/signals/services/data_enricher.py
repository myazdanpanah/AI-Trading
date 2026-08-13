"""Data enricher for signal generation — gathers news, social, macro, and AI data."""
import logging
from typing import Dict, Optional
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class SignalDataEnricher:
    """Gathers all non-technical data for signal generation."""

    @staticmethod
    def get_news_data(symbol: str) -> Dict:
        """Get recent news sentiment for a symbol from DB articles."""
        try:
            from apps.news.models import NewsArticle
            from django.utils import timezone

            cutoff = timezone.now() - timedelta(hours=24)
            articles = NewsArticle.objects.filter(
                published_at__gte=cutoff,
            ).order_by('-impact_score')[:20]

            if not articles.exists():
                return {'sentiment': 'neutral', 'impact_score': 50, 'article_count': 0}

            # Analyze sentiment distribution
            sentiments = list(articles.values_list('sentiment', flat=True))
            bullish = sentiments.count('bullish')
            bearish = sentiments.count('bearish')
            total = len(sentiments)

            if total == 0:
                return {'sentiment': 'neutral', 'impact_score': 50, 'article_count': 0}

            # Determine overall sentiment from keyword analysis
            keywords = _analyze_news_keywords(articles)
            kw_bullish = keywords.get('bullish', 0)
            kw_bearish = keywords.get('bearish', 0)
            
            # Combine keyword + sentiment counts
            bullish_total = bullish + kw_bullish
            bearish_total = bearish + kw_bearish
            
            if bullish_total > bearish_total + 2:
                sentiment = 'positive'
                impact = 60 + min(20, (bullish_total - bearish_total) * 3)
            elif bearish_total > bullish_total + 2:
                sentiment = 'negative'
                impact = 40 - min(20, (bearish_total - bullish_total) * 3)
            else:
                sentiment = 'neutral'
                impact = 50

            # Average impact score from articles
            avg_impact = sum(a.impact_score for a in articles) / total
            impact = int((impact + avg_impact) / 2)

            # Check for breaking/high-impact news
            is_breaking = any(a.impact_score >= 80 for a in articles)

            # Keyword analysis for crypto-specific signals
            keywords = _analyze_news_keywords(articles)

            return {
                'sentiment': sentiment,
                'impact_score': max(0, min(100, impact)),
                'article_count': total,
                'is_breaking': is_breaking,
                'bullish_count': bullish,
                'bearish_count': bearish,
                'keywords': keywords,
            }

        except Exception as e:
            logger.error(f"Failed to get news data: {e}")
            return {'sentiment': 'neutral', 'impact_score': 50, 'article_count': 0}

    @staticmethod
    def get_social_data(symbol: str) -> Dict:
        """Get social sentiment from Fear/Greed + X/Twitter scraping + news."""
        try:
            from apps.journal.services.journal_writer import fetch_fear_greed_index
            from apps.news.models import NewsArticle
            from django.utils import timezone
            import asyncio

            # Fear & Greed
            try:
                fg = fetch_fear_greed_index()
                fear_greed = fg.get('value', 50)
            except Exception:
                fear_greed = 50

            # X/Twitter sentiment from top accounts
            twitter_sentiment = 50
            tweet_count = 0
            try:
                from apps.social.services.twitter_scraper import TwitterScraper
                scraper = TwitterScraper()
                # Fetch from key accounts only (fast: ~3-5 accounts)
                key_accounts = {
                    'CryptoCapo_': 'analyst',
                    'WhaleAlert': 'whale',
                    'WatcherGuru': 'news',
                    'coindesk': 'news',
                    'sentdefender': 'geopolitics',
                }
                tweets = asyncio.run(scraper.fetch_all_accounts(key_accounts, limit_per_user=3))
                if tweets:
                    sentiment_result = scraper.analyze_sentiment(tweets)
                    twitter_sentiment = sentiment_result['score']
                    tweet_count = sentiment_result['tweet_count']
            except Exception as e:
                logger.warning(f"Twitter scrape failed: {e}")

            # Crypto-specific news articles
            cutoff = timezone.now() - timedelta(hours=24)
            crypto_articles = NewsArticle.objects.filter(
                published_at__gte=cutoff,
                title__icontains=symbol.replace('USDT', '').replace('USD', ''),
            ).order_by('-impact_score')[:10]

            # Whale activity detection
            whale_signal = None
            for a in crypto_articles:
                title_lower = a.title.lower()
                if any(w in title_lower for w in ['whale', 'accumulation', 'buy pressure']):
                    whale_signal = 'accumulation'
                    break
                elif any(w in title_lower for w in ['sell-off', 'dump', 'distribution']):
                    whale_signal = 'distribution'
                    break

            # Combine Fear/Greed + Twitter sentiment
            combined_score = int((fear_greed + twitter_sentiment) / 2)

            return {
                'fear_greed_index': fear_greed,
                'social_sentiment': combined_score,
                'twitter_sentiment': twitter_sentiment,
                'tweet_count': tweet_count,
                'whale_signal': whale_signal,
                'crypto_mention_count': crypto_articles.count(),
            }

        except Exception as e:
            logger.error(f"Failed to get social data: {e}")
            return {'fear_greed_index': 50, 'social_sentiment': 50}

    @staticmethod
    def get_macro_data(symbol: str, current_price: float = 0) -> Dict:
        """Get macro/economic data."""
        try:
            # BTC dominance as proxy for market regime
            from apps.market.services.unified_data import fetch_market_data

            macro = {
                'btc_trend': 'neutral',
                'dxy_trend': 'neutral',
                'oil_trend': 'neutral',
                'gold_trend': 'neutral',
                'market_regime': 'neutral',
            }

            # Get BTC dominance
            try:
                import urllib.request
                import json

                # CoinGecko BTC dominance
                url = 'https://api.coingecko.com/api/v3/global'
                req = urllib.request.Request(url, headers={'User-Agent': 'AI-Trading-Bot/1.0'})
                response = urllib.request.urlopen(req, timeout=10)
                data = json.loads(response.read())

                btc_dominance = data.get('data', {}).get('market_cap_percentage', {}).get('btc', 50)
                total_market_cap_change = data.get('data', {}).get('market_cap_change_percentage_24h_usd', 0)

                # BTC trend from dominance
                if btc_dominance > 55:
                    macro['btc_trend'] = 'bullish'  # BTC leading = risk-on for BTC
                elif btc_dominance < 45:
                    macro['btc_trend'] = 'bearish'  # Alts outperforming

                # Market regime from total cap change
                if total_market_cap_change > 2:
                    macro['market_regime'] = 'bullish'
                elif total_market_cap_change < -2:
                    macro['market_regime'] = 'bearish'

                macro['btc_dominance'] = btc_dominance
                macro['total_market_cap_change'] = total_market_cap_change

            except Exception as e:
                logger.warning(f"Failed to get BTC dominance: {e}")

            # BTC correlation - use BTC's own trend for BTCUSDT
            if symbol in ('BTC', 'BTCUSDT'):
                macro['btc_trend'] = macro['market_regime']

            return macro

        except Exception as e:
            logger.error(f"Failed to get macro data: {e}")
            return {'btc_trend': 'neutral', 'market_regime': 'neutral'}

    @staticmethod
    def get_ai_prediction(symbol: str, technical_data: Dict = None, news_data: Dict = None) -> Dict:
        """Get AI prediction using Ollama LLM."""
        try:
            import httpx
            import os

            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

            # Build context for LLM
            rsi = (technical_data or {}).get('rsi', 50)
            trend = (technical_data or {}).get('trend', 'neutral')
            macd = (technical_data or {}).get('macd_signal', 'neutral')
            news_sentiment = (news_data or {}).get('sentiment', 'neutral')
            news_count = (news_data or {}).get('article_count', 0)

            prompt = f"""You are a crypto trading analyst. Analyze {symbol} and give a SHORT prediction.

Technical: RSI={rsi}, Trend={trend}, MACD={macd}
News: sentiment={news_sentiment}, articles={news_count}

Reply with ONLY a JSON object (no markdown, no explanation):
{{"prediction": "bullish" or "bearish" or "neutral", "confidence": 0-100, "reasoning": "one sentence"}}"""

            response = httpx.post(
                f"{base_url}/api/chat",
                json={
                    'model': 'gemma4:latest',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'stream': False,
                    'options': {
                        'temperature': 0.3,
                        'num_predict': 200,
                    }
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get('message', {}).get('content', '')
                
                if not content or len(content.strip()) < 5:
                    return {'prediction': 'neutral', 'prediction_confidence': 50}

                # Try to extract JSON from response
                import json
                try:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        result = json.loads(content[start:end])
                        pred = result.get('prediction', 'neutral').lower()
                        conf = int(result.get('confidence', 50))
                        if pred in ('bullish', 'bearish', 'neutral'):
                            return {
                                'prediction': pred,
                                'prediction_confidence': conf,
                                'reasoning': result.get('reasoning', content[:200]),
                            }
                except (json.JSONDecodeError, ValueError):
                    pass

                # Fallback: keyword extraction from text
                content_lower = content.lower()
                if any(w in content_lower for w in ['bullish', 'buy', 'long', 'upward']):
                    prediction = 'bullish'
                    conf = 65
                elif any(w in content_lower for w in ['bearish', 'sell', 'short', 'downward']):
                    prediction = 'bearish'
                    conf = 65
                else:
                    prediction = 'neutral'
                    conf = 50

                return {
                    'prediction': prediction,
                    'prediction_confidence': conf,
                    'reasoning': content[:300],
                }

            return {'prediction': 'neutral', 'prediction_confidence': 50}

        except Exception as e:
            logger.error(f"Failed to get AI prediction: {e}")
            return {'prediction': 'neutral', 'prediction_confidence': 50}

    @classmethod
    def enrich(cls, symbol: str, technical_data: Dict = None, current_price: float = 0) -> Dict:
        """Gather ALL data sources for signal generation."""
        news = cls.get_news_data(symbol)
        social = cls.get_social_data(symbol)
        macro = cls.get_macro_data(symbol, current_price)
        ai = cls.get_ai_prediction(symbol, technical_data, news)

        return {
            'news_data': news,
            'sentiment_data': {
                'fear_greed_index': social.get('fear_greed_index', 50),
                'social_sentiment': social.get('social_sentiment', 50),
                'whale_signal': social.get('whale_signal'),
            },
            'macro_data': macro,
            'ai_data': ai,
        }


def _analyze_news_keywords(articles) -> Dict:
    """Analyze crypto-related keywords from news articles."""
    keywords = {
        'bullish': 0,
        'bearish': 0,
        'regulation': 0,
        'adoption': 0,
        'hack': 0,
        'etf': 0,
    }

    bullish_words = ['surge', 'rally', 'bull', 'gain', 'rise', 'adoption', 'etf approved', 'institutional']
    bearish_words = ['crash', 'dump', 'bear', 'decline', 'ban', 'hack', 'fraud', 'sec sue']

    for article in articles:
        text = (article.title + ' ' + article.content[:500]).lower()
        for w in bullish_words:
            if w in text:
                keywords['bullish'] += 1
        for w in bearish_words:
            if w in text:
                keywords['bearish'] += 1
        if any(w in text for w in ['regulation', 'sec', 'cftc', 'lawsuit']):
            keywords['regulation'] += 1
        if any(w in text for w in ['adoption', 'partnership', 'institutional']):
            keywords['adoption'] += 1
        if any(w in text for w in ['hack', 'exploit', 'stolen']):
            keywords['hack'] += 1
        if any(w in text for w in ['etf', 'spot etf']):
            keywords['etf'] += 1

    return keywords

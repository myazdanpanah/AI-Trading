"""AI-powered news analysis service."""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..models import NewsArticle
import logging

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """AI-powered news analyzer."""

    BULLISH_KEYWORDS = [
        'surge', 'rally', 'bullish', 'growth', 'adoption', 'approval',
        'partnership', 'launch', 'innovation', 'milestone', 'record',
        'institutional', 'etf approved', 'mainstream', 'upgrade',
    ]

    BEARISH_KEYWORDS = [
        'crash', 'dump', 'bearish', 'decline', 'ban', 'hack',
        'exploit', 'regulation', 'lawsuit', 'sec', 'fraud',
        'ponzi', 'scam', 'bankruptcy', 'liquidation', 'fear',
    ]

    ASSET_KEYWORDS = {
        'bitcoin': 'BTC', 'btc': 'BTC', 'ethereum': 'ETH', 'eth': 'ETH',
        'solana': 'SOL', 'sol': 'SOL', 'xrp': 'XRP', 'ripple': 'XRP',
        'cardano': 'ADA', 'ada': 'ADA', 'dogecoin': 'DOGE', 'doge': 'DOGE',
        'polkadot': 'DOT', 'dot': 'DOT', 'avalanche': 'AVAX', 'avax': 'AVAX',
        'chainlink': 'LINK', 'link': 'LINK', 'polygon': 'MATIC', 'matic': 'MATIC',
    }

    async def analyze_article(self, article_id: str) -> Dict:
        """Analyze a single article."""
        def _get_article():
            return NewsArticle.objects.get(id=article_id)

        article = await asyncio.to_thread(_get_article)

        # Perform analysis
        sentiment = self._analyze_sentiment(article.title, article.content)
        affected_assets = self._detect_assets(article.title, article.content)
        impact_score = self._calculate_impact(article.title, article.content)

        # Update article (sync helper)
        def _update_article():
            article.sentiment = sentiment
            article.impact_score = impact_score
            article.ai_summary = self._generate_summary(article.title, article.content)
            article.save()

        await asyncio.to_thread(_update_article)

        return {
            'article_id': str(article.id),
            'sentiment': sentiment,
            'affected_assets': affected_assets,
            'impact_score': impact_score,
        }

    async def analyze_batch(self, article_ids: List[str]) -> List[Dict]:
        """Analyze multiple articles."""
        results = []
        for article_id in article_ids:
            try:
                result = await self.analyze_article(article_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing article {article_id}: {e}")
        return results

    def _analyze_sentiment(self, title: str, content: str) -> str:
        """Analyze sentiment of text."""
        text = f"{title} {content}".lower()
        bullish_count = sum(1 for word in self.BULLISH_KEYWORDS if word in text)
        bearish_count = sum(1 for word in self.BEARISH_KEYWORDS if word in text)

        if bullish_count > bearish_count + 2:
            return 'bullish'
        elif bearish_count > bullish_count + 2:
            return 'bearish'
        return 'neutral'

    def _detect_assets(self, title: str, content: str) -> List[str]:
        """Detect mentioned crypto assets."""
        text = f"{title} {content}".lower()
        assets = []
        for keyword, symbol in self.ASSET_KEYWORDS.items():
            if keyword in text and symbol not in assets:
                assets.append(symbol)
        return assets[:10]

    def _calculate_impact(self, title: str, content: str) -> int:
        """Calculate impact score (0-100)."""
        text = f"{title} {content}".lower()
        score = 50
        high_impact = ['etf', 'sec', 'regulation', 'hack', 'exploit', 'institutional', 'adoption']
        for keyword in high_impact:
            if keyword in text:
                score += 10
        low_impact = ['meme', 'shib', 'pepe', 'floki']
        for keyword in low_impact:
            if keyword in text:
                score -= 10
        return max(0, min(100, score))

    def _generate_summary(self, title: str, content: str) -> str:
        """Generate a summary of the article."""
        if len(content) > 200:
            return content[:200] + '...'
        return content or title

    async def get_sentiment_summary(self, hours: int = 24) -> Dict:
        """Get sentiment summary for recent articles."""
        def _get_summary():
            since = datetime.now() - timedelta(hours=hours)
            articles = NewsArticle.objects.filter(published_at__gte=since)
            total = articles.count()
            bullish = articles.filter(sentiment='bullish').count()
            bearish = articles.filter(sentiment='bearish').count()
            neutral = articles.filter(sentiment='neutral').count()
            return {
                'total_articles': total,
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral,
            }

        return await asyncio.to_thread(_get_summary)

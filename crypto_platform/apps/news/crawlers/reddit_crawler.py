"""Reddit crawler for crypto news."""
import asyncio
from typing import List, Dict
from datetime import datetime
import httpx
from .base import BaseCrawler, CrawledArticle
import logging

logger = logging.getLogger(__name__)


class RedditCrawler(BaseCrawler):
    """Reddit crawler for crypto subreddits."""

    DEFAULT_SUBREDDITS = [
        'CryptoCurrency',
        'Bitcoin',
        'ethereum',
        'CryptoMarkets',
        'altcoin',
    ]

    def __init__(self, name: str = 'reddit', subreddits: List[str] = None):
        super().__init__(name, 'reddit')
        self.subreddits = subreddits or self.DEFAULT_SUBREDDITS
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={'User-Agent': 'CryptoAI/1.0'}
        )

    async def fetch(self, limit: int = 50) -> List[CrawledArticle]:
        """Fetch posts from Reddit."""
        articles = []
        tasks = [self._fetch_subreddit(sub) for sub in self.subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching subreddit: {result}")
                continue
            articles.extend(result)

        articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return articles[:limit]

    async def _fetch_subreddit(self, subreddit: str) -> List[CrawledArticle]:
        """Fetch posts from a subreddit."""
        try:
            url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit=25'
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            articles = []
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                if post_data.get('stickied'):
                    continue

                published_at = datetime.fromtimestamp(post_data.get('created_utc', 0))
                
                article = CrawledArticle(
                    title=post_data.get('title', ''),
                    content=post_data.get('selftext', '')[:5000],
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    source=f'reddit_{subreddit}',
                    author=post_data.get('author'),
                    published_at=published_at,
                    tags=[subreddit],
                    category='crypto',
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} posts from r/{subreddit}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
            return []

    async def health_check(self) -> bool:
        try:
            response = await self.client.get('https://www.reddit.com/r/CryptoCurrency/hot.json?limit=1')
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()

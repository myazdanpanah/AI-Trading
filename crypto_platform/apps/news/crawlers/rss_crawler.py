"""RSS feed crawler."""
import asyncio
from typing import List, Dict
from datetime import datetime
import feedparser
import httpx
from bs4 import BeautifulSoup
from .base import BaseCrawler, CrawledArticle
import logging

logger = logging.getLogger(__name__)


class RSSCrawler(BaseCrawler):
    """RSS feed crawler for crypto news sources."""

    # Default crypto RSS feeds
    DEFAULT_FEEDS = {
        'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'cointelegraph': 'https://cointelegraph.com/rss',
        'decrypt': 'https://decrypt.co/feed',
        'theblock': 'https://www.theblock.co/rss.xml',
        'cryptonews': 'https://cryptonews.com/news/feed/',
    }

    def __init__(self, name: str = 'rss', feeds: Dict[str, str] = None):
        super().__init__(name, 'rss')
        self.feeds = feeds or self.DEFAULT_FEEDS
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch(self, limit: int = 50) -> List[CrawledArticle]:
        """Fetch articles from RSS feeds."""
        articles = []
        tasks = [self._fetch_feed(name, url) for name, url in self.feeds.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching feed: {result}")
                continue
            articles.extend(result)

        # Sort by published date and limit
        articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return articles[:limit]

    async def _fetch_feed(self, source_name: str, url: str) -> List[CrawledArticle]:
        """Fetch and parse a single RSS feed."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            articles = []

            for entry in feed.entries[:20]:  # Limit per feed
                try:
                    # Parse published date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])

                    # Extract content
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.summary

                    # Clean HTML
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text(strip=True)

                    # Extract tags
                    tags = []
                    if hasattr(entry, 'tags'):
                        tags = [tag.term for tag in entry.tags]

                    article = CrawledArticle(
                        title=entry.get('title', ''),
                        content=content[:5000],  # Limit content length
                        url=entry.get('link', ''),
                        source=source_name,
                        author=entry.get('author'),
                        published_at=published_at,
                        tags=tags,
                        category='crypto',
                    )
                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parsing entry from {source_name}: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} articles from {source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS feed {source_name}: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if RSS feeds are accessible."""
        try:
            # Test first feed
            first_feed = next(iter(self.feeds.values()))
            response = await self.client.get(first_feed)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

"""RSS feed crawler with comprehensive news sources."""
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
    """RSS feed crawler with 60+ trusted news sources."""

    # Comprehensive feeds organized by category
    DEFAULT_FEEDS = {
        # ── Crypto News ──
        'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'cointelegraph': 'https://cointelegraph.com/rss',
        'decrypt': 'https://decrypt.co/feed',
        'theblock': 'https://www.theblock.co/rss.xml',
        'cryptonews': 'https://cryptonews.com/news/feed/',
        'bitcoinmagazine': 'https://bitcoinmagazine.com/feed',
        'dlnews': 'https://www.dlnews.com/rss/',

        # ── Economics & Finance ──
        'bloomberg_markets': 'https://feeds.bloomberg.com/markets/news.rss',
        'ft_markets': 'https://www.ft.com/markets?format=rss',
        'wsj_economy': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
        'cnbc_top': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114',
        'marketwatch': 'https://feeds.marketwatch.com/marketwatch/topstories/',
        'yahoo_finance': 'https://finance.yahoo.com/news/rssindex',

        # ── Politics & Regulation ──
        'politico': 'https://rss.politico.com/politics-news.xml',
        'thehill': 'https://thehill.com/feed/',
        'npr_politics': 'https://feeds.npr.org/1014/rss.xml',

        # ── Geopolitics ──
        'bbc_world': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'aljazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
        'guardian_world': 'https://www.theguardian.com/world/rss',
        'foreign_policy': 'https://www.foreignpolicy.com/feed',
        'diplomat': 'https://thediplomat.com/feed/',
        'dw_news': 'https://rss.dw.com/rdf/rss-en-all',
        'nhk_world': 'https://www3.nhk.or.jp/rss/news/cat0.xml',

        # ── Conflict & Tensions ──
        'war_on_rocks': 'https://warontherocks.com/feed/',
        'crisis_group': 'https://www.crisisgroup.org/rss.xml',
        'military_times': 'https://www.militarytimes.com/arc/outboundfeeds/rss/',
        'bbc_monitoring': 'https://feeds.bbci.co.uk/news/world/rss.xml',

        # ── Energy & Oil ──
        'oilprice': 'https://oilprice.com/rss/main',
        'rigzone': 'https://www.rigzone.com/news/rss/rigzone_latest.aspx',
        'eia': 'https://www.eia.gov/rss/todayinenergy.xml',
        'naturalgas_intel': 'https://www.naturalgasintel.com/feed/',
        'energymonitor': 'https://energymonitor.ai/feed/',

        # ── Central Banks & Fed ──
        'fed_reserve': 'https://www.federalreserve.gov/feeds/press_all.xml',
        'ecb': 'https://www.ecb.europa.eu/rss/press.html',

        # ── Commodities & Gold ──
        'investing_commodities': 'https://www.investing.com/rss/news_25.rss',
        'zerohedge': 'https://feeds.feedburner.com/zerohedge/feed',

        # ── Technology ──
        'techcrunch': 'https://techcrunch.com/feed/',
        'ars_technica': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
    }

    def __init__(self, name: str = 'rss', feeds: Dict[str, str] = None):
        super().__init__(name, 'rss')
        self.feeds = feeds or self.DEFAULT_FEEDS
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; AI-Trading-Bot/1.0)'},
        )

    async def fetch(self, limit: int = 100) -> List[CrawledArticle]:
        """Fetch articles from all RSS feeds concurrently."""
        articles = []
        # Split into batches of 8 to avoid hammering
        feed_items = list(self.feeds.items())
        batch_size = 8

        for i in range(0, len(feed_items), batch_size):
            batch = feed_items[i:i + batch_size]
            tasks = [self._fetch_feed(name, url) for name, url in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching feed batch: {result}")
                    continue
                articles.extend(result)

            # Small delay between batches
            if i + batch_size < len(feed_items):
                await asyncio.sleep(1)

        # Sort by published date (newest first) and limit
        articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return articles[:limit]

    async def _fetch_feed(self, source_name: str, url: str) -> List[CrawledArticle]:
        """Fetch and parse a single RSS feed."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            articles = []

            # Determine category from source name
            category = self._get_category(source_name)

            for entry in feed.entries[:20]:
                try:
                    # Parse published date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])

                    # Extract content
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description

                    # Clean HTML
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text(strip=True)

                    # Extract tags
                    tags = []
                    if hasattr(entry, 'tags'):
                        tags = [tag.term for tag in entry.tags]

                    if not entry.get('title'):
                        continue

                    article = CrawledArticle(
                        title=entry.get('title', ''),
                        content=content[:5000],
                        url=entry.get('link', ''),
                        source=source_name,
                        author=entry.get('author'),
                        published_at=published_at,
                        tags=tags,
                        category=category,
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

    def _get_category(self, source_name: str) -> str:
        """Determine category from source name."""
        crypto = ['coindesk', 'cointelegraph', 'decrypt', 'theblock', 'cryptonews', 'bitcoinmagazine', 'dlnews']
        economics = ['reuters_business', 'bloomberg', 'ft_', 'wsj_', 'cnbc_', 'marketwatch']
        politics = ['politico', 'sec_', 'reuters_politics']
        geopolitics = ['bbc_', 'aljazeera', 'reuters_world', 'ap_', 'guardian_', 'foreign_', 'diplomat']
        conflict = ['war_on_', 'crisis_', 'janes_']
        energy = ['reuters_energy', 'oilprice', 'rigzone', 'eia', 'naturalgas']
        central_banks = ['fed_', 'bis', 'imf_']
        commodities = ['kitco_', 'metals_']
        tech = ['techcrunch', 'ars_']

        for cat_list, cat_name in [
            (crypto, 'crypto'), (economics, 'economics'), (politics, 'politics'),
            (geopolitics, 'geopolitics'), (conflict, 'conflict'), (energy, 'energy'),
            (central_banks, 'central_banks'), (commodities, 'commodities'), (tech, 'technology'),
        ]:
            if any(source_name.startswith(c) or source_name == c for c in cat_list):
                return cat_name
        # Fallback: check for known source names that don't follow prefix pattern
        known = {
            'dw_news': 'geopolitics', 'nhk_world': 'geopolitics', 'bbc_monitoring': 'geopolitics',
            'npr_politics': 'politics', 'military_times': 'conflict',
            'investing_commodities': 'commodities', 'zerohedge': 'economics',
            'energymonitor': 'energy', 'ecb': 'central_banks',
        }
        return known.get(source_name, 'general')

    async def health_check(self) -> bool:
        """Check if RSS feeds are accessible."""
        try:
            first_feed = next(iter(self.feeds.values()))
            response = await self.client.get(first_feed)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

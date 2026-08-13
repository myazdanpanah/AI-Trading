"""X/Twitter social sentiment scraper.

Uses RSS feeds from Nitter instances (privacy-friendly Twitter frontend)
to fetch tweets from configured crypto accounts.
No API key needed.
"""
import asyncio
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScrapedTweet:
    """A scraped tweet."""
    author: str
    text: str
    url: str
    created_at: Optional[datetime] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    category: str = 'general'


class TwitterScraper:
    """Scrape X/Twitter via Nitter RSS feeds."""

    # Nitter instances that support RSS
    NITTER_INSTANCES = [
        'https://nitter.privacydev.net',
        'https://nitter.poast.org',
        'https://nitter.woodland.cafe',
        'https://nitter.cz',
        'https://nitter.1d4.us',
    ]

    # Default crypto accounts to follow
    DEFAULT_ACCOUNTS = {
        # Crypto analysts
        'CryptoCapo_': 'analyst',
        'PlanB_': 'analyst',
        'WillyWoo': 'analyst',
        'CryptoHayes': 'analyst',
        'cobie': 'analyst',
        'Pentosh1': 'analyst',
        'BluntzCapital': 'analyst',
        # Breaking news
        'WatcherGuru': 'news',
        'BitcoinMagazine': 'news',
        'coindesk': 'news',
        'tier10k': 'news',
        'WhaleAlert': 'whale',
        'unusual_whales': 'whale',
        # Geopolitics
        'sentdefender': 'geopolitics',
        'spectatorindex': 'geopolitics',
        'BNONews': 'geopolitics',
        'LiveSquawk': 'markets',
        'FinancialJuice': 'markets',
    }

    def __init__(self, nitter_instance: str = None):
        self.nitter = nitter_instance or self.NITTER_INSTANCES[0]
        self.failed_instances = set()

    async def fetch_user_tweets(self, username: str, limit: int = 20) -> List[ScrapedTweet]:
        """Fetch recent tweets from a user via Nitter RSS."""
        import httpx

        rss_url = f'{self.nitter}/{username}/rss'

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Try different Nitter instances if one fails
            for instance in [self.nitter] + [i for i in self.NITTER_INSTANCES if i != self.nitter]:
                if instance in self.failed_instances:
                    continue

                try:
                    url = f'{instance}/{username}/rss'
                    response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})

                    if response.status_code == 200:
                        return self._parse_rss(response.text, username)
                    else:
                        logger.debug(f"Nitter {instance} returned {response.status_code} for {username}")

                except Exception as e:
                    logger.debug(f"Nitter {instance} failed for {username}: {e}")
                    self.failed_instances.add(instance)
                    continue

        return []

    def _parse_rss(self, xml_text: str, username: str) -> List[ScrapedTweet]:
        """Parse Nitter RSS XML into tweets."""
        tweets = []

        # Simple XML parsing without feedparser (avoid extra dependency)
        items = re.findall(r'<item>(.*?)</item>', xml_text, re.DOTALL)

        for item in items[:20]:
            try:
                title = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
                link = re.search(r'<link>(.*?)</link>', item)
                pub_date = re.search(r'<pubDate>(.*?)</pubDate>', item)
                description = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item, re.DOTALL)

                text = title.group(1).strip() if title else ''
                # Clean HTML from description
                if description:
                    desc = re.sub(r'<[^>]+>', '', description.group(1)).strip()
                    if len(desc) > len(text):
                        text = desc

                url = link.group(1).strip() if link else ''

                # Parse date
                created_at = None
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        created_at = parsedate_to_datetime(pub_date.group(1))
                    except Exception:
                        pass

                # Extract engagement metrics from HTML
                likes = 0
                retweets = 0
                stats_text = re.findall(r'(\d+)\s*(?:like|heart|fav)', xml_text.lower())
                rt_text = re.findall(r'(\d+)\s*(?:retweet|repost)', xml_text.lower())

                if text:
                    tweets.append(ScrapedTweet(
                        author=username,
                        text=text[:500],
                        url=url,
                        created_at=created_at,
                        likes=likes,
                        retweets=retweets,
                        category=self.DEFAULT_ACCOUNTS.get(username, 'general'),
                    ))

            except Exception as e:
                logger.debug(f"Error parsing tweet: {e}")
                continue

        return tweets

    async def fetch_all_accounts(self, accounts: Dict[str, str] = None, limit_per_user: int = 5) -> List[ScrapedTweet]:
        """Fetch tweets from multiple accounts concurrently."""
        accounts = accounts or self.DEFAULT_ACCOUNTS
        all_tweets = []

        tasks = []
        for username, category in accounts.items():
            tasks.append(self._fetch_with_category(username, category, limit_per_user))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_tweets.extend(result)

        # Sort by date (newest first)
        all_tweets.sort(key=lambda t: t.created_at or datetime.min, reverse=True)
        return all_tweets

    async def _fetch_with_category(self, username: str, category: str, limit: int) -> List[ScrapedTweet]:
        """Fetch tweets and tag with category."""
        tweets = await self.fetch_user_tweets(username, limit)
        for t in tweets:
            t.category = category
        return tweets

    def analyze_sentiment(self, tweets: List[ScrapedTweet]) -> Dict:
        """Analyze sentiment from a batch of tweets."""
        if not tweets:
            return {
                'sentiment': 'neutral',
                'score': 50,
                'tweet_count': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'top_topics': [],
            }

        bullish_words = ['bullish', 'buy', 'long', 'pump', 'moon', 'ath', 'surge', 'rally', 'breakout', 'accumulate']
        bearish_words = ['bearish', 'sell', 'short', 'dump', 'crash', 'capitulation', 'decline', 'breakdown', 'distribution']
        fear_words = ['fear', 'panic', 'scared', 'worried', 'uncertain', 'risk', 'danger']

        bullish = 0
        bearish = 0
        fear_count = 0
        topics = {}

        for tweet in tweets:
            text_lower = tweet.text.lower()

            b = sum(1 for w in bullish_words if w in text_lower)
            bear = sum(1 for w in bearish_words if w in text_lower)
            f = sum(1 for w in fear_words if w in text_lower)

            bullish += b
            bearish += bear
            fear_count += f

            # Extract crypto mentions
            symbols = re.findall(r'\$?([A-Z]{2,6})\b', tweet.text)
            for sym in symbols:
                if sym in ('USD', 'USDT', 'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'AND', 'THE', 'FOR'):
                    continue
                topics[sym] = topics.get(sym, 0) + 1

        total = len(tweets)
        total_sentiment_words = bullish + bearish + 1  # +1 to avoid div by 0

        # Calculate score (0-100)
        if bullish + bearish == 0:
            score = 50
        else:
            score = 50 + ((bullish - bearish) / total_sentiment_words) * 30

        # Fear adjustment
        if fear_count > total * 0.3:
            score -= 10

        score = max(0, min(100, int(score)))

        if score > 60:
            sentiment = 'bullish'
        elif score < 40:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'

        # Top topics
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'sentiment': sentiment,
            'score': score,
            'tweet_count': total,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'fear_count': fear_count,
            'top_topics': [{'symbol': t[0], 'mentions': t[1]} for t in sorted_topics],
        }

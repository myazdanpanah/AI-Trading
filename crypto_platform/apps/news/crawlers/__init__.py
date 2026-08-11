"""News crawlers package."""
from .base import BaseCrawler, CrawledArticle
from .rss_crawler import RSSCrawler
from .reddit_crawler import RedditCrawler

__all__ = ['BaseCrawler', 'CrawledArticle', 'RSSCrawler', 'RedditCrawler']

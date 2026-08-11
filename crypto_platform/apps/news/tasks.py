"""Celery tasks for news intelligence engine."""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def crawl_news_sources(self):
    """Crawl all configured news sources."""
    from .crawlers.rss_crawler import RSSCrawler
    from .crawlers.reddit_crawler import RedditCrawler
    from .services.pipeline import NewsProcessingPipeline

    async def _crawl():
        pipeline = NewsProcessingPipeline()
        results = {'rss': {}, 'reddit': {}}

        # Crawl RSS feeds
        try:
            rss_crawler = RSSCrawler()
            rss_articles = await rss_crawler.fetch(limit=100)
            results['rss'] = await pipeline.process_articles(rss_articles, 'rss_feeds')
            await rss_crawler.close()
        except Exception as e:
            logger.error(f"RSS crawl failed: {e}")
            results['rss'] = {'error': str(e)}

        # Crawl Reddit
        try:
            reddit_crawler = RedditCrawler()
            reddit_articles = await reddit_crawler.fetch(limit=100)
            results['reddit'] = await pipeline.process_articles(reddit_articles, 'reddit')
            await reddit_crawler.close()
        except Exception as e:
            logger.error(f"Reddit crawl failed: {e}")
            results['reddit'] = {'error': str(e)}

        return results

    try:
        result = asyncio.run(_crawl())
        logger.info(f"News crawl completed: {result}")
        return result
    except Exception as e:
        logger.error(f"News crawl failed: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def analyze_news_batch(self, article_ids=None):
    """Analyze a batch of news articles."""
    from .services.analyzer import NewsAnalyzer
    from .models import NewsArticle

    async def _analyze():
        analyzer = NewsAnalyzer()

        if article_ids is None:
            # Get recent unanalyzed articles
            articles = await asyncio.to_thread(
                lambda: list(NewsArticle.objects.filter(
                    ai_summary='',
                    impact_score=50  # Default, not analyzed
                ).values_list('id', flat=True)[:50])
            )
            ids_to_analyze = [str(a) for a in articles]
        else:
            ids_to_analyze = article_ids

        if not ids_to_analyze:
            return {'analyzed': 0}

        results = await analyzer.analyze_batch(ids_to_analyze)
        return {'analyzed': len(results), 'results': results}

    try:
        result = asyncio.run(_analyze())
        logger.info(f"News analysis completed: {result}")
        return result
    except Exception as e:
        logger.error(f"News analysis failed: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task
def get_news_sentiment_summary(hours=24):
    """Get sentiment summary for recent news."""
    from .services.analyzer import NewsAnalyzer

    async def _get_summary():
        analyzer = NewsAnalyzer()
        return await analyzer.get_sentiment_summary(hours)

    return asyncio.run(_get_summary())


@shared_task
def cleanup_old_news(days=30):
    """Clean up old news articles."""
    from .models import NewsArticle
    from datetime import timedelta
    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=days)
    deleted_count = NewsArticle.objects.filter(
        published_at__lt=cutoff
    ).delete()[0]

    logger.info(f"Cleaned up {deleted_count} old news articles")
    return {'deleted': deleted_count}

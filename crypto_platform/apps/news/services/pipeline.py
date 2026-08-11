"""News processing pipeline."""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from hashlib import md5
from ..models import NewsSource, NewsArticle, NewsEntity
from ..crawlers.base import CrawledArticle
import logging

logger = logging.getLogger(__name__)


class NewsProcessingPipeline:
    """Process and store news articles."""

    def __init__(self):
        self.stats = {
            'total_fetched': 0,
            'total_new': 0,
            'total_duplicates': 0,
            'total_errors': 0,
        }

    def generate_content_hash(self, title: str, url: str) -> str:
        """Generate hash for duplicate detection."""
        content = f"{title.lower().strip()}:{url.lower().strip()}"
        return md5(content.encode()).hexdigest()

    async def process_articles(self, articles: List[CrawledArticle], source_name: str) -> Dict:
        """Process a batch of crawled articles."""
        self.stats['total_fetched'] += len(articles)

        # Get or create source (sync helper)
        def _get_or_create_source():
            source, _ = NewsSource.objects.get_or_create(
                name=source_name,
                defaults={'url': f'https://{source_name}.com', 'source_type': 'rss'}
            )
            return source

        source = await asyncio.to_thread(_get_or_create_source)

        results = {
            'new': 0,
            'duplicates': 0,
            'errors': 0,
        }

        for article in articles:
            try:
                # Check for duplicates (sync helper)
                def _check_exists():
                    return NewsArticle.objects.filter(url=article.url).exists()

                exists = await asyncio.to_thread(_check_exists)

                if exists:
                    results['duplicates'] += 1
                    continue

                # Create article (sync helper)
                def _create_article():
                    return NewsArticle.objects.create(
                        source=source,
                        title=article.title,
                        content=article.content,
                        url=article.url,
                        author=article.author or '',
                        language=article.language,
                        published_at=article.published_at or datetime.now(),
                        sentiment='neutral',
                        impact_score=50,
                    )

                await asyncio.to_thread(_create_article)
                results['new'] += 1

            except Exception as e:
                logger.error(f"Error processing article: {e}")
                results['errors'] += 1

        self.stats['total_new'] += results['new']
        self.stats['total_duplicates'] += results['duplicates']
        self.stats['total_errors'] += results['errors']

        logger.info(f"Processed {len(articles)} articles: {results}")
        return results

    async def extract_entities(self, article_id: str) -> List[Dict]:
        """Extract entities from article content."""
        def _get_article():
            return NewsArticle.objects.get(id=article_id)

        article = await asyncio.to_thread(_get_article)

        # Simple entity extraction
        entities = []
        crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 
                          'crypto', 'blockchain', 'defi', 'nft', 'web3']
        
        content_lower = article.content.lower()
        for keyword in crypto_keywords:
            if keyword in content_lower:
                entities.append({
                    'type': 'crypto',
                    'name': keyword.upper(),
                    'sentiment': 'neutral',
                })

        # Store entities (sync helper)
        def _create_entities():
            for entity_data in entities:
                NewsEntity.objects.create(
                    article=article,
                    entity_type=entity_data['type'],
                    name=entity_data['name'],
                    sentiment=entity_data['sentiment'],
                )

        await asyncio.to_thread(_create_entities)
        return entities

    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        return self.stats

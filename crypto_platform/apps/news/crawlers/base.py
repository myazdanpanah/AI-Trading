"""Base crawler interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledArticle:
    """Standardized crawled article data."""
    title: str
    content: str
    url: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str = 'en'
    tags: List[str] = None
    category: str = 'crypto'

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseCrawler(ABC):
    """Base crawler interface."""

    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type
        self.is_active = True

    @abstractmethod
    async def fetch(self, limit: int = 50) -> List[CrawledArticle]:
        """Fetch articles from source."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if crawler is healthy."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name})>"

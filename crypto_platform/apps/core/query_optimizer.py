"""Query optimization utilities for common database patterns."""
from typing import List, Optional, TypedDict, Any
from django.db import models
from django.db.models import QuerySet, Prefetch, F, Q


class PaginatedResult(TypedDict):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class QueryOptimizer:
    """Utilities for optimizing database queries."""
    
    @staticmethod
    def select_related_fields(queryset: QuerySet, fields: List[str]) -> QuerySet:
        """Apply select_related for foreign key joins."""
        return queryset.select_related(*fields)
    
    @staticmethod
    def prefetch_related_fields(queryset: QuerySet, fields: List[str]) -> QuerySet:
        """Apply prefetch_related for reverse relationships and many-to-many."""
        return queryset.prefetch_related(*fields)
    
    @staticmethod
    def optimize_signal_queries(queryset: QuerySet) -> QuerySet:
        """Optimize Signal model queries with common related objects."""
        return queryset.select_related(
            'risk_profile'
        ).prefetch_related(
            'reasons',
            'performance'
        )
    
    @staticmethod
    def optimize_learning_queries(queryset: QuerySet) -> QuerySet:
        """Optimize Learning model queries."""
        return queryset.select_related(
            'signal'
        )
    
    @staticmethod
    def paginate_queryset(
        queryset: QuerySet, 
        page: int = 1, 
        page_size: int = 50,
        max_page_size: int = 100
    ) -> PaginatedResult:
        """Paginate a queryset with metadata."""
        page_size = min(page_size, max_page_size)
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        items = list(queryset[start:end])
        
        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            has_next=end < total,
            has_previous=page > 1,
        )


class BulkOperations:
    """Bulk database operations for improved performance."""
    
    @staticmethod
    def bulk_create_signals(signals_data: List[dict]) -> List[models.Model]:
        """Bulk create Signal objects."""
        from apps.signals.models import Signal
        return Signal.objects.bulk_create([
            Signal(**data) for data in signals_data
        ], batch_size=1000)
    
    @staticmethod
    def bulk_update_signals(signals: List[models.Model], fields: List[str]):
        """Bulk update Signal objects."""
        from apps.signals.models import Signal
        Signal.objects.bulk_update(signals, fields, batch_size=1000)
    
    @staticmethod
    def bulk_create_market_data(data_list: List[dict]) -> List[models.Model]:
        """Bulk create MarketData objects."""
        from apps.market.models import MarketData
        return MarketData.objects.bulk_create([
            MarketData(**data) for data in data_list
        ], batch_size=5000)
    
    @staticmethod
    def bulk_create_sentiment(data_list: List[dict]) -> List[models.Model]:
        """Bulk create SentimentData objects."""
        from apps.sentiment.models import SentimentData
        return SentimentData.objects.bulk_create([
            SentimentData(**data) for data in data_list
        ], batch_size=1000)


class IndexSuggestions:
    """Suggestions for database indexes based on query patterns."""
    
    SUGGESTED_INDEXES = {
        'signals': [
            {'fields': ['symbol', 'created_at'], 'name': 'idx_signal_symbol_created'},
            {'fields': ['direction', 'confidence'], 'name': 'idx_signal_direction_confidence'},
            {'fields': ['timeframe', 'created_at'], 'name': 'idx_signal_timeframe_created'},
        ],
        'market': [
            {'fields': ['symbol', 'timestamp'], 'name': 'idx_market_symbol_timestamp'},
            {'fields': ['exchange', 'symbol'], 'name': 'idx_market_exchange_symbol'},
        ],
        'sentiment': [
            {'fields': ['symbol', 'timestamp'], 'name': 'idx_sentiment_symbol_timestamp'},
            {'fields': ['source', 'created_at'], 'name': 'idx_sentiment_source_created'},
        ],
        'feedback': [
            {'fields': ['symbol', 'timeframe'], 'name': 'idx_market_memory_symbol_timeframe'},
            {'fields': ['market_condition'], 'name': 'idx_market_memory_condition'},
        ],
    }
    
    @classmethod
    def get_migration_indexes(cls, app_label: str) -> List[dict]:
        """Get suggested indexes for an app's models."""
        return cls.SUGGESTED_INDEXES.get(app_label, [])

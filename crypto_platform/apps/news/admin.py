from django.contrib import admin
from .models import NewsSource, NewsArticle, NewsEntity

@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active']


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'sentiment', 'impact_score', 'published_at']
    list_filter = ['sentiment', 'language']
    search_fields = ['title', 'content']


@admin.register(NewsEntity)
class NewsEntityAdmin(admin.ModelAdmin):
    list_display = ['article', 'entity_type', 'name', 'sentiment']
    list_filter = ['entity_type']

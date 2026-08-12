from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'entries', views.JournalEntryViewSet, basename='journal-entries')
router.register(r'insights', views.JournalInsightViewSet, basename='journal-insights')
router.register(r'sources', views.NewsSourceViewSet, basename='news-sources')

urlpatterns = [
    path('', include(router.urls)),
    path('context/', views.market_context_current, name='market-context'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsSourceViewSet, NewsArticleViewSet, NewsEntityViewSet

router = DefaultRouter()
router.register(r'sources', NewsSourceViewSet)
router.register(r'articles', NewsArticleViewSet)
router.register(r'entities', NewsEntityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

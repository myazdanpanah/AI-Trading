"""URL configuration for Crypto AI Signal Platform."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.core.health_views import (
    health_check_detailed,
    readiness_probe,
    liveness_probe,
    metrics_endpoint,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'healthy', 'service': 'crypto-platform'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health-check'),
    path('health/detailed/', health_check_detailed, name='health-check-detailed'),
    path('health/ready/', readiness_probe, name='readiness-probe'),
    path('health/live/', liveness_probe, name='liveness-probe'),
    path('metrics/', metrics_endpoint, name='metrics'),
    # OpenAPI documentation (disable in production via SPECTACULAR_SETTINGS['SERVE_INCLUDE_SCHEMA'])
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/news/', include('apps.news.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/ai/', include('apps.ai_engine.urls')),
    path('api/signals/', include('apps.signals.urls')),
    path('api/learning/', include('apps.learning.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/technical-analysis/', include('apps.technical_analysis.urls')),
    path('api/sentiment/', include('apps.sentiment.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
    path('api/mobile/', include('apps.mobile.urls')),
    path('api/arbitrage/', include('apps.arbitrage.urls')),
    path('api/social/', include('apps.social.urls')),
    path('api/portfolio/', include('apps.portfolio.urls')),
    path('api/skills/', include('apps.trading_skills.urls')),
]

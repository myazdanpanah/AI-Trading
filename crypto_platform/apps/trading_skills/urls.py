from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'regime-history', views.RegimeAnalysisViewSet, basename='regime-history')
router.register(r'signal-reviews', views.SignalReviewViewSet, basename='signal-reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('skills/', views.skill_definitions, name='skill-definitions'),
    path('regime-analysis/', views.run_regime_analysis, name='run-regime-analysis'),
    path('position-sizer/', views.run_position_sizer, name='run-position-sizer'),
    path('technical-analysis/', views.run_technical_analysis, name='run-technical-analysis'),
    path('full-analysis/', views.full_analysis, name='full-analysis'),
    path('candlestick-analysis/', views.run_candlestick_analysis, name='candlestick-analysis'),
]

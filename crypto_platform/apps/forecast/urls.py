"""Forecast URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'forecasts', views.PriceForecastViewSet)
router.register(r'cycles', views.ForecastCycleViewSet)
router.register(r'weights', views.ModelWeightViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('run/', views.run_forecast, name='run-forecast'),
    path('verify/', views.verify_forecasts, name='verify-forecasts'),
    path('learn/', views.run_learning_cycle, name='run-learning'),
    path('accuracy/', views.accuracy_stats, name='accuracy-stats'),
    path('learning-stats/', views.learning_stats, name='learning-stats'),
    path('reset-weights/', views.reset_weights, name='reset-weights'),
    path('full-cycle/', views.run_full_cycle, name='full-cycle'),
]

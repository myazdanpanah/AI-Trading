"""Portfolio URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio')
router.register(r'allocations', views.PortfolioAllocationViewSet, basename='allocation')
router.register(r'rebalance-history', views.RebalanceHistoryViewSet, basename='rebalance-history')
router.register(r'tax-lots', views.TaxLotViewSet, basename='tax-lot')
router.register(r'tax-reports', views.TaxReportViewSet, basename='tax-report')

urlpatterns = [
    path('', include(router.urls)),
]

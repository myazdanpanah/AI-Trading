from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, UserWatchlistViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'watchlist', UserWatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('', include(router.urls)),
]

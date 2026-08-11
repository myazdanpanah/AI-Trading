"""Social trading URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'traders', views.TraderViewSet, basename='trader')
router.register(r'follows', views.FollowRelationshipViewSet, basename='follow')
router.register(r'copy-trades', views.CopyTradeViewSet, basename='copy-trade')
router.register(r'signals', views.TraderSignalViewSet, basename='trader-signal')
router.register(r'comments', views.SocialCommentViewSet, basename='social-comment')

urlpatterns = [
    path('', include(router.urls)),
]

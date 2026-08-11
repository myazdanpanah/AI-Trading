"""User views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import User, UserProfile, UserWatchlist
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer, UserWatchlistSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


class UserWatchlistViewSet(viewsets.ModelViewSet):
    """Manage user's watchlist."""
    serializer_class = UserWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserWatchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Sync entire watchlist (replace with new list)."""
        items = request.data.get('items', [])
        # Delete existing
        UserWatchlist.objects.filter(user=request.user).delete()
        # Create new
        watchlist = []
        for i, item in enumerate(items):
            wl = UserWatchlist.objects.create(
                user=request.user,
                symbol=item['symbol'],
                display_name=item.get('display_name', ''),
                coin_id=item.get('coin_id', ''),
                order=item.get('order', i),
                is_favorite=item.get('is_favorite', False),
            )
            watchlist.append(wl)
        serializer = self.get_serializer(watchlist, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status."""
        item = self.get_object()
        item.is_favorite = not item.is_favorite
        item.save()
        return Response(self.get_serializer(item).data)

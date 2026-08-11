"""Social trading views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Trader, FollowRelationship, CopyTrade, TraderSignal, SocialComment
from .serializers import (TraderSerializer, FollowRelationshipSerializer, 
                          CopyTradeSerializer, TraderSignalSerializer, SocialCommentSerializer)
from .services.copy_trader import CopyTrader


class TraderViewSet(viewsets.ModelViewSet):
    """API endpoint for trader profiles."""
    serializer_class = TraderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Trader.objects.filter(is_public=True)
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get top traders by performance."""
        traders = Trader.objects.filter(is_public=True).order_by('-win_rate')[:20]
        serializer = self.get_serializer(traders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def signals(self, request, pk=None):
        """Get signals shared by a trader."""
        trader = self.get_object()
        signals = TraderSignal.objects.filter(trader=trader)
        serializer = TraderSignalSerializer(signals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def setup_profile(self, request):
        """Create or update trader profile."""
        trader, created = Trader.objects.update_or_create(
            user=request.user,
            defaults={
                'display_name': request.data.get('display_name', request.user.username),
                'bio': request.data.get('bio', ''),
                'is_public': request.data.get('is_public', False),
                'allow_copy_trading': request.data.get('allow_copy_trading', False),
                'copy_trading_fee_percent': request.data.get('copy_trading_fee_percent', 0),
            }
        )
        return Response(TraderSerializer(trader).data)


class FollowRelationshipViewSet(viewsets.ModelViewSet):
    """API endpoint for follow relationships."""
    serializer_class = FollowRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FollowRelationship.objects.filter(follower=self.request.user)
    
    def perform_create(self, serializer):
        follow = serializer.save(follower=self.request.user)
        # Update follower count
        follow.trader.followers_count = follow.trader.followers.count()
        follow.trader.save()
    
    @action(detail=True, methods=['post'])
    def toggle_copy(self, request, pk=None):
        """Toggle copy trading for a followed trader."""
        follow = self.get_object()
        follow.copy_trading = not follow.copy_trading
        follow.save()
        return Response({'copy_trading': follow.copy_trading})


class CopyTradeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for copy trade history."""
    serializer_class = CopyTradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CopyTrade.objects.filter(follower=self.request.user)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get copy trading performance summary."""
        trades = CopyTrade.objects.filter(follower=request.user, status='closed')
        
        total_trades = trades.count()
        winning_trades = trades.filter(pnl__gt=0).count()
        total_pnl = sum(t.pnl for t in trades)
        
        return Response({
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': float(total_pnl),
        })


class TraderSignalViewSet(viewsets.ModelViewSet):
    """API endpoint for trader signals."""
    serializer_class = TraderSignalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TraderSignal.objects.filter(trader__is_public=True)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a trader signal."""
        signal = self.get_object()
        signal.likes_count += 1
        signal.save()
        return Response({'likes_count': signal.likes_count})


class SocialCommentViewSet(viewsets.ModelViewSet):
    """API endpoint for comments on trader signals."""
    serializer_class = SocialCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialComment.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

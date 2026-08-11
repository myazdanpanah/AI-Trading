"""Mobile app views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeviceToken, MobileAlert, MobileWidget
from .serializers import DeviceTokenSerializer, MobileAlertSerializer, MobileWidgetSerializer


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """API endpoint for managing device tokens."""
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new device token."""
        token = request.data.get('token')
        platform = request.data.get('platform')
        device_name = request.data.get('device_name', '')
        
        if not token or not platform:
            return Response(
                {'error': 'token and platform are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'platform': platform,
                'device_name': device_name,
                'is_active': True,
            }
        )
        
        return Response({
            'id': str(device.id),
            'created': created,
        })
    
    @action(detail=False, methods=['post'])
    def deactivate(self, request):
        """Deactivate a device token."""
        token = request.data.get('token')
        DeviceToken.objects.filter(token=token, user=request.user).update(is_active=False)
        return Response({'status': 'deactivated'})


class MobileAlertViewSet(viewsets.ModelViewSet):
    """API endpoint for managing mobile alerts."""
    serializer_class = MobileAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MobileAlert.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test an alert configuration."""
        alert = self.get_object()
        # In production, send a test push notification
        return Response({
            'status': 'test_sent',
            'alert': str(alert),
        })


class MobileWidgetViewSet(viewsets.ModelViewSet):
    """API endpoint for managing mobile widgets."""
    serializer_class = MobileWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MobileWidget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

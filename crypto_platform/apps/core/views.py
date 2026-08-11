"""Base views."""
from rest_framework import viewsets

class BaseModelViewSet(viewsets.ModelViewSet):
    def perform_destroy(self, instance):
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete()
        else:
            instance.delete()

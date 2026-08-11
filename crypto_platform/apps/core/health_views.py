"""Health check API endpoints for monitoring."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status as http_status
from drf_spectacular.utils import extend_schema, extend_schema_view
from .monitoring import HealthChecker, metrics


@extend_schema(tags=['Monitoring'], summary='Basic health check')
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Basic health check endpoint."""
    return Response({'status': 'healthy', 'service': 'crypto-platform'})


@extend_schema(tags=['Monitoring'], summary='Detailed health check with service status')
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_detailed(request):
    """Detailed health check including all services."""
    health = HealthChecker.check_all()
    
    status_code = http_status.HTTP_200_OK if health['status'] == 'healthy' else http_status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health, status=status_code)


@extend_schema(tags=['Monitoring'], summary='Get application metrics')
@api_view(['GET'])
@permission_classes([AllowAny])
def metrics_endpoint(request):
    """Expose metrics in Prometheus format."""
    accept = request.headers.get('Accept', '')
    
    if 'text/plain' in accept or 'prometheus' in accept:
        from rest_framework.response import Response
        from django.http import HttpResponse
        prometheus_format = metrics.get_prometheus_format()
        return HttpResponse(prometheus_format, content_type='text/plain; version=0.0.4')
    
    return Response(metrics.get_metrics())


@extend_schema(tags=['Monitoring'], summary='Readiness probe for Kubernetes')
@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_probe(request):
    """Readiness probe - checks if service is ready to accept traffic."""
    health = HealthChecker.check_database()
    
    redis_health = HealthChecker.check_redis()
    
    if health['status'] == 'healthy' and redis_health['status'] == 'healthy':
        return Response({'status': 'ready'})
    else:
        return Response({'status': 'not ready', 'reason': health.get('message', '') + ' ' + redis_health.get('message', '')}, 
                       status=http_status.HTTP_503_SERVICE_UNAVAILABLE)


@extend_schema(tags=['Monitoring'], summary='Liveness probe for Kubernetes')
@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_probe(request):
    """Liveness probe - checks if service is alive."""
    return Response({'status': 'alive'})

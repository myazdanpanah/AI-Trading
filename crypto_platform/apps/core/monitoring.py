"""Monitoring utilities for Prometheus metrics and system health checks."""
import time
import logging
from typing import Dict, Any
from functools import wraps
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and expose metrics for Prometheus."""
    
    _instance = None
    _metrics = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {
                'requests_total': 0,
                'requests_by_status': {},
                'response_times': [],
                'celery_tasks': {},
                'database_queries': 0,
            }
        return cls._instance
    
    def increment_requests(self, status_code: int):
        """Increment request counter."""
        self._metrics['requests_total'] += 1
        status_key = str(status_code // 100) + 'xx'
        self._metrics['requests_by_status'][status_key] = \
            self._metrics['requests_by_status'].get(status_key, 0) + 1
    
    def record_response_time(self, duration: float):
        """Record response time."""
        self._metrics['response_times'].append(duration)
        # Keep only last 1000 measurements
        if len(self._metrics['response_times']) > 1000:
            self._metrics['response_times'] = self._metrics['response_times'][-1000:]
    
    def record_celery_task(self, task_name: str, duration: float, success: bool):
        """Record Celery task execution."""
        if task_name not in self._metrics['celery_tasks']:
            self._metrics['celery_tasks'][task_name] = {
                'total': 0, 'success': 0, 'failure': 0, 'durations': []
            }
        task = self._metrics['celery_tasks'][task_name]
        task['total'] += 1
        if success:
            task['success'] += 1
        else:
            task['failure'] += 1
        task['durations'].append(duration)
        # Keep only last 1000 measurements
        if len(task['durations']) > 1000:
            task['durations'] = task['durations'][-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        response_times = self._metrics['response_times']
        return {
            'requests_total': self._metrics['requests_total'],
            'requests_by_status': self._metrics['requests_by_status'],
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            'celery_tasks': self._metrics['celery_tasks'],
        }
    
    def get_prometheus_format(self) -> str:
        """Format metrics in Prometheus exposition format."""
        lines = []
        lines.append('# HELP crypto_requests_total Total number of requests')
        lines.append('# TYPE crypto_requests_total counter')
        lines.append(f'crypto_requests_total {self._metrics["requests_total"]}')
        
        lines.append('# HELP crypto_response_time_seconds Average response time')
        lines.append('# TYPE crypto_response_time_seconds gauge')
        response_times = self._metrics['response_times']
        avg_time = sum(response_times) / len(response_times) if response_times else 0
        lines.append(f'crypto_response_time_seconds {avg_time:.4f}')
        
        for status, count in self._metrics['requests_by_status'].items():
            lines.append(f'crypto_requests_by_status{{status="{status}"}} {count}')
        
        return '\n'.join(lines)


# Global metrics collector instance
metrics = MetricsCollector()


def track_metrics(view_func):
    """Decorator to track request metrics."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        response = view_func(request, *args, **kwargs)
        duration = time.time() - start_time
        
        status_code = getattr(response, 'status_code', 200)
        metrics.increment_requests(status_code)
        metrics.record_response_time(duration)
        
        return response
    return wrapper


class HealthChecker:
    """Check health of all services."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'healthy', 'message': 'Database connection successful'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            value = cache.get('health_check')
            if value == 'ok':
                return {'status': 'healthy', 'message': 'Redis connection successful'}
            return {'status': 'unhealthy', 'message': 'Redis read/write failed'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def check_celery() -> Dict[str, Any]:
        """Check Celery worker status."""
        try:
            from celery import current_app
            inspector = current_app.control.inspect(timeout=5.0)
            active = inspector.active()
            if active:
                return {'status': 'healthy', 'message': f'{len(active)} workers active'}
            return {'status': 'unhealthy', 'message': 'No active workers'}
        except (ConnectionError, TimeoutError, OSError) as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def check_disk_space() -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024 ** 3)
            if free_gb > 1:
                return {'status': 'healthy', 'message': f'{free_gb:.2f} GB free'}
            return {'status': 'warning', 'message': f'Low disk space: {free_gb:.2f} GB free'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @classmethod
    def check_all(cls) -> Dict[str, Any]:
        """Check all services."""
        checks = {
            'database': cls.check_database(),
            'redis': cls.check_redis(),
            'celery': cls.check_celery(),
            'disk': cls.check_disk_space(),
        }
        
        all_healthy = all(c['status'] == 'healthy' for c in checks.values())
        
        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': time.time(),
            'services': checks,
        }

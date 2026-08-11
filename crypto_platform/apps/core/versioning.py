"""API versioning utilities."""
from rest_framework.versioning import URLPathVersioning


class ApiVersioning(URLPathVersioning):
    """Custom API versioning with URL path versioning."""
    
    # Supported versions
    allowed_versions = ['v1']
    version_param = 'version'
    
    # Default version
    default_version = 'v1'


def get_api_version(request):
    """Extract API version from request."""
    return getattr(request, 'version', 'v1')

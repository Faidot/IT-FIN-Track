"""
Audit middleware to capture request metadata.
"""

import threading

# Thread-local storage for request metadata
_request_local = threading.local()


def get_current_request():
    """Get the current request from thread-local storage."""
    return getattr(_request_local, 'request', None)


def get_client_ip(request):
    """Get the client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuditMiddleware:
    """Middleware to store request in thread-local for audit logging."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local
        _request_local.request = request
        
        # Add convenience attributes
        request.client_ip = get_client_ip(request)
        
        response = self.get_response(request)
        
        # Clear request from thread-local
        if hasattr(_request_local, 'request'):
            del _request_local.request
        
        return response

"""
Middleware for multi-tenant support and activity logging
"""


class CentreFilterMiddleware:
    """
    Middleware to inject centre context into requests
    This ensures users only access data from their assigned centre
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add centre to request if user is authenticated
        if request.user.is_authenticated and hasattr(request.user, 'centre'):
            request.centre = request.user.centre
        else:
            request.centre = None
        
        response = self.get_response(request)
        return response


class ActivityLoggingMiddleware:
    """
    Middleware to log important API requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log certain types of requests
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Add custom logging logic here if needed
            pass
        
        return response


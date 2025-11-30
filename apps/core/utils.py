from functools import wraps
from apps.users.models import ActivityLog


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(action_type, description_template):
    """
    Decorator to log user activities
    Usage: @log_activity('PROFILE_UPDATE', 'User updated their profile')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            response = func(self, request, *args, **kwargs)
            
            # Only log if request was successful
            if response.status_code < 400:
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        action_type=action_type,
                        description=description_template,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception:
                    # Don't fail the request if logging fails
                    pass
            
            return response
        return wrapper
    return decorator


def log_sensitive_access(user, resource_type, resource_id, request):
    """
    Log access to sensitive data
    """
    ActivityLog.objects.create(
        user=user,
        action_type='SENSITIVE_DATA_ACCESS',
        description=f'Accessed {resource_type} with ID {resource_id}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


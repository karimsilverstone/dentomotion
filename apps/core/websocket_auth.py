"""
Custom JWT authentication middleware for Django Channels WebSocket connections
"""
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs


@database_sync_to_async
def get_user_from_token(token_key):
    """Get user from JWT token"""
    from apps.users.models import User
    
    try:
        print(f"[JWT_MIDDLEWARE] Validating token...")
        # Validate token and get user_id
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        print(f"[JWT_MIDDLEWARE] Token valid, user_id: {user_id}")
        
        # Get user from database
        user = User.objects.get(id=user_id)
        print(f"[JWT_MIDDLEWARE] User found: {user.email}")
        return user
    except (InvalidToken, TokenError) as e:
        print(f"[JWT_MIDDLEWARE] ❌ Token validation failed: {str(e)}")
        return AnonymousUser()
    except User.DoesNotExist:
        print(f"[JWT_MIDDLEWARE] ❌ User not found in database")
        return AnonymousUser()
    except KeyError as e:
        print(f"[JWT_MIDDLEWARE] ❌ Key error: {str(e)}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Supports token in:
    1. Query parameter: ?token=YOUR_JWT_TOKEN
    2. Headers: Authorization: Bearer YOUR_JWT_TOKEN (if supported by client)
    """
    
    async def __call__(self, scope, receive, send):
        print(f"[JWT_MIDDLEWARE] Processing WebSocket connection")
        
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        print(f"[JWT_MIDDLEWARE] Query string: {query_string}")
        
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            print(f"[JWT_MIDDLEWARE] Token found in query string: {token[:20]}...")
        
        # If no token in query string, try headers
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                print(f"[JWT_MIDDLEWARE] Token found in headers: {token[:20]}...")
        
        # Authenticate user with token
        if token:
            user = await get_user_from_token(token)
            scope['user'] = user
            if user.is_authenticated:
                print(f"[JWT_MIDDLEWARE] ✅ User authenticated: {user.id} - {user.email}")
            else:
                print(f"[JWT_MIDDLEWARE] ❌ Token invalid - user not authenticated")
        else:
            print(f"[JWT_MIDDLEWARE] ❌ No token provided")
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Helper function to wrap URLRouter with JWT authentication.
    Use this instead of AuthMiddlewareStack for WebSocket routes.
    """
    return JWTAuthMiddleware(inner)


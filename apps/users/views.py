from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, ActivityLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, ActivityLogSerializer
)


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, action_type, description, request):
    """Helper function to log user activity"""
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model
    Implements role-based access control
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on role"""
        user = self.request.user
        
        # Super Admin sees all users
        if user.role == 'SUPER_ADMIN':
            return User.objects.all()
        
        # Centre Manager sees users in their centre
        elif user.role == 'CENTRE_MANAGER':
            return User.objects.filter(centre=user.centre)
        
        # Others see only themselves
        return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """Only Super Admin and Centre Managers can create users"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to create users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log activity
        log_activity(user, 'PASSWORD_CHANGE', 'User changed their password', request)
        
        return Response({'message': 'Password changed successfully.'})
    
    @action(detail=True, methods=['get'], url_path='activity-logs')
    def activity_logs(self, request, pk=None):
        """Get activity logs for a user (Managers and Super Admin only)"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to view activity logs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        logs = ActivityLog.objects.filter(user=user)
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints"""
    
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login endpoint with JWT token generation"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            # Check if account is locked
            if user.is_account_locked():
                return Response(
                    {'error': 'Account is locked. Please try again later.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Authenticate user
            authenticated_user = authenticate(request, email=email, password=password)
            
            if authenticated_user:
                # Reset failed attempts and update last login
                user.record_successful_login()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Log successful login
                log_activity(user, 'LOGIN_SUCCESS', f'User logged in from {get_client_ip(request)}', request)
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                })
            else:
                # Record failed attempt
                user.record_failed_login()
                
                # Log failed login
                log_activity(user, 'LOGIN_FAILED', f'Failed login attempt from {get_client_ip(request)}', request)
                
                return Response(
                    {'error': 'Invalid credentials.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout endpoint (blacklist refresh token)"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='password-reset')
    def password_reset(self, request):
        """Initiate password reset (sends email)"""
        # This will be implemented in Phase 3 with email integration
        return Response({
            'message': 'Password reset functionality will be available in Phase 3.'
        })


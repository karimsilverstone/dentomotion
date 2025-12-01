from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User, ActivityLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, ActivityLogSerializer,
    LoginSerializer, LoginResponseSerializer, LogoutSerializer,
    PasswordResetRequestSerializer
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


@extend_schema_view(
    list=extend_schema(
        summary="List Users",
        tags=['Users'],
        description="""
        List users with optional role filtering.
        
        **Filter by Role (2 options):**
        
        1. **Single role** - Use `role` parameter:
           - `?role=TEACHER` - Get only teachers
           - `?role=STUDENT` - Get only students
        
        2. **Multiple roles** - Use `roles` parameter:
           - `?roles=TEACHER,STUDENT` - Get teachers and students
           - `?roles=TEACHER,STUDENT,PARENT` - Get multiple roles
        
        **Available Roles:**
        - SUPER_ADMIN
        - CENTRE_MANAGER
        - TEACHER
        - STUDENT
        - PARENT
        
        **Examples:**
        - `/api/users/` - All users (based on permissions)
        - `/api/users/?role=TEACHER` - Only teachers
        - `/api/users/?roles=TEACHER,STUDENT` - Teachers and students
        - `/api/users/?role=STUDENT&page=2` - Students on page 2
        - `/api/users/?roles=TEACHER,PARENT&page_size=50` - Teachers and parents (50 per page)
        
        **Note:** If both `role` and `roles` are provided, `roles` takes priority.
        """,
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number for pagination'
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of items per page (max 100)'
            ),
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by single role (e.g., TEACHER, STUDENT, PARENT)',
                required=False,
                enum=['SUPER_ADMIN', 'CENTRE_MANAGER', 'TEACHER', 'STUDENT', 'PARENT']
            ),
            OpenApiParameter(
                name='roles',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by multiple roles, comma-separated (e.g., TEACHER,STUDENT). Takes priority over "role"',
                required=False
            ),
        ]
    ),
    create=extend_schema(summary="Create User", tags=['Users']),
    retrieve=extend_schema(summary="Get User Details", tags=['Users']),
    update=extend_schema(summary="Update User", tags=['Users']),
    partial_update=extend_schema(summary="Partial Update User", tags=['Users']),
    destroy=extend_schema(summary="Delete User", tags=['Users']),
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
        """Filter users based on role and optional roles parameter"""
        user = self.request.user
        
        # Base queryset based on user's role
        if user.role == 'SUPER_ADMIN':
            queryset = User.objects.all()
        elif user.role == 'CENTRE_MANAGER':
            queryset = User.objects.filter(centre=user.centre)
        else:
            queryset = User.objects.filter(id=user.id)
        
        # Apply role filtering if provided
        # Support both 'roles' (comma-separated) and 'role' (single)
        roles_param = self.request.query_params.get('roles', None)
        role_param = self.request.query_params.get('role', None)
        
        if roles_param:
            # Priority to 'roles' - supports comma-separated values
            # Example: ?roles=TEACHER,STUDENT,PARENT
            roles_list = [role.strip().upper() for role in roles_param.split(',')]
            queryset = queryset.filter(role__in=roles_list)
        elif role_param:
            # Fallback to 'role' - single value
            # Example: ?role=TEACHER
            queryset = queryset.filter(role=role_param.strip().upper())
        
        return queryset
    
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
    
    @extend_schema(
        summary="User Login",
        description="Authenticate user with email and password. Returns JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            401: {'description': 'Invalid credentials'},
            403: {'description': 'Account locked'},
        },
        tags=['Authentication']
    )
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
    
    @extend_schema(
        summary="User Logout",
        description="Logout user by blacklisting the refresh token.",
        request=LogoutSerializer,
        responses={
            200: {'description': 'Logged out successfully'},
            400: {'description': 'Invalid token'},
        },
        tags=['Authentication']
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
    
    @extend_schema(
        summary="Password Reset",
        description="Initiate password reset process. Sends reset email to user.",
        request=PasswordResetRequestSerializer,
        responses={
            200: {'description': 'Password reset email sent'},
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='password-reset')
    def password_reset(self, request):
        """Initiate password reset process. Sends reset email to user."""
        # This will be implemented in Phase 3 with email integration
        return Response({
            'message': 'Password reset functionality will be available in Phase 3.'
        })


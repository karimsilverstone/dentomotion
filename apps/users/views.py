from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User, ActivityLog, ParentStudentLink
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, ActivityLogSerializer,
    LoginSerializer, LoginResponseSerializer, LogoutSerializer,
    PasswordResetRequestSerializer, ParentStudentLinkSerializer,
    UserProfileSerializer
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
        List users with optional role and centre filtering.
        
        **Filter by Role (2 options):**
        
        1. **Single role** - Use `role` parameter:
           - `?role=TEACHER` - Get only teachers
           - `?role=STUDENT` - Get only students
        
        2. **Multiple roles** - Use `roles` parameter:
           - `?roles=TEACHER,STUDENT` - Get teachers and students
           - `?roles=TEACHER,STUDENT,PARENT` - Get multiple roles
        
        **Filter by Centre:**
        - `?centre=1` - Get users in centre with ID 1
        - `?centre=2` - Get users in centre with ID 2
        
        **Combine Filters:**
        - `?role=TEACHER&centre=1` - Teachers in centre 1
        - `?roles=TEACHER,STUDENT&centre=1` - Teachers and students in centre 1
        - `?centre=1&page=2` - Users in centre 1, page 2
        
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
        - `/api/users/?centre=1` - Users in centre 1
        - `/api/users/?role=TEACHER&centre=1` - Teachers in centre 1
        - `/api/users/?roles=TEACHER,STUDENT&centre=2&page_size=50` - Teachers and students in centre 2
        
        **Notes:**
        - If both `role` and `roles` are provided, `roles` takes priority
        - Centre filter applies on top of permission-based filtering
        - Super Admins can filter any centre, Centre Managers are limited to their centre
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
            OpenApiParameter(
                name='centre',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by centre ID (e.g., 1, 2, 3)',
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
        
        # Apply centre filtering if provided
        centre_param = self.request.query_params.get('centre', None)
        if centre_param:
            # Filter by centre ID
            # Example: ?centre=1
            try:
                centre_id = int(centre_param)
                queryset = queryset.filter(centre_id=centre_id)
            except ValueError:
                # Invalid centre ID, return empty queryset
                queryset = queryset.none()
        
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
    
    def destroy(self, request, *args, **kwargs):
        """Delete a user (Super Admin only)"""
        if request.user.role != 'SUPER_ADMIN':
            return Response(
                {'error': 'Only Super Admin can delete users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Check if user has related data
        from apps.classes.models import TeacherAssignment, Enrolment
        from apps.homework.models import Homework, Submission
        
        issues = []
        
        # Check teacher assignments
        if user.role == 'TEACHER':
            assignments = TeacherAssignment.objects.filter(teacher=user).count()
            if assignments > 0:
                issues.append(f'{assignments} class assignment(s)')
            
            homework_count = Homework.objects.filter(teacher=user).count()
            if homework_count > 0:
                issues.append(f'{homework_count} homework assignment(s)')
        
        # Check student enrolments
        if user.role == 'STUDENT':
            enrolments = Enrolment.objects.filter(student=user).count()
            if enrolments > 0:
                issues.append(f'{enrolments} class enrolment(s)')
            
            submissions = Submission.objects.filter(student=user).count()
            if submissions > 0:
                issues.append(f'{submissions} homework submission(s)')
        
        # Check parent links
        if user.role == 'PARENT':
            try:
                parent_links = ParentStudentLink.objects.filter(parent=user).count()
                if parent_links > 0:
                    issues.append(f'{parent_links} student link(s)')
            except Exception:
                pass  # Table might not exist yet
        
        # Check if user is managing a centre
        if user.role == 'CENTRE_MANAGER':
            if user.centre:
                issues.append(f'Managing centre: {user.centre.name}')
            
            # Check CentreManagerAssignment if exists
            try:
                from apps.centres.models import CentreManagerAssignment
                manager_assignments = CentreManagerAssignment.objects.filter(manager=user).count()
                if manager_assignments > 0:
                    issues.append(f'{manager_assignments} centre assignment(s)')
            except Exception:
                pass
        
        # Check if user has a centre assigned (will cause PROTECT error)
        if user.centre is not None:
            # Need to remove centre assignment first
            issues.append(f'Assigned to centre: {user.centre.name} (must be removed first)')
        
        if issues:
            return Response(
                {
                    'error': f'Cannot delete user. User has associated data.',
                    'detail': 'Please remove the following before deleting:',
                    'issues': issues,
                    'suggestion': 'First update user to remove centre assignment: PATCH /api/users/{id}/ {"centre": null}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            
            return Response(
                {
                    'error': 'Failed to delete user.',
                    'detail': str(e),
                    'technical_details': error_details if request.user.role == 'SUPER_ADMIN' else 'Contact administrator'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Get Current User Profile",
        description="""
        Get the profile and information of the currently authenticated user.
        
        Returns complete user information including:
        - Personal details (name, email, phone)
        - Role and permissions
        - Centre information
        - Account status
        - Last login timestamp
        
        **Use this endpoint to:**
        - Display user profile in the app
        - Check current user's role and permissions
        - Get user's centre information
        - Show account details in settings
        
        **Example Response:**
        ```json
        {
          "id": 10,
          "email": "john.doe@example.com",
          "first_name": "John",
          "last_name": "Doe",
          "phone_number": "+1234567890",
          "role": "TEACHER",
          "centre": {
            "id": 1,
            "name": "Downtown Centre",
            "location": "123 Main St"
          },
          "is_active": true,
          "last_login": "2024-01-15T10:30:00Z",
          "date_joined": "2024-01-01T00:00:00Z"
        }
        ```
        """,
        tags=['Users'],
        responses={
            200: UserSerializer,
            401: {'description': 'Unauthorized - Invalid or missing token'}
        }
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
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
    
    @extend_schema(
        summary="Get User Complete Profile",
        description="Get complete profile of a user by ID including relationships",
        responses={200: UserProfileSerializer},
        tags=['Users']
    )
    @action(detail=True, methods=['get'], url_path='profile')
    def profile(self, request, pk=None):
        """Get complete user profile by ID"""
        user = self.get_object()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List Parent-Student Links", tags=['Users']),
    create=extend_schema(summary="Link Parent to Student", tags=['Users']),
    retrieve=extend_schema(summary="Get Link Details", tags=['Users']),
    destroy=extend_schema(summary="Remove Parent-Student Link", tags=['Users']),
)
class ParentStudentLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing parent-student links
    Allows assigning parents to students
    """
    queryset = ParentStudentLink.objects.all()
    serializer_class = ParentStudentLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  # No PUT/PATCH
    
    def get_queryset(self):
        """Filter links based on user role"""
        user = self.request.user
        
        # Super Admin sees all links
        if user.role == 'SUPER_ADMIN':
            return ParentStudentLink.objects.all().select_related('parent', 'student')
        
        # Centre Manager sees links in their centre
        elif user.role == 'CENTRE_MANAGER':
            return ParentStudentLink.objects.filter(
                parent__centre=user.centre
            ).select_related('parent', 'student')
        
        # Parents see their own links
        elif user.role == 'PARENT':
            return ParentStudentLink.objects.filter(parent=user).select_related('student')
        
        # Students see their parent links
        elif user.role == 'STUDENT':
            return ParentStudentLink.objects.filter(student=user).select_related('parent')
        
        return ParentStudentLink.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create parent-student link (Super Admin or Centre Manager only)"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'Only Super Admin and Centre Managers can link parents to students.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Remove parent-student link (Super Admin or Centre Manager only)"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'Only Super Admin and Centre Managers can remove links.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


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


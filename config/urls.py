"""
URL configuration for School Portal project
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.users.views import UserViewSet, AuthViewSet
from apps.centres.views import CentreViewSet, HolidayViewSet, TermDateViewSet
from apps.classes.views import ClassViewSet
from apps.homework.views import HomeworkViewSet, SubmissionViewSet
from apps.calendar.views import EventViewSet
from apps.whiteboard.views import WhiteboardSessionViewSet

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="School Portal API",
        default_version='v1',
        description="""
# School Portal API Documentation

A comprehensive multi-centre school management system with role-based access control.

## Authentication

This API uses JWT (JSON Web Token) authentication. To authenticate:

1. Obtain tokens by calling `/api/auth/login/` with email and password
2. Use the access token in the Authorization header: `Bearer <access_token>`
3. Refresh tokens when they expire using `/api/auth/refresh/`

## User Roles

- **SUPER_ADMIN**: Full system access across all centres
- **CENTRE_MANAGER**: Manage one centre (classes, teachers, students)
- **TEACHER**: Access assigned classes only (homework, grading, whiteboard)
- **STUDENT**: Access own homework, classes, and events
- **PARENT**: View linked students' information

## Multi-Centre Support

The system supports multiple centres with full data isolation. Users (except Super Admin) 
only have access to data from their assigned centre.

## Features

### Phase 1: Core Features
- User management and authentication
- Centre management with holidays and term dates
- Class management with teacher assignments
- Homework creation, submission, and grading
- Calendar and event management

### Phase 2: Enhanced Features
- Real-time whiteboard collaboration (WebSocket)
- Role-specific dashboards
- Parent-student linking
- Student profiles with privacy protection

### Phase 3: Advanced Features
- Analytics and reporting
- Email notifications
- Background task processing
- SMS integration (optional)

## Rate Limiting

- Anonymous requests: 100 per hour
- Authenticated requests: 1000 per hour

## Pagination

List endpoints return paginated results (20 items per page by default).
Use `?page=2` to navigate pages.

## File Uploads

Maximum file size: 10MB
Supported formats: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, ZIP
        """,
        terms_of_service="",
        contact=openapi.Contact(email="support@schoolportal.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# Create router for API endpoints
router = DefaultRouter()

# Register viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'centres', CentreViewSet, basename='centre')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'terms', TermDateViewSet, basename='termdate')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'homework', HomeworkViewSet, basename='homework')
router.register(r'submissions', SubmissionViewSet, basename='submission')
router.register(r'events', EventViewSet, basename='event')
router.register(r'whiteboard/sessions', WhiteboardSessionViewSet, basename='whiteboard-session')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Swagger/OpenAPI Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api-docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication
    path('api/auth/', include([
        path('login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
        path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
        path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
        path('password-reset/', AuthViewSet.as_view({'post': 'password_reset'}), name='password-reset'),
    ])),
    
    # Dashboards
    path('api/dashboard/', include([
        path('teacher/', __import__('apps.core.dashboards', fromlist=['TeacherDashboardView']).TeacherDashboardView.as_view(), name='teacher-dashboard'),
        path('student/', __import__('apps.core.dashboards', fromlist=['StudentDashboardView']).StudentDashboardView.as_view(), name='student-dashboard'),
        path('manager/', __import__('apps.core.dashboards', fromlist=['ManagerDashboardView']).ManagerDashboardView.as_view(), name='manager-dashboard'),
        path('parent/', __import__('apps.core.dashboards', fromlist=['ParentDashboardView']).ParentDashboardView.as_view(), name='parent-dashboard'),
    ])),
    
    # Analytics (Phase 3)
    path('api/analytics/', include([
        path('homework-trends/', __import__('apps.core.analytics', fromlist=['HomeworkTrendsView']).HomeworkTrendsView.as_view(), name='homework-trends'),
        path('student-performance/', __import__('apps.core.analytics', fromlist=['StudentPerformanceView']).StudentPerformanceView.as_view(), name='student-performance'),
        path('centre-overview/', __import__('apps.core.analytics', fromlist=['CentreOverviewView']).CentreOverviewView.as_view(), name='centre-overview'),
        path('teacher-performance/', __import__('apps.core.analytics', fromlist=['TeacherPerformanceView']).TeacherPerformanceView.as_view(), name='teacher-performance'),
    ])),
    
    # Health check endpoint
    path('api/health/', lambda request: __import__('django.http').JsonResponse({'status': 'ok'})),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

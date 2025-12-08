"""
URL configuration for School Portal project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.users.views import UserViewSet, AuthViewSet, ParentStudentLinkViewSet
from apps.centres.views import CentreViewSet, HolidayViewSet, TermDateViewSet
from apps.classes.views import ClassViewSet
from apps.homework.views import HomeworkViewSet, SubmissionViewSet
from apps.calendar.views import EventViewSet
from apps.whiteboard.views import WhiteboardSessionViewSet

# Create router for API endpoints
router = DefaultRouter()

# Register viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'parent-student-links', ParentStudentLinkViewSet, basename='parent-student-link')
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
    
    # OpenAPI 3.0 Documentation (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api-docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),
    
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
        path('admin/', __import__('apps.core.dashboards', fromlist=['SuperAdminDashboardView']).SuperAdminDashboardView.as_view(), name='admin-dashboard'),
    ])),
    
    # Analytics (Phase 3)
    path('api/analytics/', include([
        path('homework-trends/', __import__('apps.core.analytics', fromlist=['HomeworkTrendsView']).HomeworkTrendsView.as_view(), name='homework-trends'),
        path('student-performance/', __import__('apps.core.analytics', fromlist=['StudentPerformanceView']).StudentPerformanceView.as_view(), name='student-performance'),
        path('centre-overview/', __import__('apps.core.analytics', fromlist=['CentreOverviewView']).CentreOverviewView.as_view(), name='centre-overview'),
        path('teacher-performance/', __import__('apps.core.analytics', fromlist=['TeacherPerformanceView']).TeacherPerformanceView.as_view(), name='teacher-performance'),
    ])),
    
    # Health check endpoint
    path('api/health/', lambda request: JsonResponse({'status': 'ok'})),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer


@extend_schema_view(
    list=extend_schema(summary="List Events", tags=['Calendar']),
    create=extend_schema(summary="Create Event", tags=['Calendar']),
    retrieve=extend_schema(summary="Get Event Details", tags=['Calendar']),
    update=extend_schema(summary="Update Event", tags=['Calendar']),
    partial_update=extend_schema(summary="Partial Update Event", tags=['Calendar']),
    destroy=extend_schema(summary="Delete Event", tags=['Calendar']),
)
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event management with visibility rules
    - Students: See events from their centre + class events for enrolled classes
    - Teachers: See events from their centre + class events for assigned classes
    - Managers: See all events for their centre
    - Super Admin: See all events
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super Admin sees all events
        if user.role == 'SUPER_ADMIN':
            return Event.objects.all().select_related(
                'centre', 'class_instance', 'created_by'
            )
        
        # Centre Manager sees all events in their centre
        if user.role == 'CENTRE_MANAGER' and user.centre:
            return Event.objects.filter(
                centre=user.centre
            ).select_related('centre', 'class_instance', 'created_by')
        
        # Teachers see centre events + class events for their classes
        if user.role == 'TEACHER' and user.centre:
            from django.db.models import Q
            return Event.objects.filter(
                Q(centre=user.centre, event_type='CENTRE_EVENT') |
                Q(class_instance__teacher_assignments__teacher=user, event_type='CLASS_EVENT')
            ).distinct().select_related('centre', 'class_instance', 'created_by')
        
        # Students see centre events + class events for enrolled classes
        if user.role == 'STUDENT' and user.centre:
            from django.db.models import Q
            return Event.objects.filter(
                Q(centre=user.centre, event_type='CENTRE_EVENT') |
                Q(
                    class_instance__enrolments__student=user,
                    class_instance__enrolments__is_active=True,
                    event_type='CLASS_EVENT'
                )
            ).distinct().select_related('centre', 'class_instance', 'created_by')
        
        return Event.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EventCreateSerializer
        return EventSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Teachers can create class events for their classes
        Managers can create centre and class events for their centre
        Super Admin can create any event
        """
        user = request.user
        event_type = request.data.get('event_type')
        
        if user.role == 'STUDENT' or user.role == 'PARENT':
            return Response(
                {'error': 'Students and parents cannot create events.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Teachers can only create class events for their classes
        if user.role == 'TEACHER':
            if event_type != 'CLASS_EVENT':
                return Response(
                    {'error': 'Teachers can only create class events.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            class_id = request.data.get('class_instance')
            if not class_id:
                return Response(
                    {'error': 'Class is required for class events.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from apps.classes.models import TeacherAssignment
            if not TeacherAssignment.objects.filter(
                teacher=user, class_instance_id=class_id
            ).exists():
                return Response(
                    {'error': 'You can only create events for classes you teach.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Centre Manager can only create events in their centre
        if user.role == 'CENTRE_MANAGER':
            centre_id = request.data.get('centre')
            if centre_id != user.centre.id:
                return Response(
                    {'error': 'You can only create events for your own centre.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only the creator or managers/admins can update events"""
        event = self.get_object()
        user = request.user
        
        if user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            if event.created_by != user:
                return Response(
                    {'error': 'You can only update your own events.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only the creator or managers/admins can delete events"""
        event = self.get_object()
        user = request.user
        
        if user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            if event.created_by != user:
                return Response(
                    {'error': 'You can only delete your own events.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='calendar')
    def calendar_view(self, request):
        """
        Get events for calendar view
        Query params: view_type (month/week/list), start_date, end_date
        """
        view_type = request.query_params.get('view_type', 'month')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        # Filter by date range
        if start_date and end_date:
            queryset = queryset.filter(
                event_date__gte=start_date,
                event_date__lte=end_date
            )
        elif view_type == 'month':
            # Default to current month
            today = timezone.now()
            start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end = today.replace(month=today.month + 1, day=1)
            queryset = queryset.filter(event_date__gte=start, event_date__lt=end)
        
        elif view_type == 'week':
            # Default to current week
            today = timezone.now()
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
            queryset = queryset.filter(event_date__gte=start, event_date__lt=end)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        """Get upcoming events (next 30 days)"""
        today = timezone.now()
        end_date = today + timedelta(days=30)
        
        queryset = self.get_queryset().filter(
            event_date__gte=today,
            event_date__lte=end_date
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


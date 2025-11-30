from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import WhiteboardSession, WhiteboardSnapshot
from .serializers import (
    WhiteboardSessionSerializer, WhiteboardSessionCreateSerializer,
    WhiteboardSnapshotSerializer
)


@extend_schema_view(
    list=extend_schema(summary="List Whiteboard Sessions", tags=['Whiteboard']),
    create=extend_schema(summary="Create Whiteboard Session", tags=['Whiteboard']),
    retrieve=extend_schema(summary="Get Whiteboard Session Details", tags=['Whiteboard']),
    update=extend_schema(summary="Update Whiteboard Session", tags=['Whiteboard']),
    partial_update=extend_schema(summary="Partial Update Whiteboard Session", tags=['Whiteboard']),
    destroy=extend_schema(summary="Delete Whiteboard Session", tags=['Whiteboard']),
)
class WhiteboardSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Whiteboard Sessions
    Teachers can create and control sessions for their classes
    Students can join sessions for enrolled classes
    """
    queryset = WhiteboardSession.objects.all()
    serializer_class = WhiteboardSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super Admin sees all sessions
        if user.role == 'SUPER_ADMIN':
            return WhiteboardSession.objects.all().select_related(
                'class_instance', 'teacher'
            ).prefetch_related('snapshots')
        
        # Centre Manager sees all sessions in their centre
        if user.role == 'CENTRE_MANAGER' and user.centre:
            return WhiteboardSession.objects.filter(
                class_instance__centre=user.centre
            ).select_related('class_instance', 'teacher').prefetch_related('snapshots')
        
        # Teachers see sessions for their classes
        if user.role == 'TEACHER':
            return WhiteboardSession.objects.filter(
                class_instance__teacher_assignments__teacher=user
            ).select_related('class_instance', 'teacher').prefetch_related('snapshots')
        
        # Students see sessions for enrolled classes
        if user.role == 'STUDENT':
            return WhiteboardSession.objects.filter(
                class_instance__enrolments__student=user,
                class_instance__enrolments__is_active=True
            ).select_related('class_instance', 'teacher')
        
        return WhiteboardSession.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WhiteboardSessionCreateSerializer
        return WhiteboardSessionSerializer
    
    def create(self, request, *args, **kwargs):
        """Only teachers can create whiteboard sessions"""
        if request.user.role != 'TEACHER':
            return Response(
                {'error': 'Only teachers can create whiteboard sessions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify teacher is assigned to the class
        class_instance = serializer.validated_data['class_instance']
        if not class_instance.teacher_assignments.filter(teacher=request.user).exists():
            return Response(
                {'error': 'You can only create sessions for classes you teach.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if there's already an active session for this class
        active_session = WhiteboardSession.objects.filter(
            class_instance=class_instance,
            is_active=True
        ).first()
        
        if active_session:
            return Response(
                {'error': 'There is already an active session for this class.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='end')
    def end_session(self, request, pk=None):
        """End a whiteboard session (teacher only)"""
        session = self.get_object()
        
        if request.user.role != 'TEACHER' or session.teacher != request.user:
            return Response(
                {'error': 'Only the teacher who created the session can end it.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not session.is_active:
            return Response(
                {'error': 'Session is already ended.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.end_session()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='join')
    def join_session(self, request, pk=None):
        """Join a whiteboard session (students and teachers)"""
        session = self.get_object()
        
        if not session.is_active:
            return Response(
                {'error': 'This session is not active.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user has access to this class
        class_instance = session.class_instance
        
        if request.user.role == 'TEACHER':
            if not class_instance.teacher_assignments.filter(teacher=request.user).exists():
                return Response(
                    {'error': 'You do not have access to this class.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif request.user.role == 'STUDENT':
            if not class_instance.enrolments.filter(
                student=request.user, is_active=True
            ).exists():
                return Response(
                    {'error': 'You are not enrolled in this class.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        else:
            return Response(
                {'error': 'Only teachers and students can join sessions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return session details for joining
        serializer = self.get_serializer(session)
        return Response({
            'message': 'Successfully joined session',
            'session': serializer.data,
            'websocket_url': f'/ws/whiteboard/{session.id}/'
        })
    
    @action(detail=True, methods=['get', 'post'], url_path='snapshots')
    def snapshots(self, request, pk=None):
        """Manage snapshots for a session"""
        session = self.get_object()
        
        if request.method == 'GET':
            snapshots = WhiteboardSnapshot.objects.filter(session=session)
            serializer = WhiteboardSnapshotSerializer(snapshots, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Only teachers can save snapshots
            if request.user.role != 'TEACHER':
                return Response(
                    {'error': 'Only teachers can save snapshots.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = WhiteboardSnapshotSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(session=session, saved_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_sessions(self, request):
        """Get currently active sessions for user"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


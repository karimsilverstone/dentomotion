from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Homework, Submission
from .serializers import (
    HomeworkSerializer, HomeworkCreateSerializer, HomeworkUpdateSerializer,
    SubmissionSerializer, SubmissionCreateSerializer, SubmissionGradeSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List Homework",
        tags=['Homework'],
        description="""
        List homework with optional filtering.
        
        **Filters:**
        - `class_instance` - Filter by class ID
        - `teacher` - Filter by teacher ID
        - `overdue` - Show only overdue homework (true/false)
        - `due_date_from` - Homework due after this date (YYYY-MM-DD)
        - `due_date_to` - Homework due before this date (YYYY-MM-DD)
        - `search` - Search by title
        
        **Examples:**
        - `/api/homework/` - All accessible homework
        - `/api/homework/?class_instance=5` - Homework for class 5
        - `/api/homework/?overdue=true` - Only overdue homework
        - `/api/homework/?due_date_from=2024-01-01&due_date_to=2024-12-31` - Homework in date range
        - `/api/homework/?search=algebra` - Search for "algebra"
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
                name='class_instance',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by class ID',
                required=False
            ),
            OpenApiParameter(
                name='teacher',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by teacher ID',
                required=False
            ),
            OpenApiParameter(
                name='overdue',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Show only overdue homework',
                required=False
            ),
            OpenApiParameter(
                name='due_date_from',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Homework due after this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='due_date_to',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Homework due before this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search by homework title',
                required=False
            ),
        ]
    ),
    create=extend_schema(summary="Create Homework", tags=['Homework']),
    retrieve=extend_schema(summary="Get Homework Details", tags=['Homework']),
    update=extend_schema(summary="Update Homework", tags=['Homework']),
    partial_update=extend_schema(summary="Partial Update Homework", tags=['Homework']),
    destroy=extend_schema(summary="Delete Homework", tags=['Homework']),
)
class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Homework management
    Teachers: Create, update, delete for their classes
    Students: View homework for enrolled classes
    Managers: View all homework in their centre
    """
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset based on user role
        if user.role == 'SUPER_ADMIN':
            queryset = Homework.objects.all().select_related(
                'class_instance', 'teacher'
            ).prefetch_related('submissions')
        elif user.role == 'CENTRE_MANAGER' and user.centre:
            queryset = Homework.objects.filter(
                class_instance__centre=user.centre
            ).select_related('class_instance', 'teacher').prefetch_related('submissions')
        elif user.role == 'TEACHER':
            queryset = Homework.objects.filter(
                class_instance__teacher_assignments__teacher=user
            ).select_related('class_instance', 'teacher').prefetch_related('submissions')
        elif user.role == 'STUDENT':
            queryset = Homework.objects.filter(
                class_instance__enrolments__student=user,
                class_instance__enrolments__is_active=True
            ).select_related('class_instance', 'teacher')
        else:
            queryset = Homework.objects.none()
        
        # Apply filters
        from django.utils import timezone
        
        # Filter by class
        class_param = self.request.query_params.get('class_instance', None)
        if class_param:
            try:
                queryset = queryset.filter(class_instance_id=int(class_param))
            except ValueError:
                queryset = queryset.none()
        
        # Filter by teacher
        teacher_param = self.request.query_params.get('teacher', None)
        if teacher_param:
            try:
                queryset = queryset.filter(teacher_id=int(teacher_param))
            except ValueError:
                queryset = queryset.none()
        
        # Filter by overdue
        overdue_param = self.request.query_params.get('overdue', None)
        if overdue_param and overdue_param.lower() in ['true', '1']:
            queryset = queryset.filter(due_date__lt=timezone.now())
        
        # Filter by due date range
        due_date_from = self.request.query_params.get('due_date_from', None)
        if due_date_from:
            queryset = queryset.filter(due_date__gte=due_date_from)
        
        due_date_to = self.request.query_params.get('due_date_to', None)
        if due_date_to:
            queryset = queryset.filter(due_date__lte=due_date_to)
        
        # Search by title
        search_param = self.request.query_params.get('search', None)
        if search_param:
            queryset = queryset.filter(title__icontains=search_param)
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return HomeworkCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HomeworkUpdateSerializer
        return HomeworkSerializer
    
    def create(self, request, *args, **kwargs):
        """Only teachers can create homework"""
        if request.user.role != 'TEACHER':
            return Response(
                {'error': 'Only teachers can create homework.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify teacher is assigned to the class
        class_instance = serializer.validated_data['class_instance']
        if not class_instance.teacher_assignments.filter(teacher=request.user).exists():
            return Response(
                {'error': 'You can only create homework for classes you teach.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only the teacher who created it can update homework"""
        homework = self.get_object()
        if request.user.role != 'TEACHER' or homework.teacher != request.user:
            return Response(
                {'error': 'You can only update your own homework.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only the teacher who created it can delete homework"""
        homework = self.get_object()
        if request.user.role != 'TEACHER' or homework.teacher != request.user:
            return Response(
                {'error': 'You can only delete your own homework.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'], url_path='submissions')
    def submissions(self, request, pk=None):
        """Get all submissions for a homework (teachers and managers only)"""
        if request.user.role not in ['TEACHER', 'CENTRE_MANAGER', 'SUPER_ADMIN']:
            return Response(
                {'error': 'You do not have permission to view submissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework = self.get_object()
        submissions = Submission.objects.filter(homework=homework).select_related('student')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit homework (students only)"""
        if request.user.role != 'STUDENT':
            return Response(
                {'error': 'Only students can submit homework.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework = self.get_object()
        
        # Check if student is enrolled in the class
        if not homework.class_instance.enrolments.filter(
            student=request.user, is_active=True
        ).exists():
            return Response(
                {'error': 'You are not enrolled in this class.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already submitted
        existing_submission = Submission.objects.filter(
            homework=homework, student=request.user
        ).first()
        
        if existing_submission and existing_submission.status in ['SUBMITTED', 'GRADED']:
            return Response(
                {'error': 'You have already submitted this homework.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update submission
        serializer = SubmissionCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        if existing_submission:
            existing_submission.file = serializer.validated_data.get('file')
            existing_submission.status = 'SUBMITTED'
            existing_submission.submitted_at = timezone.now()
            existing_submission.save()
            return Response(SubmissionSerializer(existing_submission).data)
        else:
            submission = serializer.save(
                student=request.user,
                status='SUBMITTED',
                submitted_at=timezone.now()
            )
            return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='grade/(?P<submission_id>[^/.]+)')
    def grade(self, request, pk=None, submission_id=None):
        """Grade a submission (teachers only)"""
        if request.user.role != 'TEACHER':
            return Response(
                {'error': 'Only teachers can grade submissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        homework = self.get_object()
        
        # Verify teacher is assigned to the class
        if not homework.class_instance.teacher_assignments.filter(teacher=request.user).exists():
            return Response(
                {'error': 'You can only grade homework for classes you teach.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            submission = Submission.objects.get(id=submission_id, homework=homework)
        except Submission.DoesNotExist:
            return Response(
                {'error': 'Submission not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubmissionGradeSerializer(submission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            status='GRADED',
            graded_at=timezone.now(),
            graded_by=request.user
        )
        
        return Response(SubmissionSerializer(submission).data)


@extend_schema_view(
    list=extend_schema(
        summary="List Submissions",
        tags=['Homework'],
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
        ]
    ),
    retrieve=extend_schema(summary="Get Submission Details", tags=['Homework']),
)
class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing submissions
    Students: View their own submissions
    Teachers: View submissions for their classes
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'SUPER_ADMIN':
            return Submission.objects.all().select_related('homework', 'student', 'graded_by')
        
        if user.role == 'CENTRE_MANAGER' and user.centre:
            return Submission.objects.filter(
                homework__class_instance__centre=user.centre
            ).select_related('homework', 'student', 'graded_by')
        
        if user.role == 'TEACHER':
            return Submission.objects.filter(
                homework__class_instance__teacher_assignments__teacher=user
            ).select_related('homework', 'student', 'graded_by')
        
        if user.role == 'STUDENT':
            return Submission.objects.filter(student=user).select_related('homework', 'graded_by')
        
        return Submission.objects.none()


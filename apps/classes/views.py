from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Class, TeacherAssignment, Enrolment
from .serializers import (
    ClassSerializer, ClassCreateSerializer,
    TeacherAssignmentSerializer, EnrolmentSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List Classes",
        tags=['Classes'],
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
    create=extend_schema(
        summary="Create Class",
        tags=['Classes'],
        description="""
        Create a new class with optional teachers and students.
        
        **Optional Fields:**
        - `teacher_ids`: Array of teacher IDs to assign (max 3 per teacher)
        - `student_ids`: Array of student IDs to enroll
        
        **Example:**
        ```json
        {
          "centre": 1,
          "name": "Math 101",
          "level_or_age_group": "Grade 5",
          "teacher_ids": [10, 11],
          "student_ids": [20, 21, 22]
        }
        ```
        
        **Notes:**
        - Teachers and students are optional
        - Teachers must have role='TEACHER'
        - Students must have role='STUDENT'
        - Students must be in the same centre as the class
        - Teachers can be assigned to max 3 classes
        """
    ),
    retrieve=extend_schema(summary="Get Class Details", tags=['Classes']),
    update=extend_schema(summary="Update Class", tags=['Classes']),
    partial_update=extend_schema(summary="Partial Update Class", tags=['Classes']),
    destroy=extend_schema(summary="Delete Class", tags=['Classes']),
)
class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Class model with centre-based filtering
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super Admin sees all classes
        if user.role == 'SUPER_ADMIN':
            return Class.objects.all().select_related('centre').prefetch_related(
                'teacher_assignments__teacher', 'enrolments__student'
            )
        
        # Centre Manager and Teachers see classes in their centre
        if user.role in ['CENTRE_MANAGER', 'TEACHER'] and user.centre:
            queryset = Class.objects.filter(centre=user.centre).select_related('centre')
            
            # Teachers only see their assigned classes
            if user.role == 'TEACHER':
                queryset = queryset.filter(teacher_assignments__teacher=user)
            
            return queryset.prefetch_related('teacher_assignments__teacher', 'enrolments__student')
        
        # Students see classes they're enrolled in
        if user.role == 'STUDENT':
            return Class.objects.filter(
                enrolments__student=user,
                enrolments__is_active=True
            ).select_related('centre').prefetch_related('teacher_assignments__teacher')
        
        return Class.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClassCreateSerializer
        return ClassSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new class with optional teachers and students"""
        # Validate permissions first
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to create classes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Centre Manager can only create classes in their centre
        if request.user.role == 'CENTRE_MANAGER':
            if request.data.get('centre') != request.user.centre.id:
                return Response(
                    {'error': 'You can only create classes in your own centre.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Use the create serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_instance = serializer.save()
        
        # Return the full class details using ClassSerializer
        output_serializer = ClassSerializer(class_instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def create(self, request, *args, **kwargs):
        """Only Super Admin and Centre Managers can create classes"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to create classes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Centre Manager can only create classes in their centre
        if request.user.role == 'CENTRE_MANAGER':
            if request.data.get('centre') != request.user.centre.id:
                return Response(
                    {'error': 'You can only create classes in your own centre.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['get', 'post'], url_path='teachers')
    def teachers(self, request, pk=None):
        """Manage teachers for a class"""
        class_instance = self.get_object()
        
        if request.method == 'GET':
            assignments = TeacherAssignment.objects.filter(class_instance=class_instance)
            serializer = TeacherAssignmentSerializer(assignments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Only Super Admin and Centre Managers can assign teachers
            if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
                return Response(
                    {'error': 'You do not have permission to assign teachers.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = TeacherAssignmentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(class_instance=class_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='teachers/(?P<teacher_id>[^/.]+)')
    def remove_teacher(self, request, pk=None, teacher_id=None):
        """Remove a teacher from a class"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to remove teachers.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        class_instance = self.get_object()
        try:
            assignment = TeacherAssignment.objects.get(
                class_instance=class_instance,
                teacher_id=teacher_id
            )
            assignment.delete()
            return Response({'message': 'Teacher removed from class.'})
        except TeacherAssignment.DoesNotExist:
            return Response(
                {'error': 'Teacher assignment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get', 'post'], url_path='enrolments')
    def enrolments(self, request, pk=None):
        """Manage student enrolments for a class"""
        class_instance = self.get_object()
        
        if request.method == 'GET':
            enrolments = Enrolment.objects.filter(
                class_instance=class_instance,
                is_active=True
            )
            serializer = EnrolmentSerializer(enrolments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Only Super Admin and Centre Managers can enrol students
            if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
                return Response(
                    {'error': 'You do not have permission to enrol students.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = EnrolmentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(class_instance=class_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='enrolments/(?P<student_id>[^/.]+)')
    def remove_student(self, request, pk=None, student_id=None):
        """Remove a student from a class (set inactive)"""
        if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            return Response(
                {'error': 'You do not have permission to remove students.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        class_instance = self.get_object()
        try:
            enrolment = Enrolment.objects.get(
                class_instance=class_instance,
                student_id=student_id
            )
            enrolment.is_active = False
            enrolment.save()
            return Response({'message': 'Student removed from class.'})
        except Enrolment.DoesNotExist:
            return Response(
                {'error': 'Enrolment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


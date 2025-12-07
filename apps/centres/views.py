from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Centre, Holiday, TermDate
from .serializers import (
    CentreSerializer, CentreCreateSerializer, CentreUpdateSerializer,
    HolidaySerializer, TermDateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List Centres",
        tags=['Centres'],
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
        summary="Create Centre",
        tags=['Centres'],
        description="""
        Create a new centre with a designated Centre Manager.
        
        **Required Fields:**
        - `name` - Centre name
        - `country` - Country
        - `city` - City
        - `timezone` - Timezone (e.g., UTC, America/New_York)
        - `centre_manager_id` - User ID to assign as Centre Manager
        
        **Note:** The user specified in `centre_manager_id` will:
        - Be assigned the role CENTRE_MANAGER
        - Be assigned to this centre
        - Become the manager of this centre
        
        **To get available users for manager assignment:**
        ```
        GET /api/users/?role=TEACHER  # Or any non-admin user
        GET /api/users/?role=PARENT   # Any user who isn't already a manager
        ```
        
        **Example Request:**
        ```json
        {
          "name": "Downtown Centre",
          "country": "USA",
          "city": "New York",
          "timezone": "America/New_York",
          "centre_manager_id": 15
        }
        ```
        """
    ),
    retrieve=extend_schema(summary="Get Centre Details", tags=['Centres']),
    update=extend_schema(
        summary="Update Centre",
        tags=['Centres'],
        description="""
        Update a centre with optional manager change.
        
        **Updatable Fields:**
        - `name` - Centre name
        - `country` - Country
        - `city` - City
        - `timezone` - Timezone
        - `centre_manager_id` - New manager ID (optional)
        
        **Changing Centre Manager:**
        If you provide `centre_manager_id`:
        - The old manager will be demoted to TEACHER role
        - The old manager's centre assignment will be removed
        - The new user will become CENTRE_MANAGER
        - The new user will be assigned to this centre
        
        **Example: Update centre and change manager**
        ```json
        {
          "name": "Updated Centre Name",
          "country": "USA",
          "city": "Boston",
          "timezone": "America/New_York",
          "centre_manager_id": 20
        }
        ```
        
        **Example: Update centre without changing manager**
        ```json
        {
          "name": "Updated Centre Name",
          "city": "Los Angeles"
        }
        ```
        
        **Note:** Only Super Admin can update centres.
        """
    ),
    partial_update=extend_schema(
        summary="Partial Update Centre",
        tags=['Centres'],
        description="""
        Partially update a centre (only provided fields are updated).
        
        **Optional Fields:**
        - `name`
        - `country`
        - `city`
        - `timezone`
        - `centre_manager_id` - Change manager
        
        **Example: Only change manager**
        ```json
        {
          "centre_manager_id": 25
        }
        ```
        
        **Example: Only change name**
        ```json
        {
          "name": "New Centre Name"
        }
        ```
        """
    ),
    destroy=extend_schema(
        summary="Delete Centre",
        tags=['Centres'],
        description="""
        Delete a centre (Super Admin only).
        
        **Important:** A centre can only be deleted if:
        - It has no users associated with it
        - It has no classes associated with it
        
        **Before deleting a centre:**
        1. Reassign or delete all users in the centre
        2. Delete all classes in the centre
        3. Then delete the centre
        
        **Error Responses:**
        - 400: Centre has users or classes
        - 403: Not authorized (not Super Admin)
        - 404: Centre not found
        """,
        responses={
            204: {'description': 'Centre deleted successfully'},
            400: {
                'description': 'Cannot delete - centre has associated users or classes',
                'content': {
                    'application/json': {
                        'example': {
                            'error': 'Cannot delete centre. There are 15 user(s) associated with this centre.',
                            'detail': 'Please reassign or delete all users before deleting the centre.',
                            'users_count': 15
                        }
                    }
                }
            },
            403: {'description': 'Permission denied'},
            404: {'description': 'Centre not found'}
        }
    ),
)
class CentreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Centre model
    Super Admin: Full access
    Centre Manager: Read access to their centre only
    Others: Read access to their centre
    """
    queryset = Centre.objects.all()
    serializer_class = CentreSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super Admin sees all centres
        if user.role == 'SUPER_ADMIN':
            return Centre.objects.all()
        
        # Others see only their centre
        if user.centre:
            return Centre.objects.filter(id=user.centre.id)
        
        return Centre.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CentreCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CentreUpdateSerializer
        return CentreSerializer
    
    def create(self, request, *args, **kwargs):
        """Only Super Admin can create centres"""
        if request.user.role != 'SUPER_ADMIN':
            return Response(
                {'error': 'Only Super Admin can create centres.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only Super Admin can update centres"""
        if request.user.role != 'SUPER_ADMIN':
            return Response(
                {'error': 'Only Super Admin can update centres.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use the update serializer and return full centre details
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full centre details with manager info
        output_serializer = CentreSerializer(instance)
        return Response(output_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Only Super Admin can delete centres"""
        if request.user.role != 'SUPER_ADMIN':
            return Response(
                {'error': 'Only Super Admin can delete centres.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        centre = self.get_object()
        
        # Check if centre has users
        users_count = centre.users.count()
        if users_count > 0:
            return Response(
                {
                    'error': f'Cannot delete centre. There are {users_count} user(s) associated with this centre.',
                    'detail': 'Please reassign or delete all users before deleting the centre.',
                    'users_count': users_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if centre has classes
        classes_count = centre.classes.count()
        if classes_count > 0:
            return Response(
                {
                    'error': f'Cannot delete centre. There are {classes_count} class(es) associated with this centre.',
                    'detail': 'Please delete all classes before deleting the centre.',
                    'classes_count': classes_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to delete centre.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get', 'post'], url_path='holidays')
    def holidays(self, request, pk=None):
        """Manage holidays for a centre"""
        centre = self.get_object()
        
        if request.method == 'GET':
            holidays = Holiday.objects.filter(centre=centre)
            serializer = HolidaySerializer(holidays, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Only Super Admin and Centre Manager can add holidays
            if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
                return Response(
                    {'error': 'You do not have permission to add holidays.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = HolidaySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(centre=centre)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'], url_path='terms')
    def terms(self, request, pk=None):
        """Manage term dates for a centre"""
        centre = self.get_object()
        
        if request.method == 'GET':
            terms = TermDate.objects.filter(centre=centre)
            serializer = TermDateSerializer(terms, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Only Super Admin and Centre Manager can add terms
            if request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
                return Response(
                    {'error': 'You do not have permission to add term dates.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = TermDateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(centre=centre)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="List Holidays",
        tags=['Centres'],
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
    create=extend_schema(summary="Create Holiday", tags=['Centres']),
    retrieve=extend_schema(summary="Get Holiday Details", tags=['Centres']),
    update=extend_schema(summary="Update Holiday", tags=['Centres']),
    partial_update=extend_schema(summary="Partial Update Holiday", tags=['Centres']),
    destroy=extend_schema(summary="Delete Holiday", tags=['Centres']),
)
class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual holidays"""
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'SUPER_ADMIN':
            return Holiday.objects.all()
        
        if user.centre:
            return Holiday.objects.filter(centre=user.centre)
        
        return Holiday.objects.none()


@extend_schema_view(
    list=extend_schema(
        summary="List Term Dates",
        tags=['Centres'],
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
    create=extend_schema(summary="Create Term Date", tags=['Centres']),
    retrieve=extend_schema(summary="Get Term Date Details", tags=['Centres']),
    update=extend_schema(summary="Update Term Date", tags=['Centres']),
    partial_update=extend_schema(summary="Partial Update Term Date", tags=['Centres']),
    destroy=extend_schema(summary="Delete Term Date", tags=['Centres']),
)
class TermDateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual term dates"""
    queryset = TermDate.objects.all()
    serializer_class = TermDateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'SUPER_ADMIN':
            return TermDate.objects.all()
        
        if user.centre:
            return TermDate.objects.filter(centre=user.centre)
        
        return TermDate.objects.none()


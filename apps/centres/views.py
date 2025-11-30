from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Centre, Holiday, TermDate
from .serializers import (
    CentreSerializer, CentreCreateSerializer,
    HolidaySerializer, TermDateSerializer
)


@extend_schema_view(
    list=extend_schema(summary="List Centres", tags=['Centres']),
    create=extend_schema(summary="Create Centre", tags=['Centres']),
    retrieve=extend_schema(summary="Get Centre Details", tags=['Centres']),
    update=extend_schema(summary="Update Centre", tags=['Centres']),
    partial_update=extend_schema(summary="Partial Update Centre", tags=['Centres']),
    destroy=extend_schema(summary="Delete Centre", tags=['Centres']),
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
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Super Admin can delete centres"""
        if request.user.role != 'SUPER_ADMIN':
            return Response(
                {'error': 'Only Super Admin can delete centres.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
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
    list=extend_schema(summary="List Holidays", tags=['Centres']),
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
    list=extend_schema(summary="List Term Dates", tags=['Centres']),
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


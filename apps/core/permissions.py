from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission class for Super Admin only"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'


class IsCentreManager(permissions.BasePermission):
    """Permission class for Centre Manager"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CENTRE_MANAGER'


class IsTeacher(permissions.BasePermission):
    """Permission class for Teacher"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'TEACHER'


class IsStudent(permissions.BasePermission):
    """Permission class for Student"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'STUDENT'


class IsParent(permissions.BasePermission):
    """Permission class for Parent"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'PARENT'


class HasCentreAccess(permissions.BasePermission):
    """
    Permission class to ensure users only access data from their centre
    Super Admin has access to all centres
    """
    
    def has_object_permission(self, request, view, obj):
        # Super Admin has access to everything
        if request.user.role == 'SUPER_ADMIN':
            return True
        
        # Check if object has a centre attribute
        if hasattr(obj, 'centre'):
            return obj.centre == request.user.centre
        
        # Check if object is a centre itself
        if obj.__class__.__name__ == 'Centre':
            return obj == request.user.centre
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.created_by == request.user or obj.user == request.user


class IsTeacherOrManager(permissions.BasePermission):
    """Permission for Teacher or Centre Manager or Super Admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.role in ['TEACHER', 'CENTRE_MANAGER', 'SUPER_ADMIN']


class IsManagerOrAdmin(permissions.BasePermission):
    """Permission for Centre Manager or Super Admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.role in ['CENTRE_MANAGER', 'SUPER_ADMIN']


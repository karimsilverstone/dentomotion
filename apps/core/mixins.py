from django.db import models


class CentreFilterMixin:
    """
    Mixin to filter querysets by centre
    Automatically filters based on user's role and centre
    """
    
    def get_centre_filtered_queryset(self, queryset, user):
        """Filter queryset based on user's centre"""
        if user.role == 'SUPER_ADMIN':
            return queryset
        
        if user.centre:
            return queryset.filter(centre=user.centre)
        
        return queryset.none()


class TimestampMixin(models.Model):
    """
    Abstract model to add created_at and updated_at timestamps
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


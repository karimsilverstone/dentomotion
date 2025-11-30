from django.db import models
from django.utils import timezone


class Event(models.Model):
    """Event model for centre and class-based events"""
    
    EVENT_TYPE_CHOICES = [
        ('CENTRE_EVENT', 'Centre Event'),
        ('CLASS_EVENT', 'Class Event'),
        ('HOLIDAY', 'Holiday'),
    ]
    
    centre = models.ForeignKey(
        'centres.Centre',
        on_delete=models.CASCADE,
        related_name='events'
    )
    class_instance = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
        help_text='If set, this is a class-specific event'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['event_date']
        indexes = [
            models.Index(fields=['centre', 'event_date']),
            models.Index(fields=['class_instance', 'event_date']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        if self.class_instance:
            return f"{self.title} - {self.class_instance.name} ({self.event_date.date()})"
        return f"{self.title} - {self.centre.name} ({self.event_date.date()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Class events must have a class_instance
        if self.event_type == 'CLASS_EVENT' and not self.class_instance:
            raise ValidationError('Class events must have a class specified.')
        
        # Centre events should not have a class_instance
        if self.event_type == 'CENTRE_EVENT' and self.class_instance:
            raise ValidationError('Centre events should not have a class specified.')


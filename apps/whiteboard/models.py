from django.db import models
from django.utils import timezone


class WhiteboardSession(models.Model):
    """Whiteboard session model for real-time collaboration"""
    
    class_instance = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='whiteboard_sessions'
    )
    teacher = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='whiteboard_sessions'
    )
    session_name = models.CharField(max_length=200)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Whiteboard Session'
        verbose_name_plural = 'Whiteboard Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['class_instance', 'is_active']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        return f"{self.session_name} - {self.class_instance.name}"
    
    def end_session(self):
        """End the whiteboard session"""
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()


class WhiteboardSnapshot(models.Model):
    """Store whiteboard state snapshots"""
    
    session = models.ForeignKey(
        WhiteboardSession,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    snapshot_data = models.JSONField(help_text='Canvas state as JSON')
    saved_at = models.DateTimeField(default=timezone.now)
    saved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='saved_snapshots'
    )
    name = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Whiteboard Snapshot'
        verbose_name_plural = 'Whiteboard Snapshots'
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['session', 'saved_at']),
        ]
    
    def __str__(self):
        return f"Snapshot of {self.session.session_name} at {self.saved_at}"


from django.db import models
from django.utils import timezone as django_timezone
import pytz


class CentreManagerAssignment(models.Model):
    """Links centre managers to centres (many-to-many)"""
    
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='managed_centres',
        limit_choices_to={'role': 'CENTRE_MANAGER'}
    )
    centre = models.ForeignKey(
        'Centre',
        on_delete=models.CASCADE,
        related_name='manager_assignments'
    )
    assigned_at = models.DateTimeField(default=django_timezone.now)
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary centre for this manager'
    )
    
    class Meta:
        verbose_name = 'Centre Manager Assignment'
        verbose_name_plural = 'Centre Manager Assignments'
        unique_together = [['manager', 'centre']]
        indexes = [
            models.Index(fields=['manager']),
            models.Index(fields=['centre']),
        ]
    
    def __str__(self):
        return f"{self.manager.get_full_name()} → {self.centre.name}"


class Centre(models.Model):
    """Centre model for multi-tenant support"""
    
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        choices=[(tz, tz) for tz in pytz.common_timezones]
    )
    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Centre'
        verbose_name_plural = 'Centres'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"
    
    def get_local_time(self):
        """Get current time in centre's timezone"""
        tz = pytz.timezone(self.timezone)
        return django_timezone.now().astimezone(tz)


class Holiday(models.Model):
    """Holiday model for centre-specific holidays"""
    
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name='holidays'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes about the holiday'
    )
    date = models.DateField()
    is_recurring = models.BooleanField(
        default=False,
        help_text='If true, this holiday repeats every year'
    )
    
    class Meta:
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']
        indexes = [
            models.Index(fields=['centre', 'date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.centre.name} ({self.date})"


class TermDate(models.Model):
    """Term dates for academic terms"""
    
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name='term_dates'
    )
    term_name = models.CharField(max_length=100, help_text='e.g., Fall 2024, Spring 2025')
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        verbose_name = 'Term Date'
        verbose_name_plural = 'Term Dates'
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['centre', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.term_name} - {self.centre.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')


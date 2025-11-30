from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator


def homework_file_path(instance, filename):
    """Generate file path for homework attachments"""
    return f'homework/{instance.class_instance.centre.id}/{instance.class_instance.id}/{filename}'


def submission_file_path(instance, filename):
    """Generate file path for submission files"""
    return f'submissions/{instance.homework.class_instance.centre.id}/{instance.homework.id}/{instance.student.id}/{filename}'


class Homework(models.Model):
    """Homework assignments created by teachers"""
    
    class_instance = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='homeworks'
    )
    teacher = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='assigned_homeworks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(
        upload_to=homework_file_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'zip']
        )]
    )
    assigned_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Homework'
        verbose_name_plural = 'Homework'
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['class_instance', 'due_date']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.class_instance.name}"
    
    def is_overdue(self):
        """Check if homework is past due date"""
        return timezone.now() > self.due_date
    
    def get_submission_stats(self):
        """Get submission statistics"""
        total_students = self.class_instance.enrolments.filter(is_active=True).count()
        submissions = self.submissions.all()
        submitted = submissions.filter(status='SUBMITTED').count() + submissions.filter(status='GRADED').count()
        graded = submissions.filter(status='GRADED').count()
        
        return {
            'total_students': total_students,
            'submitted': submitted,
            'graded': graded,
            'pending': total_students - submitted
        }


class Submission(models.Model):
    """Student submissions for homework"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted'),
        ('GRADED', 'Graded'),
    ]
    
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='homework_submissions'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    file = models.FileField(
        upload_to=submission_file_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'zip']
        )]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    mark = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        unique_together = [['homework', 'student']]
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['homework', 'status']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.homework.title}"
    
    def is_late(self):
        """Check if submission was submitted late"""
        if self.submitted_at:
            return self.submitted_at > self.homework.due_date
        return False


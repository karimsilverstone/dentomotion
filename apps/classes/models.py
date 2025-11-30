from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Class(models.Model):
    """Class model for organizing students and teachers"""
    
    centre = models.ForeignKey(
        'centres.Centre',
        on_delete=models.CASCADE,
        related_name='classes'
    )
    name = models.CharField(max_length=200)
    level_or_age_group = models.CharField(
        max_length=100,
        help_text='e.g., Grade 5, Ages 10-12, Beginner'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['centre', 'name']
        indexes = [
            models.Index(fields=['centre', 'name']),
        ]
        unique_together = [['centre', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.level_or_age_group}) - {self.centre.name}"
    
    def get_teachers(self):
        """Get all teachers assigned to this class"""
        return self.teacher_assignments.all()
    
    def get_students(self):
        """Get all enrolled students"""
        return self.enrolments.filter(is_active=True)


class TeacherAssignment(models.Model):
    """Intermediate model for teacher-class many-to-many relationship"""
    
    teacher = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )
    class_instance = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Teacher Assignment'
        verbose_name_plural = 'Teacher Assignments'
        unique_together = [['teacher', 'class_instance']]
        indexes = [
            models.Index(fields=['teacher']),
            models.Index(fields=['class_instance']),
        ]
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} → {self.class_instance.name}"
    
    def clean(self):
        """Validate that the user is a teacher"""
        if self.teacher.role != 'TEACHER':
            raise ValidationError('Only users with role TEACHER can be assigned to classes.')
        
        # Check teacher doesn't exceed 3 classes (as per requirements)
        if self.teacher.teaching_assignments.count() >= 3:
            raise ValidationError('A teacher can be assigned to a maximum of 3 classes.')


class Enrolment(models.Model):
    """Student enrolment in classes"""
    
    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='enrolments'
    )
    class_instance = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrolments'
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Enrolment'
        verbose_name_plural = 'Enrolments'
        unique_together = [['student', 'class_instance']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['class_instance', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.class_instance.name}"
    
    def clean(self):
        """Validate that user is a student and in same centre as class"""
        if self.student.role != 'STUDENT':
            raise ValidationError('Only users with role STUDENT can be enrolled in classes.')
        
        if self.student.centre != self.class_instance.centre:
            raise ValidationError('Students can only enrol in classes within their own centre.')


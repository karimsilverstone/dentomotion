from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import EmailValidator


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access"""
    
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('CENTRE_MANAGER', 'Centre Manager'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    ]
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email Address'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Centre assignment for multi-tenancy (NULL for SUPER_ADMIN)
    centre = models.ForeignKey(
        'centres.Centre',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Security
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['centre']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def record_failed_login(self):
        """Record failed login attempt and lock if threshold exceeded"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save(update_fields=['failed_login_attempts'])
    
    def record_successful_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.last_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_login'])


class ActivityLog(models.Model):
    """Audit trail for sensitive user actions"""
    
    ACTION_TYPES = [
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('SENSITIVE_DATA_ACCESS', 'Sensitive Data Access'),
        ('PERMISSION_CHANGE', 'Permission Change'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action_type} at {self.timestamp}"


class ParentStudentLink(models.Model):
    """Link between parents and students"""
    
    RELATIONSHIP_CHOICES = [
        ('MOTHER', 'Mother'),
        ('FATHER', 'Father'),
        ('GUARDIAN', 'Guardian'),
        ('OTHER', 'Other'),
    ]
    
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_links',
        limit_choices_to={'role': 'PARENT'}
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parent_links',
        limit_choices_to={'role': 'STUDENT'}
    )
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Parent-Student Link'
        verbose_name_plural = 'Parent-Student Links'
        unique_together = [['parent', 'student']]
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.parent.get_full_name()} ({self.relationship}) -> {self.student.get_full_name()}"


class StudentProfile(models.Model):
    """Extended profile for students with sensitive information"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        limit_choices_to={'role': 'STUDENT'}
    )
    date_of_birth = models.DateField(null=True, blank=True)
    contacts = models.JSONField(
        default=dict,
        help_text='Contact information as JSON (phone, email, etc.)'
    )
    parent_contacts = models.JSONField(
        default=dict,
        help_text='Parent contact information as JSON'
    )
    medical_notes = models.TextField(
        blank=True,
        help_text='Medical conditions, allergies, etc.'
    )
    emergency_contact = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"


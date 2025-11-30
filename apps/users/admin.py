from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ActivityLog, ParentStudentLink, StudentProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'failed_login_attempts', 'account_locked_until')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__email', 'description')
    readonly_fields = ('user', 'action_type', 'timestamp', 'ip_address', 'user_agent', 'description')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ParentStudentLink)
class ParentStudentLinkAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'relationship', 'created_at')
    list_filter = ('relationship',)
    search_fields = ('parent__email', 'student__email', 'parent__first_name', 'student__first_name')
    raw_id_fields = ['parent', 'student']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ['user']
    fieldsets = (
        ('Student', {'fields': ('user',)}),
        ('Basic Information', {'fields': ('date_of_birth',)}),
        ('Contacts', {'fields': ('contacts', 'parent_contacts', 'emergency_contact')}),
        ('Medical', {'fields': ('medical_notes',)}),
    )


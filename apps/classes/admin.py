from django.contrib import admin
from .models import Class, TeacherAssignment, Enrolment


class TeacherAssignmentInline(admin.TabularInline):
    model = TeacherAssignment
    extra = 1
    raw_id_fields = ['teacher']


class EnrolmentInline(admin.TabularInline):
    model = Enrolment
    extra = 1
    raw_id_fields = ['student']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level_or_age_group', 'centre', 'created_at')
    list_filter = ('centre', 'level_or_age_group')
    search_fields = ('name', 'centre__name')
    inlines = [TeacherAssignmentInline, EnrolmentInline]
    date_hierarchy = 'created_at'


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'class_instance', 'assigned_at')
    list_filter = ('class_instance__centre',)
    search_fields = ('teacher__first_name', 'teacher__last_name', 'class_instance__name')
    raw_id_fields = ['teacher', 'class_instance']
    date_hierarchy = 'assigned_at'


@admin.register(Enrolment)
class EnrolmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_instance', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'class_instance__centre')
    search_fields = ('student__first_name', 'student__last_name', 'class_instance__name')
    raw_id_fields = ['student', 'class_instance']
    date_hierarchy = 'enrolled_at'


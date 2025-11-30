from django.contrib import admin
from .models import Homework, Submission


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ['student', 'submitted_at', 'status']
    fields = ['student', 'status', 'mark', 'submitted_at']


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_instance', 'teacher', 'assigned_date', 'due_date')
    list_filter = ('class_instance__centre', 'assigned_date', 'due_date')
    search_fields = ('title', 'description', 'teacher__first_name', 'teacher__last_name')
    raw_id_fields = ['class_instance', 'teacher']
    inlines = [SubmissionInline]
    date_hierarchy = 'due_date'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'homework', 'status', 'mark', 'submitted_at', 'graded_at')
    list_filter = ('status', 'homework__class_instance__centre')
    search_fields = ('student__first_name', 'student__last_name', 'homework__title')
    raw_id_fields = ['homework', 'student', 'graded_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'submitted_at'


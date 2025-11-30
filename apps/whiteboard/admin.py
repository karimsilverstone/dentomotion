from django.contrib import admin
from .models import WhiteboardSession, WhiteboardSnapshot


class WhiteboardSnapshotInline(admin.TabularInline):
    model = WhiteboardSnapshot
    extra = 0
    readonly_fields = ['saved_at', 'saved_by']


@admin.register(WhiteboardSession)
class WhiteboardSessionAdmin(admin.ModelAdmin):
    list_display = ('session_name', 'class_instance', 'teacher', 'started_at', 'ended_at', 'is_active')
    list_filter = ('is_active', 'class_instance__centre')
    search_fields = ('session_name', 'teacher__first_name', 'teacher__last_name', 'class_instance__name')
    raw_id_fields = ['class_instance', 'teacher']
    readonly_fields = ['started_at', 'ended_at']
    inlines = [WhiteboardSnapshotInline]
    date_hierarchy = 'started_at'


@admin.register(WhiteboardSnapshot)
class WhiteboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'saved_by', 'saved_at')
    list_filter = ('session__class_instance__centre',)
    search_fields = ('name', 'session__session_name')
    raw_id_fields = ['session', 'saved_by']
    readonly_fields = ['saved_at']
    date_hierarchy = 'saved_at'


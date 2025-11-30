from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'centre', 'class_instance', 'event_date', 'created_by')
    list_filter = ('event_type', 'centre', 'event_date')
    search_fields = ('title', 'description', 'centre__name', 'class_instance__name')
    raw_id_fields = ['centre', 'class_instance', 'created_by']
    date_hierarchy = 'event_date'
    readonly_fields = ['created_at', 'updated_at']


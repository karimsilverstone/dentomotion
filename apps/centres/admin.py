from django.contrib import admin
from .models import Centre, Holiday, TermDate


class HolidayInline(admin.TabularInline):
    model = Holiday
    extra = 1


class TermDateInline(admin.TabularInline):
    model = TermDate
    extra = 1


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'timezone', 'created_at')
    list_filter = ('country', 'timezone')
    search_fields = ('name', 'city', 'country')
    inlines = [HolidayInline, TermDateInline]
    date_hierarchy = 'created_at'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'centre', 'date', 'is_recurring')
    list_filter = ('is_recurring', 'centre')
    search_fields = ('name', 'centre__name')
    date_hierarchy = 'date'


@admin.register(TermDate)
class TermDateAdmin(admin.ModelAdmin):
    list_display = ('term_name', 'centre', 'start_date', 'end_date')
    list_filter = ('centre',)
    search_fields = ('term_name', 'centre__name')
    date_hierarchy = 'start_date'


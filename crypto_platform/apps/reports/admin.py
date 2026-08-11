"""Admin configuration for reports app."""
from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'title', 'period_start', 'period_end', 'generated_at', 'is_sent']
    list_filter = ['report_type', 'is_sent']
    search_fields = ['title']
    readonly_fields = ['generated_at']
    list_per_page = 25

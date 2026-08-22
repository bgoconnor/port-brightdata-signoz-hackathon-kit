from django.contrib import admin

from .models import Paper, ScrapeRun


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('arxiv_id', 'title', 'score', 'reproducible', 'scraped_at')
    list_filter = ('reproducible',)
    search_fields = ('arxiv_id', 'title', 'authors', 'subjects')


@admin.register(ScrapeRun)
class ScrapeRunAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'bright_job_id', 'status', 'bright_status',
        'records_received', 'records_written', 'failure_count', 'created_at',
    )
    list_filter = ('status', 'bright_status')
    search_fields = ('bright_job_id', 'collector_id', 'target_url')
    readonly_fields = ('created_at', 'updated_at')
